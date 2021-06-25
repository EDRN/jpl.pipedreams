# encoding: utf-8

'''Plugins ops 🤔'''

import pkgutil
import inspect
from .utils.misc_utils import ignore_unmatched_kwargs


def apply_to_all_methods(decorator):
    # ref: https://stackoverflow.com/questions/6307761/how-to-decorate-all-functions-of-a-class-without-typing-it-over-and-over-for-eac
    def decorate(cls):
        for attr in cls.__dict__: # there's probably a better way to do this
            if callable(getattr(cls, attr)) and attr != "__init__":
                setattr(cls, attr, decorator(getattr(cls, attr)))
        return cls
    return decorate


class Plugin(object):
    """Base class that each plugin must inherit from. within this class
    you must define the methods that all of your plugins must implement
    """

    @staticmethod
    def kwargs_to_args(func):
        def inner(self, kwargs):
            # print('kwargs_to_args:', func, kwargs)
            return func(self, **kwargs)
        return inner

    def __init__(self):
        self.description = 'UNKNOWN'

        # # NOTE:- IMPORTANT CODE: the below can be applied to all inheriting function statically! removed because we are not dynamically applyin decorators during runtime!

        # for attr in self.__class__.__dict__:
        #     if callable(getattr(self.__class__, attr)) and attr != "__init__":
        #         setattr(self.__class__, attr, ignore_unmatched_kwargs(getattr(self.__class__, attr)))
        #
        # # NOTE:- the following applies the 'kwargs_to_args' decorator to all the methods of this class (even the inherited ones)
        # # this happens because such a child class calls the super init function when initialized.
        # # otherwise @apply_to_all_methods(Plugin.kwargs_to_args) sugar can be used at the level at which the decorator needs to be applied directly
        # for attr in self.__class__.__dict__:
        #     if callable(getattr(self.__class__, attr)) and attr != "__init__":
        #         setattr(self.__class__, attr, Plugin.kwargs_to_args(getattr(self.__class__, attr)))

    def run(self, **kwargs):
        """The method that we expect all plugins to implement. This is the
        method that our framework will call
        """
        # raise NotImplementedError

    def apply(self, func_name, **kwargs):
        """
        Run a specific function by name from the plugin object
        """
        result = ignore_unmatched_kwargs(getattr(self, func_name))(**kwargs)
        return result

def import_module_by_name(module_name):
    plugin_module = __import__(module_name, fromlist=['blah'])
    clsmembers = inspect.getmembers(plugin_module, inspect.isclass)
    for (_, c) in clsmembers:
        # Only add classes that are a sub class of Plugin, but NOT Plugin itself
        if issubclass(c, Plugin) & (c is not Plugin) & (c.__name__ !="Template"):
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

class PluginCollection(object):

    def __init__(self):
        self.plugin_defs = {}
        self.plugin_inits={}

    def load_plugins(self, name):
        pass

    def get_plugin(self, name):
        if name in self.plugin_inits.keys():
            # print('already init plugin found:', name)
            plugin=self.plugin_inits.get(name)
        else:
            # print('getting a new plugin:', name)
            plugin=self.get_new_plugin(name)
        return plugin

    def get_new_plugin(self, name):
        # look for the plugin in already searched definitions
        plugin_def = self.plugin_defs.get(name, None)
        if plugin_def is not None:
            # print('pre plugin def found, initializing it:', name)
            plugin = plugin_def()  # initialize it
            self.plugin_inits[name] = plugin
        else:
            # search for the plugin
            # print('plugin def not found, looking:', name)
            plugins = find_plugins(name)
            if len(plugins) != 1:
                # todo: throw error
                print('More than one plugin found:', plugins)
                return None
            else:
                # print('plugin def found, adding and initializing:', name)
                plugin = plugins[0]
                self.plugin_defs[name] = plugin
                plugin = plugin()
                self.plugin_inits[name] = plugin

        return plugin

    def apply(self, template, plugin_name, func_name, kwargs):
        plugin=self.get_plugin(template+'.'+plugin_name)
        result=plugin.apply(func_name, **kwargs)
        return result

"""
refs:
https://www.guidodiepen.nl/2019/02/implementing-a-simple-plugin-framework-in-python/
https://www.datacamp.com/community/tutorials/decorators-python
https://realpython.com/primer-on-python-decorators/#decorators-with-arguments
https://stackoverflow.com/questions/6307761/how-to-decorate-all-functions-of-a-class-without-typing-it-over-and-over-for-eac
https://www.geeksforgeeks.org/creating-decorator-inside-a-class-in-python/
"""
