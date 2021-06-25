# encoding: utf-8

from jpl.pipedreams.examples.data_pipe.plugins_ops import Plugin


class Basic(Plugin):
    """This plugin convert all metadata values back to int type and add 1
    """
    def __init__(self):
        super().__init__()
        self.description = 'for basic processing pf metadata'

    def load_resources(self, **kwargs):
        pass

    def run(self, **kwargs):
        meta_dict = kwargs['meta_dict']
        for k, v in meta_dict.items():
            meta_dict[k] = int(v) + 1
        return {'meta_dict': meta_dict}

    def close_resources(self, **kwargs):
        pass
