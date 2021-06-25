# encoding: utf-8

from jpl.pipedreams.plugins_ops import Plugin


class Template(Plugin):
    def __init__(self):
        super().__init__()
        self.description = 'for publishing the metadata in a database'

    def enrich_metadata(self, *args, **kwargs):
        raise NotImplementedError

    def push(self, metadata, url, mock=False):
        raise NotImplementedError

    def delete(self, id, url):
        raise NotImplementedError

    def delete_by_query(self, key_val, url):
        raise NotImplementedError

    def gather_ids(self, url):
        raise NotImplementedError
