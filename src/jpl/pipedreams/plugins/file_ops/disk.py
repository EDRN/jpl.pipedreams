# encoding: utf-8

from jpl.pipedreams.utils.misc_utils import insensitive_glob
from .template import Template
import os


class Disk(Template):
    def __init__(self):
        super().__init__()
        self.description = 'for basic disk file ops'

    def get_bytes(self, path):
        return {'content_bytes': open(path, 'rb').read()}

    def read_str(self, path):
        return {'content_str': open(path, 'r').read()}

    def get_file_size(self, path):
        return int(os.path.getsize(path))

    def isfile(self, path):
        if path.endswith('/'):
            path=path[:-1]
        return os.path.isfile(path)

    def isdir(self, path):
        if path.endswith('/'):
            path=path[:-1]
        return os.path.isdir(path)

    def exists(self, path):
        if path.endswith('/'):
            path=path[:-1]
        return os.path.exists(path)

    def dir_walk(self, path):
        if not path.endswith('/'):
            path=path+'/'
        for root, subdirs, files in os.walk(path):
            subdirs=[os.path.join(path, subdir) for subdir in subdirs]
            files=[os.path.join(path, file) for file in files]
            return subdirs, files
        return [], []

    def recurse(self, path):
        subdirs, files = self.dir_walk(path)
        resource_children = subdirs + files
        for resource in resource_children:
            yield from self.recurse(resource)

        yield path, resource_children

    def download(self, source_path, target_path):
        # TODO: implement a copy operation on disk
        pass

    def search_file(self, path, pattern):
        return [name for name in insensitive_glob(os.path.join(path, pattern))]

    def file_size(self, path):
        return int(os.path.getsize(os.path.join(path)))

    def makedirs(self, path):
        os.makedirs(path, exist_ok=True)
