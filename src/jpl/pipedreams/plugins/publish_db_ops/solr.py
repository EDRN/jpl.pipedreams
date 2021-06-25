# encoding: utf-8

import json
import requests
from jpl.pipedreams.utils.misc_utils import MyException

# TODO: before 'core' param was being passed separately, now it should be part of the url

from .template import Template


# 🤔 This doesn't seem to be used in this module
# def comaelcase(str):
#     return str[0].upper() + ''.join(str[1:]).lower()


class Solr(Template):
    def __init__(self):
        super().__init__()
        self.description = 'for publishing the metadata into solr'

    def push(self, metadata, url, mock=False):
        status=''
        if mock:
            status='successfully mock-pushed to solr'
        else:
            headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
            response=requests.post(url, data=bytes(json.dumps(metadata), 'utf-8'), headers=headers)

            if response.status_code==400:
                raise MyException("Error while publishing to Solr: "+response.text)
            else:
                print('got this response from solr: ', response.text)
                status=response.text
        return {'solr_status': status}

    def delete(self, id, url):
        url = url+'/update?commit=true'
        metadata={'delete':{'id':id}}
        print('deleting: ', url, json.dumps(metadata, indent=4), '\n')
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        response = requests.post(url, data=bytes(json.dumps(metadata), 'utf-8'), headers=headers)
        if response.status_code == 400:
            raise MyException("Error while publishing to Solr: " + response.text)
        else:
            print('got this response from solr: ', response.text)
        return response.text

    def delete_by_query(self, key_val, url):
        url = url  + '/update?commit=true'
        metadata = {'delete': {'query': key_val[0]+':'+key_val[1]}}
        print('deleting: ', url, json.dumps(metadata, indent=4), '\n')
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        response = requests.post(url, data=bytes(json.dumps(metadata), 'utf-8'), headers=headers)
        if response.status_code == 400:
            raise MyException("Error while publishing to Solr: " + response.text)
        else:
            print('got this response from solr: ', response.text)
        return response.text

    def gather_ids(self, url):
        url = url+'/select'
        metadata={"params": {"q":'id:*', "rows": 10000, "wt": "json", "fl":"id"}}
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        print('trying to locate:', url, json.dumps(metadata))
        response = requests.post(url, data=bytes(json.dumps(metadata), 'utf-8'), headers=headers)
        if response.status_code == 400:
            raise MyException("Error while publishing to Solr: " + response.text)
        else:
            print('got this response from solr: ', response.json())
        docs=response.json().get('response').get('docs')
        docs=[doc['id'] for doc in docs]
        return docs