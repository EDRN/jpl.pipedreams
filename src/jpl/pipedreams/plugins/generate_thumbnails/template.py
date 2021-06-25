# encoding: utf-8

from jpl.pipedreams.plugins_ops import Plugin


class Template(Plugin):
    def __init__(self):
        super().__init__()
        self.description = 'for thumbnail generation'

    def generate_thumbnail(self, image_filepath, thumbnail_filepath):
        raise NotImplementedError
