# encoding: utf-8

'''Template for testing'''

from jpl.pipedreams.plugins_ops import Plugin


class Template(Plugin):
    def __init__(self):
        super().__init__()
        self.description = 'for testing'

    def test(self, *args, **kwargs):
        raise NotImplementedError
