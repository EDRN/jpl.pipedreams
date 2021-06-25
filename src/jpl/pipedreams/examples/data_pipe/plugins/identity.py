# encoding: utf-8

from jpl.pipedreams.examples.data_pipe.plugins_ops import Plugin


class Identity(Plugin):
    """This plugin is just the identity function: it returns the argument
    """
    def __init__(self):
        super().__init__()
        self.description = 'Identity function'

    def load_resources(self):
        self.resources = 2

    def run(self, argument):
        """The actual implementation of the identity plugin is to just return the
        argument
        """
        return argument + self.resources

    def close_resources(self):
        pass
