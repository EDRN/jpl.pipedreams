# encoding: utf-8

'''Demonstration. This is a demo to show the usage of jpl.pipedreams'''


import os
import time
from jpl.pipedreams.data_pipe import Operation
from plugins.general.for_demo import add_suffix_to_dict_values, retrieve_additional_metadata

# Let us declare some global variables first
base_data_path = os.path.join(os.path.dirname(__file__), 'data') # the path to the test data

# here we will state the url for the redis instance we seek to use
redis_path='redis://localhost:6379'
# you will also have to provide the relative path to your directory with all your plugins.
# This helps us find all your functions and register them as Celery Workers.
plugins_dir_list=['plugins']


# Hello World!
# ============
#
# Here we will go through the steps rather quickly and explain things more clearly in the next section.
#
# First, initialize an operation (an operation contains a task graph associated with it):
my_first_operation = Operation(name='my_first_operation', redis_path=redis_path, include_plugins=plugins_dir_list)

# Declare your process using a plugin function:
process_list = [
    ["hello_world_read", "plugins.file_ops.disk.read_str", {"path": os.path.join(base_data_path, 'mydata0.txt')}]
]

"""
- The 'process_list' may contain multiple process declarations with the following format:
    (<process_name: give a name to this process>, <plugin path or a function etc.>, <any params needed for the function to run>)
"""
# add the declaration to your operation
my_first_operation.add_pipes("mydata0.txt", process_list)
# run the operation
my_first_operation.run_graph()


# ========================= The one where things start to get complicated...I mean complex!
# ======================================================================================================================
"""
- Here we will create a pipeline where a .cfg file is read and some simple process is applied to the contents.
"""
my_second_operation = Operation(name='my_second_operation', redis_path=redis_path, include_plugins=plugins_dir_list)
# declare the processes that run sequentially in a single template; we call this a template cause you can reuse it later.
main_task_template = [
    # read the metadata file from disk
    ["read_cfg", "plugins.file_ops.disk.read_str", None],
    # parse the string into a dictionary
    ["parse_cfg", "plugins.metadata_parsers.cfg.parse_metadata", None],
    # change the name to match the input of the next function
    ["result_change_name", 'change_name', {'in_to_out': {'metadata': 'meta_input'}}],
    # do some simple processing to the metadata
    ["process_metadata", add_suffix_to_dict_values, {"suffix": "|", "op_out": ["metadata"]}],
]

# using your template, initialize/add tasks to your operation all at once
my_second_operation.add_pipes(resource_ID="mydata1.cfg", processes=main_task_template, runtime_params_dict={'read_cfg': {'path': os.path.join(base_data_path, 'mydata1.cfg')}})


"""
- The above 'add_pipes' call, takes each item in the declared template and initializes a unique task with 'resource_ID' and 
    'processe_name' together as the primary key.
- Notice that we can use any imported function, like 'add_suffix_to_dict_values' 
    or, a well defined plugin (using our interface), like 'jpl.pipedreams.plugins.file_ops.disk.read_str'
    or, even some internal connector functions, like 'change_name'
- Using the 'runtime_params_dict' you can also pass more params for you task functions. As a rule of thumb, 
    you can add the params that can be reused, in the template declaration, and the ones that may change with each task 
    initialization, during the 'add_pipes' call.
- Notice that the internal function 'change_name' makes sure that the 'metadata' param is fed into the 'meta_input' 
    param of the function 'add_suffix_to_dict_values'.
- Notice the 'op_out' param in the last process, what it does is makes sure that the result of 
    the 'add_suffix_to_dict_values' function gets the name 'metadata'.
"""
my_second_operation.run_graph()
print('Results:', my_second_operation.results)


# ========================= The one where we do much less work!
# ======================================================================================================================
my_second_operation.add_pipes(resource_ID="mydata2.cfg", processes=main_task_template, runtime_params_dict={'read_cfg': {'path': os.path.join(base_data_path, 'mydata2.cfg')}})

"""
- Here we used our earlier template to initialize some more tasks but with a different 'resource_ID' 
    (making them independent tasks of course) and we also feed a different file to this pipeline
- Notice that we used the filename also as the 'resource_ID'. To be honest, you can use any name 
    above and it won't be an issue.
"""
my_second_operation.run_graph(processes=1)
"""
- If you give the 'process' a value more than 1, it uses Celery and Redis to parallelize the graph execution.
- Try it but make sure you have a redis client running and have Celery installed!
"""
time.sleep(3)


# ========================= The one where the long lost twins meet!
# ======================================================================================================================
# declare a new process, to be used to merge results from the already declared pipelines
merge_template = ("data_merge", 'merge', {"in_multi": "metadata",  "merge_type": "collect"})
my_second_operation.add_pipes(resource_ID="data_merge1", processes=[merge_template])
"""
- Here we are intending to merge the two results from earlier, both called 'metadata', such that the duplicate keys 
    with different values get joined together in a list. This highlights the usefulness of another internal function.
"""
my_second_operation.add_connection(s_resource_ID='mydata1.cfg', s_name='process_metadata', t_resource_ID='data_merge1', t_name='data_merge')
my_second_operation.add_connection(s_resource_ID='mydata2.cfg', s_name='process_metadata', t_resource_ID='data_merge1', t_name='data_merge')
"""
- Since we had already declared and initialized all the tasks, in above we just connect the tasks together
"""
my_second_operation.run_graph()


# ========================== The one where the kids steal their parent's car keys
# ======================================================================================================================
my_third_operation = Operation(name='my_third_operation', redis_path=redis_path, include_plugins=plugins_dir_list)

add_op_resource = [
    # read the bytes of the file from disk
    ["read_excel", "plugins.file_ops.disk.get_bytes", None],
    # parse the excel into a dataframe
    ["excel_to_df", "plugins.metadata_parsers.excel.parse_metadata", None],
    # add the result to the op resources
    ["add_extra_metedata_resource", 'add_to_op_resource', {"in_to_op": {'metadata': 'additional_metadata'}}],
    # remove the op resource part of the result from the result
    ["remove_resource_from_result", 'remove_keys', {"keys_to_remove":["metadata"]}]
]
"""
- We defined a process template where we intend to read an excel sheet and make it available to all our successor tasks
    by using the internal function 'add_to_op_resource'.
- Notice that we also removed it from the output of the task, as it was completely unnecessary since the very next task 
    may not need it!
"""
main_task_template = [
    # read the metadata file from disk
    ["read_cfg", "plugins.file_ops.disk.read_str", None],
    # parse the string into a dictionary
    ["parse_cfg", "plugins.metadata_parsers.cfg.parse_metadata", None],
    # add the additional metadata to the main metadata
    ["use_the_added_resource", retrieve_additional_metadata, None]
]
"""
- Here the function 'retrieve_additional_metadata' gives a good example of how to use the op_resource we added earlier.
    Go chek out the implementation of it.
- This helps us load resources only one time and let it be used by inheriting tasks!
"""
runtime_params_dict = {
    'read_cfg': {'path': os.path.join(base_data_path, 'mydata1.cfg')},
    'read_excel': {'path': os.path.join(base_data_path, 'mymapping.xlsx')}
}
my_third_operation.add_pipes(resource_ID="mydata1.cfg", processes=add_op_resource+main_task_template, runtime_params_dict=runtime_params_dict)
my_third_operation.run_graph()

"""
Now, let us simplify things further by defining templates.
"""
my_fourth_operation = Operation(name='my_fourth_operation', redis_path=redis_path, include_plugins=plugins_dir_list)

main_task_template = [
    # read the metadata file from disk
    ["read_cfg", "plugins.file_ops.disk.read_str"],
    # parse the string into a dictionary
    ["plugins.metadata_parsers.cfg.parse_metadata"],
    # change the name to match the input of the next function
    ['change_name', {'in_to_out': {'metadata': 'meta_input'}}],
    # do some simple processing to the metadata
    [add_suffix_to_dict_values, {"suffix": "|", "op_out": ["metadata"]}],
]
# add this to the operation as a template that can be used by its name later.
my_fourth_operation.define_template('metadata_reader', main_task_template)

my_fourth_operation.add_pipes(resource_ID="mydata1.cfg", processes=[['metadata_reader']], runtime_params_dict={'read_cfg': {'path': os.path.join(base_data_path, 'mydata1.cfg')}})
my_fourth_operation.add_pipes(resource_ID="mydata2.cfg", processes=[['metadata_reader']], runtime_params_dict={'read_cfg': {'path': os.path.join(base_data_path, 'mydata2.cfg')}})
my_fourth_operation.add_pipes(resource_ID="data_merge1", processes=[["data_merge", 'merge', {"in_multi": "metadata",  "merge_type": "collect"}]])
my_fourth_operation.add_connection(s_resource_ID='mydata1.cfg', s_name='metadata_reader', t_resource_ID='data_merge1', t_name='data_merge')
my_fourth_operation.add_connection(s_resource_ID='mydata2.cfg', s_name='metadata_reader', t_resource_ID='data_merge1', t_name='data_merge')
my_fourth_operation.run_graph()

"""
let us create a graph within a graph!
"""

my_fifth_operation = Operation(name='my_fifth_operation', redis_path=redis_path, include_plugins=plugins_dir_list)

main_task_template = [
    # read the metadata file from disk
    ["read_cfg", "plugins.file_ops.disk.read_str"],
    # parse the string into a dictionary
    ["plugins.metadata_parsers.cfg.parse_metadata"],
    # change the name to match the input of the next function
    ['change_name', {'in_to_out': {'metadata': 'meta_input'}}],
    # do some simple processing to the metadata
    [add_suffix_to_dict_values, {"suffix": "|", "op_out": ["metadata"]}],
]
# add this to the operation as a template that can be used by its name later.
my_fifth_operation.define_template('metadata_reader', main_task_template)

def some_process(new_operation):
    new_operation.add_pipes(resource_ID="mydata1.cfg", processes=[['metadata_reader']], runtime_params_dict={'read_cfg': {'path': os.path.join(base_data_path, 'mydata1.cfg')}})
    return

my_fifth_operation.add_pipes(resource_ID="graph_create_1", processes=[[some_process]])
my_fifth_operation.run_graph()

