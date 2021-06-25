import os

# create/add a task to gather any the additional_metadata from upstream resources that apply to the the current resource
def retrieve_additional_metadata(metadata, resource, op_resources):
    # check if the op resource came from a resource that is a parent directory of the current resource
    # get the 'additional_metadata' if any, from the op_resource and add to the main metadata
    for parent_task_ID, op_resource in op_resources.items():
        parent_resource=parent_task_ID.split('|+|')[1]
        # if the current resource is the child of the inherited resource
        if os.path.commonpath([parent_resource]) == os.path.commonpath([parent_resource, resource]):
            if 'additional_metadata' in op_resource.keys():
                # have some matching criteria
                additional_metadata=op_resource['additional_metadata']
                file_ID_column='LABCAS_ID' if 'LABCAS_ID' in additional_metadata.columns else "FileName"
                if file_ID_column in additional_metadata.columns:
                    additional_metadata=additional_metadata[additional_metadata[file_ID_column]==os.path.basename(resource)]
                    if len(additional_metadata)!=0:
                        additional_metadata=additional_metadata.to_dict('records')[0]
                        for k,v in additional_metadata.items():
                            metadata[k]=v
    return metadata

def temp_func(x):
    return x+2