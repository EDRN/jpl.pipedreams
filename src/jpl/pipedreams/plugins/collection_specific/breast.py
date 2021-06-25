
import os
from pathlib import Path
from  file_ops import cfg_to_dict
import re
import pandas as pd
from  file_ops import exists, get_bytes

def get_sub_dataset_name(thisDir):

    if thisDir.lower() == 'primary':
        subDatasetName = 'Primary Images'
    elif thisDir.lower() == 'mammograms':
        subDatasetName = 'Mammograms'
    elif thisDir.lower() == 'truth':
        subDatasetName = 'Truth files'
    elif thisDir.lower() == '2d':
        subDatasetName = 'Full-Field Digital Mammography (FFDM) images (2D)'
    elif thisDir.lower() == 'ffdm':
        subDatasetName = 'Full-Field Digital Mammography (FFDM) images (2D)'
    elif thisDir.lower() == 'volume':
        subDatasetName = 'Digital Breast Tomosynthesis  (DBT) images (3D)'
    elif thisDir.lower() == 'proc':
        subDatasetName = 'Processed (for display)'
    elif thisDir.lower() == 'raw':
        subDatasetName = 'Raw (for processing)'
    elif thisDir.lower() == 'cview':
        subDatasetName = 'C-View'
    elif thisDir.lower() == 'mask':
        subDatasetName = 'Mask'
    else:
        subDatasetName = thisDir

    return subDatasetName

def enrich_metadata(publish_type, metadata, **kwargs):

    if publish_type!='datasets':
        return metadata

    templates=kwargs['templates']
    s3_bucket=kwargs['s3_bucket']
    archive_dir=kwargs['archive_dir']
    s3_client=kwargs['s3_client']
    additional_met_excel=kwargs.get('additional_met_excel', None)

    if type(metadata["DatasetName"])==list:
        DatasetName=metadata["DatasetName"][0]
        DatasetId=metadata['DatasetId'][0]
    else:
        DatasetName=metadata["DatasetName"]
        DatasetId=metadata['DatasetId']


    if len(Path(DatasetId).parts)==2: # for first level datasets


        # add other additional metadata from excel files!
        if additional_met_excel is not None:
            print('Looking for additional metadata file:', additional_met_excel)
            if not exists(additional_met_excel, '', archive_dir):
                print('The additional metadata file could not be found!')
            else:
                metadata_df = pd.read_excel(get_bytes(additional_met_excel, '', archive_dir), sheet_name='BRS-I data')
                # edit the 'ParticipantID' values to match them to the dataset names in labcas
                metadata_df['ParticipantID'] = metadata_df['ParticipantID'].apply(lambda x: str(x) if 'E' in str(x) else "AB"+str(x))
                # remove the 'Site' for further anonymity of patients
                metadata_df.drop(columns=['Site'], inplace=True)
                # look for the 'ParticipantID' matching the current DatasetName
                matches=metadata_df[metadata_df['ParticipantID']==DatasetName].to_dict('records')
                if len(matches)!=0:
                    # assuming there will be a single match only!
                    additional_metadata=matches[0]
                    print('Participant found with additional metadata! Adding!:', DatasetName)
                    for k, v in additional_metadata.items():
                        metadata[k] = v


        for template in templates:
            regex=template['regex']
            template_fpath=template['template_fpath']
            p = re.compile(regex)
            if p.match(DatasetName)!=None:

                # read in template metadata file
                metadata_,_=cfg_to_dict(template_fpath, s3_bucket, archive_dir, s3_client)
                for k, v in metadata_.items():
                    metadata[k]=v

                # create a description

                metadata["DatasetDescription"]= DatasetName+ " mammography images"
                metadata["DatasetName"] = DatasetName # replace the placeholder

    else:
        metadata["DatasetName"] = get_sub_dataset_name(DatasetName)

    return metadata

