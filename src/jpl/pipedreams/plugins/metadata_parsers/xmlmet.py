from .template import Template
from lxml import etree

class Xmlmet(Template):
    def __init__(self):
        super().__init__()
        self.description = 'read metadata from xml files'

    def parse_metadata(self, content_str):
        metadata = {}
        parser = etree.XMLParser(recover=True)  # todo: should this be initialized once ??
        mydoc = etree.fromstring(content_str, parser=parser)
        items = mydoc.findall('keyval')
        for item in items:
            key = ''
            val = ''
            try:
                key = item.findall('key')[0].text
                val = item.findall('val')[0].text
            except:
                if key == '':
                    continue
            metadata[key.replace('_File_', '')] = val
        return {"metadata": metadata}

