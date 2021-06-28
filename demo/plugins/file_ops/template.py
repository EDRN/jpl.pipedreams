# encoding: utf-8

from jpl.pipedreams.plugins_ops import Plugin


class Template(Plugin):
    def __init__(self):
        super().__init__()
        self.description = 'for basic file ops'

    def get_bytes(self, *args, **kwargs):
        raise NotImplementedError

    def read_str(self, *args, **kwargs):
        raise NotImplementedError

    def get_file_size(self, *args, **kwargs):
        raise NotImplementedError

    def isfile(self, *args, **kwargs):
        raise NotImplementedError

    def isdir(self, *args, **kwargs):
        raise NotImplementedError

    def exists(self, *args, **kwargs):
        raise NotImplementedError

    def dir_walk(self, *args, **kwargs):
        raise NotImplementedError

    def download(self, *args, **kwargs):
        raise NotImplementedError

    def search_file(self, *args, **kwargs):
        raise NotImplementedError
