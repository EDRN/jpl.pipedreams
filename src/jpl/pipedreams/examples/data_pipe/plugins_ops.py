"""
-Define a base class for the plugins
-Implement a method to look for plugins that inherit this base class
-Every publishing task will load all plugins, using walk_package, which will also call 'load_resources' function. Then
    'perform_operation' will be called as many times as needed on different dirs and files. Then maybe we will run 'close_resources' on the
    plugin-objects.
ref: https://www.guidodiepen.nl/2019/02/implementing-a-simple-plugin-framework-in-python/
"""

import pkgutil
import inspect

class Plugin(object):
    """Base class that each plugin must inherit from. within this class
    you must define the methods that all of your plugins must implement
    """

    def __init__(self):
        self.description = 'UNKNOWN'

    def run(self, **kwargs):
        """The method that we expect all plugins to implement. This is the
        method that our framework will call
        """
        raise NotImplementedError

    def load_resources(self, **kwargs):
        """
        Load any resources necessary for a
        """
        raise NotImplementedError

    def close_resources(self, **kwargs):
        """
        Safely close any resources opened in the load_resources function
        """
        raise NotImplementedError

def import_module_by_name(module_name):
    plugin_module = __import__(module_name, fromlist=['blah'])
    clsmembers = inspect.getmembers(plugin_module, inspect.isclass)
    for (_, c) in clsmembers:
        # Only add classes that are a sub class of Plugin, but NOT Plugin itself
        if issubclass(c, Plugin) & (c is not Plugin):
            # print(f'    Found plugin class: {c.__module__}.{c.__name__}')
            yield c

def find_plugins(package):
    """walk the supplied package to retrieve all plugins (find and initialized objects of a plugin type class)
    """
    imported_package = __import__(package, fromlist=["blah"]) # todo: what is the usage of 'fromlist'!
    plugins=[]
    if hasattr(imported_package, "__path__"):
        for _, pluginname, ispkg in pkgutil.iter_modules(imported_package.__path__, imported_package.__name__ + '.'):
            if not ispkg:
                plugins.extend(list(import_module_by_name(pluginname)))
    else:
        module_name=imported_package.__name__
        plugins.extend(list(import_module_by_name(module_name)))

    return plugins

class PluginCollection_orig(object):
    """Upon creation, this class will read the plugins package for modules
    that contain a class definition that is inheriting from the Plugin class
    """

    def __init__(self, plugin_package):
        """Constructor that initiates the reading of all available plugins
        when an instance of the PluginCollection object is created
        """
        self.plugin_package = plugin_package
        self.plugins=find_plugins(self.plugin_package)

    def apply_plugins_on_value(self, argument, plugin_names):
        """Apply all of the requested plugins on the argument supplied to this function
        """
        print(f'Applying plugins: {plugin_names} on value {argument}:')
        for plugin in self.plugins:
            if plugin.__class__.__name__ in plugin_names:
                print(f'    Applying {plugin.description} on value {argument} yields value {plugin.run(argument)}')


class PluginCollection(object):

    def __init__(self):
        self.plugin_defs = {}
        self.plugin_inits={}

    def get_plugin(self, name):
        plugin=self.plugin_inits.get(name, self.get_new_plugin(name))
        return plugin

    def get_new_plugin(self, name):
        # look for the plugin in already searched definitions
        plugin_def = self.plugin_defs.get(name, None)
        if plugin_def is not None:
            plugin = plugin_def()  # initialize it
            self.plugin_inits[name] = plugin
        else:
            # search for the plugin
            plugins = find_plugins(name)
            if len(plugins) != 1:
                # todo: throw error
                print('More than one plugin found!')
                return None
            else:
                plugin = plugins[0]
                self.plugin_defs[name] = plugin
                self.plugin_inits[name] = plugin()
                plugin = plugin()

        return plugin