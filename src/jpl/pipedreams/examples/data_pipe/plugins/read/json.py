# encoding: utf-8

from jpl.pipedreams.examples.data_pipe.plugins_ops import Plugin
import os
import json


class Json(Plugin):
    """This plugin reads a metadata from a json file
    """
    def __init__(self):
        super().__init__()
        self.description = 'for reading json file'

    def load_resources(self, **kwargs):
        self.base_dir = kwargs['base_dir']

    def run(self, **kwargs):
        file_path = kwargs['file_path']
        return {'meta_dict': json.loads(open(os.path.join(self.base_dir, file_path)).read())}

    def close_resources(self):
        pass
