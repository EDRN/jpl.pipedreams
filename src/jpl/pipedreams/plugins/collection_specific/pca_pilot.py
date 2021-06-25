
# TODO: ALERT: these mappings need to be manually updated!
# https://mcl.nci.nih.gov/studies
study_id_mappings={
    '12':'MCL Supplement: A Pre-Cancer Atlas (PCA) for Breast, Lung, Pancreas, and Prostate Pilot Project'
}
# https://mcl.nci.nih.gov/resources/informatics_tools/mcl-site-and-investigator-ids
site_id_mappings={
    '78':'University of Vermont',
    '76':'University of California, San Diego'
}

import re
import pandas as pd
from  file_ops import exists, get_bytes
from api import archive_dir
import os

def camel_case_split(str):
    return ' '.join(re.findall(r'[A-Z](?:[a-z]+|[A-Z]*(?=[A-Z]|$))', str))

def enrich_metadata(publish_type, metadata, **kwargs):



    if publish_type!='files' or '_meta' in os.path.basename(metadata['FileId']).lower():
        return metadata



    # check if there is a metadata file available and gather metadata from the metadata file
    metadata_from_meta_file={}
    print(metadata['FileId'], metadata['FileName'])
    rel_file_loc=metadata['FileId']
    file_name=metadata['FileName']
    metadata_rel_file_loc=os.path.join(os.path.dirname(rel_file_loc), os.path.basename(rel_file_loc).replace('_Data','_Meta').replace('_DATA', '_META'))

    if '_meta' in os.path.basename(metadata_rel_file_loc).lower() and  '.xlsx' in os.path.basename(metadata_rel_file_loc).lower() and exists(metadata_rel_file_loc, '', archive_dir):
        print('reading meta file for pca:', metadata_rel_file_loc)
        metadata_filename_df=pd.read_excel(get_bytes(metadata_rel_file_loc, '', archive_dir), sheet_name='CoreFileUploadTemplate')
        metadata_from_meta_file=metadata_filename_df[metadata_filename_df['FileName'].str.lower()==file_name.lower().replace('.xlsx','')]
        print('metadata_from_meta_file', metadata_from_meta_file)
        if len(metadata_from_meta_file)!=0:
            metadata_from_meta_file=metadata_from_meta_file.to_dict('records')[0]
        # change the Timestamp formats to date strings
        for k,v in metadata_from_meta_file.items():
            if str(type(v))=="<class 'pandas._libs.tslibs.timestamps.Timestamp'>": # pd.tslib.Timestamp:
                metadata_from_meta_file[k]=v.to_pydatetime().strftime("%m/%d/%Y")
        print('metadata_from_meta_file', metadata_from_meta_file)


    # add the metadata from the metadata file (only add new metadata, do not replace what is already there)
    for key, val in metadata_from_meta_file.items():
        if key not in metadata.keys():
            metadata[key] = val


    # gather metadata from the filename
    metadata_from_file_name={}

    parts=metadata['FileName'].replace('.xlsx','').split('_')
    if len(parts)!=6:
        return metadata

    StudyID, SiteID, FileContent, DateFileGenerated, Version, DataUploadType=parts
    FileContent=camel_case_split(FileContent)
    Description=', '.join([FileContent+' Data', site_id_mappings.get(SiteID,''), 'Submitted '+DateFileGenerated])
    metadata_from_file_name['Description']=Description
    metadata_from_file_name['StudyID']=StudyID
    metadata_from_file_name['SiteID']=SiteID
    metadata_from_file_name['Site']=site_id_mappings[SiteID]
    # this metadata is already being populated under the name 'ProtocolName' at the collection level!
    # metadata_from_file_name['Study'] = study_id_mappings[StudyID]
    metadata_from_file_name['FileContent']=FileContent
    metadata_from_file_name['DateFileGenerated']=DateFileGenerated
    metadata_from_file_name['Version'] = Version
    print('metadata_from_file_name', metadata_from_file_name)


    # add the metadata from the file name (only add new metadata, do not replace what is already there)
    for key,val in metadata_from_file_name.items():
        if key not in metadata.keys():
            metadata[key]=val

    # todo: publish the data file



    return metadata

"""
Adding Description field based on metadata in the filename

+++++++ Parsing metadata from filename

Here’s the link to the MCL portal that has all of this documentation (for your reference) – https://mcl.nci.nih.gov/resources/informatics_tools/data-upload
  
Below is the file naming conventions that a site should follow when the upload
 
<Study ID>_<Site ID>_<File Type>_<File Submission Date>_<Version>_<Date Upload Type>
Examples:

12_82_ClinicalCore_20200212_0_DATA.xlsx

12_111_Biospecimen_20200213_1_META.xlsx

12_109_SOP_FFPELabelShip_20200427_1_DATA.pdf


File naming elements:

Study ID = identifier provided by CDMG to uniquely identify the MCL study. List of study IDs may be found on the MCL portal.
SiteID = identifier provided by CDMG to uniquely identify an MCL research team. List of Site IDs may be found on the MCL portal.
File Type = type of data captured in the submitting file, e.g. ClinicalCore, Biospecimen, SOP_SOP name, Document 
File Submission Date = date the file is submitted to LabCAS for capture in the archive, formatted as YYYYMMDD.
Version = the version of the file submitted, with 0 being the first submission. Files submitted more than once should increment version.
Data Upload Type =“DATA” for the data file or “META” for the metadata file. 
Study ID – https://mcl.nci.nih.gov/studies
Site ID - https://mcl.nci.nih.gov/resources/informatics_tools/mcl-site-and-investigator-ids
 
Metadata templates will differ based on the types of files that are uploaded:
labcascorefileuploaddictionary_v0-0-1 (2) is the clinical and biospecimen data files. This should be used to include the metadata for these files.
mcl_genomics_smart3seqext_template_v0-0-1 (1)  is for the smart-3seq files.

++++++++++++++++++ Adding Description field: 

Collection ID= PCA_Pilot_Data/PCA_Pilot_Clinical_Data
File Metadata:
FileName= 12_78_ClinicalCore_20200409_0_Data
Description=Clinical Core Data, University of Vermont, Submitted 20200409
 
FileName= 12_78_UVM_Biospecimen_DataUpload_May-14-20_ID1334
Description=Biospecimen Core Data, University of Vermont, Submitted 20200520

"""