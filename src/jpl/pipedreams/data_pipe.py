# encoding: utf-8

'''Resources and tasks for data pipes'''

from .celery_task_registry import celery_obj_func_runner, celery_indi_func_runner
from .plugins_ops import PluginCollection
from .utils.misc_utils import merge_dict, merge_dicts, nested_set, collect_dicts, ignore_unmatched_kwargs
import copy
import datetime
import inspect
import networkx as nx
import os
import shlex
import subprocess
import time


class Resource(object):

    def __init__(self, ID: str, **kwargs):
        self.ID = ID
        self.resources = kwargs


class Task(object):

    def __init__(self, name: str, process, resource_ID: str, plugin_collection: PluginCollection, run_function=None, params: dict=None, op_params: dict=None):

        if params is None:
            params={}
        if op_params is None:
            op_params={}

        is_plugin = False
        if type(process) == str:
            process_name=str(process)
            process = plugin_collection.get_plugin(process)
            is_plugin=True
        elif hasattr(process, '__call__'):
            process_name = process.__name__
        else:
            pass # todo : throw error
            print('process type not recognized: '+ str(type(process)))
            return

        if run_function is not None:
            process_name+='..'+run_function

        self.name=name
        self.resource_ID=resource_ID
        self.process=process
        self.process_name=process_name
        self.is_plugin=is_plugin
        self.result={}
        self.params=params
        self.op_params=op_params
        self.run_function=run_function

    @staticmethod
    def concoct_task_ID(name, resource_ID):
        return name + '|+|' + resource_ID

    def get_task_ID(self):
        return Task.concoct_task_ID(self.name, self.resource_ID)

    def run_task(self, single_process=True, **kwargs):
        for k, v in self.params.items():
            kwargs[k]=v

        self.params=kwargs

        if self.is_plugin:
            if self.run_function is not None:
                if single_process:
                    self.result = self.process.apply(self.run_function, **kwargs)
                else:
                    self.result=celery_obj_func_runner.delay(self.process, self.run_function, **kwargs)
            else:
                if single_process:
                    self.result = self.process.run(**kwargs)
                else:
                    self.result = celery_obj_func_runner.delay(self.process, 'run', **kwargs)
        else:
            if single_process:
                self.result=ignore_unmatched_kwargs(self.process)(**kwargs)
            else:
                self.result = celery_indi_func_runner.delay(self.process, **kwargs)

    def postprocess_results(self):

        # convert the result into a dict based on the op_params if not already a dict!
        if "op_out" in self.op_params.keys():
            if type(self.result) != tuple:
                self.result = tuple([self.result])
            result_dict = {}
            for i, k in enumerate(self.op_params["op_out"]):
                result_dict[k] = self.result[i]
            self.result = result_dict

        # in case the function does not return any results
        if self.result is None:
            self.result={}

        # a process metadata that tracks which tasks have been applied to the artifact so far
        process_undergone = self.params.get('processes_undergone', list())
        process_undergone.append(self.name)
        self.result['processes_undergone'] = process_undergone

def register_connector_func(func):
    """
    a dummy decorator
    """
    return func

def register_non_parallelizable_connector_func(func):
    """
    a dummy decorator
    """
    return func

def methodsWithDecorator(cls, decoratorName):
    """
    Find all the methods names of a class with a particular decorator applied
    """
    sourcelines = inspect.getsourcelines(cls)[0]
    for i,line in enumerate(sourcelines):
        line = line.strip()
        if line.split('(')[0].strip() == '@'+decoratorName: # leaving a bit out
            nextLine = sourcelines[i+1]
            name = nextLine.split('def')[1].split('(')[0].strip()
            yield(name)

class Operation(object):

    # ======== result connection/manipulation help functions:

    @register_connector_func
    def change_name(self, in_to_out:dict, **kwargs):
        return {in_to_out.get(k, k): v for k, v in kwargs.items()}

    @register_connector_func
    def remove_keys(self, keys_to_remove, result_levels=None, **kwargs):
        if result_levels is None:
            result_levels = []
        level_value = kwargs
        for level in result_levels:
            level_value = level_value[level]
        level_value_edit = {k: v for k, v in level_value.items() if k not in keys_to_remove}
        kwargs=nested_set(kwargs, result_levels, level_value_edit)
        return kwargs

    @register_non_parallelizable_connector_func
    def add_to_op_resource(self, in_to_op: dict, **kwargs):
        for resource_name, resource_name_new in in_to_op.items():
            if kwargs['task_ID'] not in self.added_resources.keys():
                self.added_resources[kwargs['task_ID']]={}
            self.added_resources[kwargs['task_ID']][resource_name_new]=kwargs[resource_name]
            # print('DBG adding 1:', kwargs['task_ID'], resource_name_new, kwargs[resource_name])
            # print('DBG adding 2:', self.added_resources)
        kwargs.pop('task_ID')
        return kwargs

    @register_connector_func
    def merge(self, in_multi, out="collapsed_results", merge_type='forced_ordered', **kwargs):
        list_of_dict = []
        if type(in_multi)==list:
            for result_name in in_multi:
                list_of_dict.append(kwargs.get(result_name, {}))
                kwargs.pop(result_name) if result_name in kwargs.keys() else 0

        if type(in_multi)==str and in_multi in kwargs.keys():
            if out == 'collapsed_results':
                out = in_multi
            list_of_dict = kwargs[in_multi]
        if merge_type=='forced_ordered':
            kwargs[out] = merge_dicts(list_of_dict)
        elif merge_type=='collect':
            kwargs[out] = collect_dicts(list_of_dict)
        return kwargs

    @register_connector_func
    def artificial_wait(self, wait_time, **kwargs):
        time.sleep(wait_time)
        return kwargs


    def __init__(self, name: str):
        self.task_graph=nx.DiGraph()
        self.name = name
        self.task_ID_to_task={}
        self.plugin_collection=PluginCollection()
        self.results={}
        self.params={}
        self.added_resources={}
        self.inherited_resource={}

        # add all the connector functions to a dictionary; to be accessed using their names
        self.connector_functions_mapping= {func_name: getattr(self, func_name) for func_name in list(methodsWithDecorator(Operation, 'register_connector_func'))}
        self.non_parallel_connector_functions_mapping={func_name: getattr(self, func_name) for func_name in list(methodsWithDecorator(Operation, 'register_non_parallelizable_connector_func'))}

    def add_edge(self, task_ID_A, task_ID_B):

        task_graph = self.task_graph
        task_ID_to_task = self.task_ID_to_task

        if task_ID_A not in task_ID_to_task.keys() or task_ID_B not in task_ID_to_task.keys():
            print('ERROR: Please, initialize the processes first using the \'add_pipes\' function!')
            return None
        print("Adding Edge: " + task_ID_A + " --> " + task_ID_B)
        task_graph.add_edge(task_ID_A, task_ID_B)
        # check if the above breaks the DAG assumptions
        if not nx.is_directed_acyclic_graph(task_graph):
            task_graph.remove_edge(task_ID_A, task_ID_B)
            print("LOOP ERROR: :",
                task_ID_A + " --> " + task_ID_B + " could not be added because it will create a loop!")

    def add_pipes(self, resource_ID:str, processes:list, runtime_params_dict:dict=None, resource_dict:dict=None):
        """
        processes: a list of tuples (process_name, process)
        runtime_params_dict: {process_name:runtime_params_as_dict}}
        """

        runtime_params_dict={} if runtime_params_dict is None else copy.deepcopy(runtime_params_dict)
        resource_dict={} if resource_dict is None else copy.deepcopy(resource_dict)

        task_graph=self.task_graph
        task_ID_to_task=self.task_ID_to_task

        task_prev=None
        for i, (name, process, runtime_params) in enumerate(processes):
            runtime_params = {} if runtime_params is None else copy.deepcopy(runtime_params)
            op_param_keys=[key for key in runtime_params.keys() if 'op_' in key]
            op_params={k:runtime_params[k] for k in op_param_keys}
            for k in op_param_keys:
                runtime_params.pop(k)
            task_ID=Task.concoct_task_ID(name, resource_ID)
            # check if it is an invocation request for an internal utility function
            run_function=None
            if type(process)==str and (process in self.connector_functions_mapping.keys() or process in self.non_parallel_connector_functions_mapping.keys()):
                process=self.connector_functions_mapping.get(process, process)
                if type(process)==str:
                    process=self.non_parallel_connector_functions_mapping[process]
                runtime_params['task_ID']=task_ID
            elif type(process)==str and 'plugins.' in process:
                run_function=process.split('.')[-1]
                process='.'.join(process.split('.')[:-1])

            if task_ID not in task_ID_to_task.keys():
                # merge the runtime params provided during declaration of the pipe and addition of the pipe!
                runtime_params=merge_dict(runtime_params, runtime_params_dict.get(name, {}))
                task=Task(name, process, resource_ID, self.plugin_collection, run_function, runtime_params, op_params)
                task_ID_to_task[task.get_task_ID()] = task
                print('Adding Node:', task_ID)
                task_graph.add_node(task_ID, process=process)
            else:
                task=task_ID_to_task[task_ID]
            if i!=0:
                self.add_edge(task_prev.get_task_ID(), task.get_task_ID())

            # add any explicitly provided resources for this task; these will be made available to any downstream tasks
            for resource_name, resource in resource_dict.get(name, {}).items():
                if task_ID not in self.added_resources[task_ID].keys():
                    self.added_resources[task_ID] ={}
                self.added_resources[task_ID][resource_name]=resource

            task_prev=task


    def add_connection(self, resource_ID_A, name_A, resource_ID_B, name_B):
        """
        To connect two tasks which have been already initialized using the function: add_pipes
        """
        task_ID_A= Task.concoct_task_ID(name_A, resource_ID_A)
        task_ID_B = Task.concoct_task_ID(name_B, resource_ID_B)
        self.add_edge(task_ID_A, task_ID_B)

    def task_prep(self, task_ID):
        print('\n')
        # print('DBG: all_added_resources:', self.added_resources.get(task_ID, None))
        # print('DBG: all_inherited_resource:', self.inherited_resource)
        # gather the results from the parent tasks
        params = {}
        resources = {}
        for parent_task_ID in self.task_graph.predecessors(task_ID):
            # print('DBG: parent_task_ID:', parent_task_ID)
            parent_task = self.task_ID_to_task[parent_task_ID]
            for k, v in parent_task.result.items():
                if k not in params.keys():
                    params[k] = []
                    # todo: can provide more options in run_graph as to how to resolve this issue!
                params[k].append(v)

            # add the explicitly added resources of parent tasks to this task's inherited resources
            if parent_task_ID in self.added_resources.keys():
                # print('DBG: found explicit resource of parent')
                if task_ID not in self.inherited_resource.keys():
                    self.inherited_resource[task_ID] = {}
                for resource_name, resource in self.added_resources[parent_task_ID].items():
                    if parent_task_ID not in self.inherited_resource[task_ID].keys():
                        self.inherited_resource[task_ID][parent_task_ID] = {}
                    self.inherited_resource[task_ID][parent_task_ID][resource_name] = resource

            # add the inherited resources of parent as well to this task's inherited resources
            if parent_task_ID in self.inherited_resource.keys():
                # print('DBG: found inherited resource of parent')
                if task_ID not in self.inherited_resource.keys():
                    self.inherited_resource[task_ID] = {}
                for predessesor_task_ID, resource_dict in self.inherited_resource[parent_task_ID].items():
                    for resource_name, resource in resource_dict.items():
                        if predessesor_task_ID not in self.inherited_resource[task_ID].keys():
                            self.inherited_resource[task_ID][predessesor_task_ID] = {}
                        self.inherited_resource[task_ID][predessesor_task_ID][resource_name] = resource

        # collect all resources (current and inherited for this task)
        resources = self.inherited_resource.get(task_ID, {})
        if task_ID in self.added_resources.keys():
            resources[task_ID] = self.added_resources[task_ID]

        # in case of duplicate param names from different task results the results will be in list with the same param name:
        for k, v in params.items():
            if len(v) == 1:
                params[k] = v[0]

        params['op_resources'] = resources

        return params

    # # OLD CODE: for non parallel task execution
    # def run_graph(self):
    #     for task_ID in nx.topological_sort(self.task_graph):
    #         task = self.task_ID_to_task[task_ID]
    #         params=self.task_prep(task_ID)
    #         print("Running:", task_ID)
    #         print("   ---> with inherited params (from parent(s) task result(s)):", params)
    #         print("   ---> with runtime params:", task.runtime_params)
    #         task.run_task(single_process=True, **params)
    #         task.postprocess_results(single_process=True, **params)
    #         print("     ---> result:", task.result)
    #         # gather all the params and task results for this operation
    #         self.params[task_ID]=params
    #         self.results[task_ID]=task.result


    def run_graph(self, processes=1):

        if processes<1:
            processes=1

        start=datetime.datetime.now()
        if processes>1:
            # todo: make sure redis is running
            # start a single Celery worker that can spawn multiple processes
            subprocess.Popen(
                shlex.split("celery -A jpl.pipedreams.celeryapp:app worker -l INFO --concurrency="+str(processes)+" -n worker1"),
                stdout=open(os.devnull, 'wb'))

        task_graph=self.task_graph
        next=set()
        added=set()
        completed=set()

        # find all nodes with 0 in-degree and add them to the 'next list'
        seed_tasks=[task_ID for task_ID in task_graph.nodes if task_graph.in_degree(task_ID)==0]
        next.update(seed_tasks)
        task_completed_count=0
        while (len(next)!=0 or len(added)!=0):

            # sweep the next queue and add tasks to workers or get them done
            to_remove=[]
            to_add=[]
            for next_task_ID in next:
                # check if all the parents are in the completed queue
                predecessors=task_graph.predecessors(next_task_ID)
                ripe=True
                for predecessor_ID in predecessors:
                    if predecessor_ID not in completed:
                        ripe=False
                if ripe:
                    next_task = self.task_ID_to_task[next_task_ID]
                    # gather params from parents
                    params=self.task_prep(next_task_ID)
                    print("Adding to Run Queue:", next_task_ID)
                    print("   ---> with inherited params (from parent(s) task result(s)):", params)
                    print("   ---> with self params:", next_task.params)
                    if processes==1 or next_task_ID in self.non_parallel_connector_functions_mapping.keys():
                        next_task.run_task(single_process=True, **params)
                        next_task.postprocess_results()
                        print("Non-parallel Task Completed:", next_task_ID)
                        print("     ---> result:", next_task.result)
                        self.results[next_task_ID]=next_task.result
                        completed.add(next_task_ID)
                        task_completed_count += 1
                        # add the children to next
                        for new_next_task_ID in task_graph.successors(next_task_ID):
                            to_add.append(new_next_task_ID)
                    else:
                        next_task.run_task(single_process=False, **params)
                        added.add(next_task_ID)
                to_remove.append(next_task_ID)
            for task_ID in to_remove:
                next.remove(task_ID)
            for task_ID in to_add:
                next.add(task_ID)

            # sweep the added queue for completed tasks and move them to the completed queue
            to_remove=[]
            for added_task_ID in added:
                added_task=self.task_ID_to_task[added_task_ID]
                if str(added_task.result.state)=='SUCCESS':
                    task_completed_count+=1
                    added_task.result=added_task.result.get()
                    added_task.postprocess_results()
                    print("Parallel Task Completed:", added_task_ID)
                    print("     ---> result:", added_task.result)
                    self.results[added_task_ID] = added_task.result
                    completed.add(added_task_ID)
                    to_remove.append(added_task_ID)
                    # add the children to next
                    for next_task_ID in task_graph.successors(added_task_ID):
                        next.add(next_task_ID)

            for task_ID in to_remove:
                added.remove(task_ID)

        # kill celery worker
        subprocess.call(shlex.split("pkill -f \"celery\""))
        print('num nodes in task graph:', len(task_graph.nodes))
        print('num task completed:', task_completed_count)
        print('time taken:', datetime.datetime.now()-start)
