import os, pkg_resources
import pandas as pd

# TODO: create config loader functions. Load -> Save in Cache
solr_port = 8983
api_port=5000
solr_url = 'http://localhost:'+str(solr_port)+'/solr/'
archive_dir = os.path.join(os.environ.get('LABCAS_INSTALL', './'),'archive')
thumbnails_dir = os.path.join(os.environ.get('LABCAS_INSTALL', './'),'thumbnails')
s3_bucket=None
s3_profile_name='saml'
mock=False

# 🤔 ``repo_resource_path`` doesn't seem to be used anywhere, and using ``__file__`` is
# bad form, so just setting it to None for now.
# OLD:
#    repo_resource_path = os.path.join(pathlib.Path(__file__).parent, 'archive')
# NOW:
repo_resource_path = None

# load some basic configs
metadata_model_path = pkg_resources.resource_filename(__name__, 'LabCASCoreMetadataModel_V0.0.xlsx')
config_path = pkg_resources.resource_filename(__name__, 'config.txt')
inheritance_config = pkg_resources.resource_filename(__name__, 'inheritance_config.txt')


# ====== load mine-type mappings
mime_type_mappings={}
mime_df=pd.read_excel(metadata_model_path, sheet_name="MIME Type PV List", header=0)
for _, row in mime_df.iterrows():
    extention=row['MIME type'].split('=')[0]
    Met_vaue=row['Metadata value']
    mime_type_mappings[extention]=Met_vaue

# ====== load inheritence inclusion/exclusion lists (todo: only exclusions lists for now, include functionality for both later)
up_exclude=set()
down_exclude=set()
lines=open(inheritance_config,'r').readlines()
for line in lines:
    line=line.strip()
    if line=='':
        continue
    line=line.split('||')
    if line[0]=='<up>' and line[1]=='<exclude>':
        up_exclude.update([item.strip() for item in line[2].split(',')])
    if line[0]=='<down>' and line[1]=='<exclude>':
        down_exclude.update([item.strip() for item in line[2].split(',')])

# ====== load basic config

class Config(object):
    def __init__(self, config_path):
        values_lookup = {}
        field_lookup = {}
        special_change_requests = {}

        # read the rules from the config file
        for line in open(config_path, 'r').readlines():
            line = line.strip()
            if line == '':
                continue
            line = line.split('||')

            if len(line) == 2:
                if line[1][0] == '<' and line[1][-1] == '>':
                    if line[0] not in special_change_requests.keys():
                        special_change_requests[line[0]] = []
                    special_change_requests[line[0]].append(''.join(line[1][1:-1]).lower())
                else:
                    field_lookup[line[0]] = line[1]
            if len(line) == 3:
                field = line[0]
                value = line[1]
                aliases = [item.strip() for item in line[2].split(',')]
                if field not in values_lookup.keys():
                    values_lookup[field] = {}
                for alias in aliases:
                    values_lookup[field][alias] = value

        self.values_lookup = values_lookup
        self.field_lookup = field_lookup
        self.special_change_requests = special_change_requests

basic_config_obj=Config(config_path)