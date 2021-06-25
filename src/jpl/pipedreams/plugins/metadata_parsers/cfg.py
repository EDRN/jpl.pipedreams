# encoding: utf-8

from .template import Template
import configparser
from jpl.pipedreams.utils.misc_utils import MyException


class Cfg(Template):
    def __init__(self):
        super().__init__()
        self.description = 'read metadata from .cfg files'

    def parse_metadata(self, content_str):
        metadata = {}
        config = configparser.RawConfigParser()
        config.optionxform = str
        config.read_string(content_str)
        header = config.sections()
        if len(header) == 0 or header[0] not in ['Collection', 'Dataset', "File"]:
            raise MyException(
                'Improper formatting of the metadata file! Provide the correct header/section; Collection, Dataset or File!')
        else:
            header = header[0]
        for key in config[header]:
            value = config[header][key].strip()
            key = key.strip()
            value = [item.strip() for item in value.split('|') if item.strip() != '']
            metadata[key] = value
        return {"metadata": metadata, "header": header}
