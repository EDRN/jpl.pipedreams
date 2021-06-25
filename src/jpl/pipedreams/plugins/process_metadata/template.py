# encoding: utf-8

from jpl.pipedreams.plugins_ops import Plugin


class Template(Plugin):
    def __init__(self):
        super().__init__()
        self.description = 'for processing metadata'

    def enrich_metadata(self, *args, **kwargs):
        raise NotImplementedError
