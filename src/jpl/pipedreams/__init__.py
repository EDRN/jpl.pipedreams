# encoding: utf-8

'''Pipe Dreams'''

import importlib.resources


PACKAGE_NAME = __name__

try:
    __version__ = VERSION = importlib.resources.files(__name__).joinpath('VERSION.txt').read_text().strip()
except AttributeError:
    __version__ = VERSION = importlib.resources.read_text(__name__, 'VERSION.txt')
