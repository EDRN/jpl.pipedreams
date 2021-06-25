"""
Main application that demonstrates the functionality of
the dynamic plugins and the PluginCollection class
"""

from jpl.pipedreams.examples.data_pipe.plugins_ops import PluginCollection_orig


def main():
    """main function that runs the application
    """
    my_plugins = PluginCollection_orig('plugins')
    my_plugins.apply_plugins_on_value(5, ['Identity'])


if __name__ == '__main__':
    main()