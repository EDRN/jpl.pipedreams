import os

def add_suffix_to_dict_values(meta_input, suffix):
    return {k: str(v[0])+'_'+suffix for k,v in meta_input.items()}

def retrieve_additional_metadata(metadata, op_resources):
    for parent_task_ID, op_resource in op_resources.items():
        additional_metadata=op_resource['additional_metadata']
        additional_metadata = additional_metadata.to_dict('records')[0]
        for k, v in additional_metadata.items():
            metadata[k]=v
    return metadata
