from .template import Template

def comaelcase(str):
    return str[0].upper() + ''.join(str[1:]).lower()

class Basic(Template):
    def __init__(self):
        super().__init__()
        self.description = 'basic metadata enrichment based on the configs'

    def enrich_metadata(self, metadata, config_obj):

        values_lookup=config_obj.values_lookup
        field_lookup=config_obj.field_lookup
        special_change_requests=config_obj.special_change_requests

        # apply the rules to metadata
        metadata_={}
        for k, v in metadata.items():

            k = field_lookup.get(k, k) # replace the field to the new value

            if k in values_lookup.keys():
                if type(v)==list:
                    v=[values_lookup[k].get(_v, _v) for _v in v]
                if type(v)==str:
                    v=values_lookup[k].get(v, v)

            # apply special changes:
            if k in special_change_requests.keys():
                for request in special_change_requests[k]:
                    if request =='camelcase':
                        if type(v) == list:
                            v = [comaelcase(_v) for _v in v]
                        if type(v) == str:
                            v = comaelcase(v)
            metadata_[k]=v
        return {"metadata": metadata_}