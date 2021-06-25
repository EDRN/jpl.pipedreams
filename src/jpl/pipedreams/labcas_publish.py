# encoding: utf-8

import os

from .data_pipe import Operation
from .configs.basic import mime_type_mappings, up_exclude, down_exclude, solr_url, basic_config_obj
from .plugins.general.general_functions import retrieve_additional_metadata
from .configs.mappings import file_ext_to_thumbnail_plugin

# =========== create a basic LabCAS style metadata ingestion pipeline using data pipes ===============
# ====================================================================================================

basic_labcas_publishing=Operation('basic_labcas_publishing')
all_plugin_applier = basic_labcas_publishing.plugin_collection

# 🤨 These values for ``data_dir``, ``config_dir``, and ``thumbnails_dir`` seem wrong:
data_dir='/Users/asitangmishra/PycharmProjects/labcas_publish_api/publish_pipeline/test/test_data/archive/'
config_dir='/Users/asitangmishra/PycharmProjects/labcas_publish_api/publish_pipeline/configs'
thumbnails_dir='/Users/asitangmishra/PycharmProjects/labcas_publish_api/publish_pipeline/test/test_data/thumbnails/'
recreate_thumbnail=True
additional_metadata_file_paths=['collection1/additional_lookup_file.xlsx']


# ===== define the pipes

def get_parse_pipe(metadata_file_type, reader_func_name, suffix=''):
    return [
            # read the metadata file from disk
            (metadata_file_type+"_to_str"+suffix, "jpl.pipedreams.plugins.file_ops.disk."+reader_func_name, None),
            # parse the string into a dictionary
            ("parse_"+metadata_file_type+"_str"+suffix, "jpl.pipedreams.plugins.metadata_parsers."+metadata_file_type + ".parse_metadata", None),
        ]


def get_pipe_by_name(pipe, pipe_section):
    lookup= {unit[0]:unit for unit in pipe}
    return [lookup[unit] for unit in pipe_section]


merge_parsed_metadata_pipe=[
    ("merge_parsed_metadata", 'merge', {"in_multi": "metadata"})
    ]


base_pipe= [
        # add basic path metadata
        ("add_basic_meta", 'merge', {"in_multi": ["basic_metadata", "metadata"], "out": "metadata"}),
        # apply basic metadata processing
        ("process_meta_basic", "jpl.pipedreams.plugins.process_metadata.basic.enrich_metadata", None),

        # add a test wait
        ("test_wait", "artificial_wait", {'wait_time': 0}), # this is just to test the parallelization capability

        # for receiving metadata from up
        ("up_receive", 'merge', {"in_multi": ["down_send_metadata", "metadata"], "out": "metadata"}),

        # look for any additional metadata in op_resources
        ("add_additional_meta", retrieve_additional_metadata, {"op_out": ["metadata"]}),

        # add basic down send metadata
        ("add_basic_down_send", 'merge', {"in_multi": ["metadata", "basic_down_metadata"], "out": "down_send_metadata"}),
        # for sending the metadata to down
        ("down_send", 'remove_keys', {"keys_to_remove": down_exclude, "result_levels": ['down_send_metadata']}),
        # change name of the result
        ("result_name_change_1", 'change_name', {'in_to_out': {'down_send_metadata': 'metadata'}}),

        # for receiving metadata from down
        ("down_receive", 'merge', {"in_multi": "up_send_metadata", "merge_type": "collect"}),
        # merge with the main metadata stream
        ("further_merge", 'merge', {"in_multi": ["up_send_metadata", "metadata"], "out": "up_send_metadata"}),

        # for sending metadata to up
        ("up_send", 'remove_keys', {"keys_to_remove": up_exclude, "result_levels": ['up_send_metadata']}),
        # change name of the result
        ("result_name_change_2", 'change_name', {'in_to_out': {"up_send_metadata": "metadata"}}),

        # push to solr
        ("publish_to_solr", "jpl.pipedreams.plugins.publish_db_ops.solr.push", None)
    ]


# ====== recurse through a directory structure and build the task graph
collection_resource='collection1'
collection_path=os.path.join(data_dir, collection_resource)
for resource_path, resource_children_path in all_plugin_applier.apply('jpl.pipedreams.plugins.file_ops', 'disk', 'recurse', {"path": collection_path}):
    resource=os.path.relpath(resource_path, data_dir)
    resource_name=os.path.basename(resource)
    print('\nResource:', resource)
    basic_metadata={}
    isCollection = True if resource==collection_path else False
    basic_metadata['Id']=resource
    basic_metadata['Name'] = resource_name
    isdir=all_plugin_applier.apply('jpl.pipedreams.plugins.file_ops', 'disk', 'isdir', {"path": resource_path})
    if isdir:
        if resource_name.lower()=='_old_':
            print('not publishing this directory as it contains stale/incorrect files!')
            continue
        cfg_metadata_path=os.path.join(resource_path, resource_name + '.cfg')
        xml_metadata_path=os.path.join(resource_path, resource_name + '.xmlmet')
        if isCollection:
            basic_metadata['CollectionId']=resource
            basic_metadata['CollectionName']=resource_name
        else:
            basic_metadata['DatasetId'] = resource
            basic_metadata['DatasetName'] = resource_name
            basic_metadata['DatasetVersion'] = 1
    else:
        if '.met' in resource_name or '.xmlmet' in resource_name or '.cfg' in resource_name or '.listing' == resource_name:
            print('not publishing this file as it is a metadata file!')
            continue
        cfg_metadata_path=resource_path +'.cfg'
        xml_metadata_path = resource_path + '.xmlmet'
        basic_metadata['FileId'] = resource
        basic_metadata['FileName'] = resource_name
        basic_metadata['FileSize'] = all_plugin_applier.apply('jpl.pipedreams.plugins.file_ops', 'disk', 'file_size', {"path": resource_path})
        basic_metadata["FileDownloadId"]= "abc" # todo: this is just a place holder: should remove it?
        basic_metadata['DatasetVersion'] = 1
        file_extention = resource_name.split('.')[-1]
        basic_metadata['FileType'] = mime_type_mappings.get(file_extention, 'unknown')
        basic_metadata['FileVersion']=1

    # === look for metadata files and add the parsing tasks

    if all_plugin_applier.apply('jpl.pipedreams.plugins.file_ops', 'disk', 'exists', {"path": cfg_metadata_path}):
        metadata_pipe=get_parse_pipe("cfg", "read_str")
        metadata_pipe.extend(merge_parsed_metadata_pipe)
        runtime_params_dict={}
        runtime_params_dict[metadata_pipe[0][0]]={"path": os.path.join(data_dir, cfg_metadata_path)}
        basic_labcas_publishing.add_pipes(resource, metadata_pipe, runtime_params_dict=runtime_params_dict)

    if all_plugin_applier.apply('jpl.pipedreams.plugins.file_ops', 'disk', 'exists', {"path": xml_metadata_path}):
        metadata_pipe=get_parse_pipe("xmlmet", "read_str")
        metadata_pipe.extend(merge_parsed_metadata_pipe)
        runtime_params_dict={}
        runtime_params_dict[metadata_pipe[0][0]]={"path": os.path.join(data_dir, xml_metadata_path)}
        basic_labcas_publishing.add_pipes(resource, metadata_pipe, runtime_params_dict=runtime_params_dict)

    # if an excel or csv file are present in this path for additional metadata add them as a resource for the current and any downstream tasks
    _meta_files=[]
    if isdir:
        # find any _META files here
        _meta_files=all_plugin_applier.apply('jpl.pipedreams.plugins.file_ops', 'disk', 'search_file', {"path": resource_path, 'pattern': '*_meta*'})
        # check if a metadata file has been explicitly provided for this path
        for additional_metadata_file_path in additional_metadata_file_paths:
            if os.path.commonpath([os.path.abspath(resource)]) == os.path.commonpath([os.path.abspath(resource), os.path.abspath(additional_metadata_file_path)]):
                _meta_files.append(os.path.join(data_dir, additional_metadata_file_path))

    for i, additional_metadata_file_path in enumerate(_meta_files):
        ext=additional_metadata_file_path.split('.')[-1]
        if ext=='xlsx':
            metadata_pipe = get_parse_pipe("excel", "get_bytes", suffix=str(i))
        elif ext=='txt':
            metadata_pipe = get_parse_pipe("txt", "get_bytes", suffix=str(i))
        else:
            metadata_pipe = get_parse_pipe("csv", "get_bytes", suffix=str(i))
        metadata_pipe.append(
            ("add_to_resource"+str(i), 'add_to_op_resource', {"in_to_op":{'metadata': 'additional_metadata'}})
        )
        metadata_pipe.append(("remove_resource_from_result"+str(i), 'remove_keys', {"keys_to_remove":["metadata"]})
        )
        metadata_pipe.extend(merge_parsed_metadata_pipe)
        runtime_params_dict = {}
        runtime_params_dict[metadata_pipe[0][0]] = {"path": additional_metadata_file_path}
        basic_labcas_publishing.add_pipes(resource, metadata_pipe, runtime_params_dict=runtime_params_dict)

    # add already defined processes to the main pipe (this is where you are assembling multiple process definitions for task initialization in one go!)
    main_pipe=[]
    main_pipe.extend(merge_parsed_metadata_pipe)
    main_pipe.extend(base_pipe)

    # add tasks pertaining to thumbnail generation
    if not isdir:
        file_extention = resource_name.split('.')[-1]
        thumbnail_plugin_to_apply = file_ext_to_thumbnail_plugin.get(file_extention, None)
        if thumbnail_plugin_to_apply is not None:
            thumbnail_rel_path = os.path.join(os.path.dirname(resource),
                                              resource_name.replace('.' + file_extention, '.png'))
            thumbnail_path = os.path.join(thumbnails_dir, thumbnail_rel_path)
            # create the dir structure
            main_pipe.append(("create_required_dirs_for_thumbnail", "jpl.pipedreams.plugins.file_ops.disk.makedirs",
                              {"path": os.path.dirname(thumbnail_path)}))
            # create a thumbnail if not already exists or if forced to redo
            main_pipe.append(
                ("generate_thumbnail", "jpl.pipedreams.plugins.generate_thumbnails." + thumbnail_plugin_to_apply+'.generate_thumbnail',
                 {"image_filepath": resource_path, "thumbnail_filepath": thumbnail_path}))


    # add some more runtime params for the tasks to be initialized (mostly the ones that are not common for the underlying process)
    runtime_params_dict={}
    runtime_params_dict['process_meta_basic'] = {"config_obj": basic_config_obj}
    runtime_params_dict['publish_to_solr'] = {"url": solr_url, "mock": True}
    runtime_params_dict['add_basic_meta'] = {"basic_metadata": basic_metadata}
    runtime_params_dict['add_additional_meta'] = {"resource": resource}
    if isdir and not isCollection:
        runtime_params_dict['add_basic_down_send'] = {'basic_down_metadata': {"DatasetParentId": resource}}

    # use your pipe to init multiple tasks and add them to the task graph
    basic_labcas_publishing.add_pipes(resource, main_pipe, runtime_params_dict=runtime_params_dict)

    # connect this level/resource with all its child levels/resources
    for resource_child_path in resource_children_path:
        resource_child=os.path.relpath(resource_child_path, data_dir)
        resource_child_name = os.path.basename(resource_child)
        if '.met' in resource_child_name or '.xmlmet' in resource_child_name or '.cfg' in resource_child_name or '.listing' == resource_child_name:
            continue
        # get and reuse some previously defined process definitions to initialize more tasks
        basic_labcas_publishing.add_pipes(resource_child, get_pipe_by_name(base_pipe, ['up_receive']))
        basic_labcas_publishing.add_pipes(resource_child, get_pipe_by_name(base_pipe, ['up_send']))
        # add tasks explicitly to a certain place in the task graph
        basic_labcas_publishing.add_connection(resource, 'down_send', resource_child, 'up_receive')
        basic_labcas_publishing.add_connection(resource_child, 'up_send', resource, 'down_receive')

# ===== run the task graph
basic_labcas_publishing.run_graph(processes=10)

"""
Notes on adding metadata to directories (Collection and Datasets) and files:-

To a single file:
    - In .cfg or .xmlmet format with the same name and location as the file with an additional extention of .cfg or .xmlmet resp.

To a single file or directory:
    - in an excel, csv or txt (essentially a tab separated csv) format to a single file or directory:
        -use _META in the name of the file,
            Or the file path has been provided as an additional metadata file
        -make sure it is either in the same location as the file or dir or in a parent directory
        -make sure there is a row with all the metadata and a column; either called FileName with the exact name of that file or dir,
            Or called LABCAS_ID with the LabCAS ID of that file or dir 

To multiple files or directories:
    - in an excel, csv or txt (essentially a tab separated csv) format to a single file or directory:
        -use _META in the name of the file,
            Or the file path has been provided as an additional metadata file
        -make sure it is either in the same location as the files or directories or in a parent directory
        -make sure there is a row (per file/dir) with all the metadata and a column; either called FileName with the exact name of per file or dir,
            Or called LABCAS_ID with the LabCAS ID of the files or dirs
"""

"""
TODO:
-find out what else to add as part of the collection specific plugins
    -add the step right after 'process_meta_basic'
    -get the most recent plugin implementations from master branch
    -replace the argument list (add op_resouces) and file reading with just getting it from the op_resource
    -move all the kwargs from the publishing script to runtime kwargs for that task
    -make sure the relevant files are added to op_resource with proper names
        -make sure the 'add_additional_meta' is switched off wherever necessary
-create a simpler pipeline example

-publish datasets using this in mcl dev
-create .zip files when necessary and publish the zipped ones too
    -add a pipe result_name_change_2 -> zip_file -> publish_zip_to_solr
-some stray k,v: Task_ID is being passed in params somehow!
-convert this into a framework!
"""



