import pandas as pd
# FIXME: I can't find an ``api`` module; there is a ``repo_resource_path`` but it's in a module
# called ``...configs.basic`` 🤷‍♀️ Maybe this module isn't used? 🤔
from api import repo_resource_path
import os


def enrich_metadata(publish_type, metadata, **kwargs):

    if publish_type!='files':
        return metadata

    lookup_path = kwargs['path']
    relative=kwargs.get('relative', 'False')
    if relative=='True':
        lookup_path= os.path.join(repo_resource_path, lookup_path)
    lookup=pd.read_csv(lookup_path)
    file_name=metadata.get('FileName', None)
    if file_name==None:
        return metadata
    row=lookup[lookup['image_name']==file_name]
    if len(row)==0:
        return metadata
    fileurl='https://cloud.proscia.com/repos/2615?slide='+str(int(row['Slide_Field_Sample_ID'].values[0]))
    metadata['FileUrl']=fileurl
    metadata['Tools'] = ['Proscia']
    return metadata