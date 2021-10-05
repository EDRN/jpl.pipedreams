# encoding: utf-8

'''Resources and tasks for data pipes'''

from .plugins_ops import PluginCollection
from .utils.misc_utils import merge_dict, merge_dicts, nested_set, collect_dicts, MyException
import copy
import datetime
import networkx as nx
import os
import shlex
import subprocess
import time, sys
from tqdm import tqdm
from jpl.pipedreams.celeryapp import CeleryDreamer, obj_func_runner, indi_func_runner
import inspect

class Resource(object):

    def __init__(self, ID: str, **kwargs):
        self.ID = ID
        self.resources = kwargs


class Task(object):

    def __init__(self, name: str, process, resource_ID: str, plugin_collection: PluginCollection, celerydreamer,
                 run_function=None, params: dict = None, op_params: dict = None):

        if params is None:
            params = {}
        if op_params is None:
            op_params = {}

        is_plugin = False
        if type(process) == str:
            process_name = str(process)
            process = plugin_collection.get_plugin(process)
            is_plugin = True
        elif hasattr(process, '__call__'):
            process_name = process.__name__
        else:
            pass  # todo : throw error
            print('process type not recognized: ' + str(type(process)))
            return

        if run_function is not None:
            process_name += '..' + run_function

        self.name = name
        self.resource_ID = resource_ID
        self.process = process
        self.process_name = process_name
        self.is_plugin = is_plugin
        self.result = {}
        self.params = params
        self.op_params = op_params
        self.run_function = run_function
        self.celerydreamer = celerydreamer
        self.time_taken=None # in seconds
        self.objects={} # these objects will go into the process like a param that can be added upon by the process

    @staticmethod
    def get_process_name(process):
        if type(process) == str:
            return process
        elif hasattr(process, '__call__'):
            return process.__name__
        else:
            MyException('Error: Process name could not be resolved!')

    @staticmethod
    def concoct_task_ID(name, resource_ID):
        return name + '|+|' + resource_ID

    @staticmethod
    def task_ID_to_resource_ID(task_ID):
        return task_ID.split('|+|')[1]

    @staticmethod
    def task_ID_to_function_name(task_ID):
        return task_ID.split('|+|')[0]

    def get_task_ID(self):
        return Task.concoct_task_ID(self.name, self.resource_ID)

    def run_task(self, single_process=True, **kwargs):
        for k, v in self.params.items():
            kwargs[k] = v

        self.params = kwargs

        if self.is_plugin:
            if self.run_function is not None:
                if single_process:
                    self.result = obj_func_runner(self.process, self.run_function, self.objects, **kwargs)
                else:
                    self.result = self.celerydreamer.celery_obj_func_runner.delay(self.process, self.run_function, self.objects, **kwargs)
            else:
                if single_process:
                    self.result = obj_func_runner(self.process, 'run', self.objects, **kwargs)
                else:
                    self.result = self.celerydreamer.celery_obj_func_runner.delay(self.process, 'run', self.objects, **kwargs)
        else:
            if single_process:
                self.result = indi_func_runner(self.process, self.objects, **kwargs)
            else:
                self.result = self.celerydreamer.celery_indi_func_runner.delay(self.process, self.objects, **kwargs)

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
            self.result = {}

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
    for i, line in enumerate(sourcelines):
        line = line.strip()
        if line.split('(')[0].strip() == '@' + decoratorName:  # leaving a bit out
            nextLine = sourcelines[i + 1]
            name = nextLine.split('def')[1].split('(')[0].strip()
            yield (name)


class Operation(object):

    # ======== result connection/manipulation help functions:

    @staticmethod
    @register_connector_func
    def change_name(in_to_out: dict, **kwargs):
        return {in_to_out.get(k, k): v for k, v in kwargs.items()}

    @staticmethod
    @register_connector_func
    def remove_keys(keys_to_remove, result_levels=None, **kwargs):
        if result_levels is None:
            result_levels = []
        level_value = kwargs
        for level in result_levels:
            level_value = level_value[level]
        level_value_edit = {k: v for k, v in level_value.items() if k not in keys_to_remove}
        kwargs = nested_set(kwargs, result_levels, level_value_edit)
        return kwargs

    @register_non_parallelizable_connector_func
    def add_to_op_resource(self, in_to_op: dict, **kwargs):
        for resource_name, resource_name_new in in_to_op.items():
            if kwargs['task_ID'] not in self.added_resources.keys():
                self.added_resources[kwargs['task_ID']] = {}
            self.added_resources[kwargs['task_ID']][resource_name_new] = kwargs[resource_name]
            # print('DBG adding 1:', kwargs['task_ID'], resource_name_new, kwargs[resource_name])
            # print('DBG adding 2:', self.added_resources)
        kwargs.pop('task_ID')
        return kwargs

    @staticmethod
    @register_connector_func
    def merge(in_multi, out="collapsed_results", merge_type='forced_ordered', **kwargs):
        list_of_dict = []
        if type(in_multi) == list:
            for result_name in in_multi:
                list_of_dict.append(kwargs.get(result_name, {}))
                kwargs.pop(result_name) if result_name in kwargs.keys() else 0

        if type(in_multi) == str and in_multi in kwargs.keys():
            if out == 'collapsed_results':
                out = in_multi
            list_of_dict = kwargs[in_multi]
        if merge_type == 'forced_ordered':
            kwargs[out] = merge_dicts(list_of_dict)
        elif merge_type == 'collect':
            kwargs[out] = collect_dicts(list_of_dict)
        return kwargs

    @staticmethod
    @register_connector_func
    def artificial_wait(wait_time, **kwargs):
        time.sleep(wait_time)
        return kwargs

    def generate_process_ID(self):
        self.counter+=1
        return str(self.counter)

    def __init__(self, name: str, redis_path=None, include_plugins=None):
        self.instructions = []
        self.task_graph = nx.DiGraph()
        self.name = name
        self.task_ID_to_task = {}
        self.plugin_collection = PluginCollection()
        self.results = {}
        self.inherited_params = {}
        self.self_params = {}
        self.added_resources = {}
        self.inherited_resource = {}
        self.redis_path = redis_path
        self.include_plugins = include_plugins
        self.times = {}
        self.cache = {}
        self.templates={}
        self.counter=0

        # add all the connector functions to a dictionary; to be accessed using their names
        self.connector_functions_mapping = {func_name: getattr(Operation, func_name) for func_name in
                                            list(methodsWithDecorator(Operation, 'register_connector_func'))}
        self.non_parallel_connector_functions_mapping = {func_name: getattr(self, func_name) for func_name in list(
            methodsWithDecorator(Operation, 'register_non_parallelizable_connector_func'))}

        if include_plugins is None:
            include_plugins = []
        if redis_path is not None:
            self.celerydreamer = CeleryDreamer(include_plugins, redis_path)

    def prepare_results(self):
        prepared_results=[]
        for task_ID, result in self.results.items():
            prepared_results.append({
            'resource_ID' : Task.task_ID_to_resource_ID(task_ID),
            'function_applied' : Task.task_ID_to_function_name(task_ID),
            'time_taken' : self.times.get(task_ID, None),
            'inherited_params' : self.inherited_params.get(task_ID, None),
            'self_params' : self.self_params.get(task_ID, None),
            })
        return prepared_results

    def execute_instructions(self):
        new_nodes_created=[]
        for function_name, params in self.instructions:
            result=self.__getattribute__(function_name)(**params)
            if type(result)==dict and 'new_nodes_created' in result.keys():
                new_nodes_created.extend(result['new_nodes_created'])
        self.instructions=[]
        return new_nodes_created

    def _add_to_instructions(self, params, function_name):
            params['delayed']=False # so that while execution it is actually executed!
            params.pop('self')
            self.instructions.append((function_name, params))


    def add_to_global_cache(self, ID, resource, delayed=True):
        if delayed==True:
            self._add_to_instructions(locals(), inspect.stack()[0][3])
            return

        self.cache[ID]=resource

    def define_template(self, name, processes, delayed=True):
        if delayed==True:
            self._add_to_instructions(locals(), inspect.stack()[0][3])
            return
        self.templates[name]=self._normalize_process_details(processes)

    def add_edge(self, task_ID_A, task_ID_B, silent=False, delayed=True):

        if delayed==True:
            self._add_to_instructions(locals(), inspect.stack()[0][3])
            return

        task_graph = self.task_graph
        task_ID_to_task = self.task_ID_to_task

        if task_ID_A not in task_ID_to_task.keys():
            raise MyException('ERROR: Please, initialize the processes first using the \'add_pipes\' function: '+task_ID_A)
        if task_ID_B not in task_ID_to_task.keys():
            raise MyException('ERROR: Please, initialize the processes first using the \'add_pipes\' function: '+task_ID_B)
        if not silent:
            print("Adding Edge: " + task_ID_A + " --> " + task_ID_B)
        # check if the above breaks the DAG assumptions
        if not nx.has_path(task_graph, task_ID_B, task_ID_A):
            task_graph.add_edge(task_ID_A, task_ID_B)
        else:
            print("LOOP ERROR: :",
                      task_ID_A + " --> " + task_ID_B + " could not be added because it will create a loop!")

    def _normalize_process_details(self, processes):

        # check if there are any calls to templates and unroll them
        processes_ = []
        for process_details in processes:
            if len(process_details) == 1 and process_details[0] in self.templates.keys():
                processes_.extend(self.templates[process_details[0]])
            else:
                processes_.append(process_details)
        processes = processes_

        processes_=[]
        for i, process_details in enumerate(processes):
            if len(process_details)==1: # (process)
                process=process_details[0]
                name=Task.get_process_name(process)+'_'+self.generate_process_ID()
                runtime_params = None
            elif len(process_details)==2:
                if type(process_details[1])==dict: # (process, runtime_params)
                    process = process_details[0]
                    runtime_params = process_details[1]
                    name = Task.get_process_name(process) + '_' + self.generate_process_ID()
                else: # (name, process)
                    name=process_details[0]
                    process = process_details[1]
                    runtime_params = None
            elif len(process_details)==3: # (name, process, runtime_params)
                name = process_details[0]
                process = process_details[1]
                runtime_params = process_details[2]
            else:
                raise MyException('Error: Incorrect number of process details given:', len(process_details))
            processes_.append([name, process, runtime_params])
        return processes_

    def add_pipes(self, resource_ID: str, processes: list, runtime_params_dict: dict = None,
                  resource_dict: dict = None, silent=False, delayed=True):

        """
        processes: a list of tuples (process_name, process)
        runtime_params_dict: {process_name:runtime_params_as_dict}}
        """

        if delayed==True:
            self._add_to_instructions(locals(), inspect.stack()[0][3])
            return

        new_nodes_created=[]

        runtime_params_dict = {} if runtime_params_dict is None else copy.deepcopy(runtime_params_dict)
        resource_dict = {} if resource_dict is None else copy.deepcopy(resource_dict)

        task_graph = self.task_graph
        task_ID_to_task = self.task_ID_to_task

        task_prev = None

        for i, (name, process, runtime_params)  in enumerate(self._normalize_process_details(processes)):
            runtime_params = {} if runtime_params is None else copy.deepcopy(runtime_params)
            op_param_keys = [key for key in runtime_params.keys() if 'op_' in key]
            op_params = {k: runtime_params[k] for k in op_param_keys}
            for k in op_param_keys:
                runtime_params.pop(k)
            task_ID = Task.concoct_task_ID(name, resource_ID)
            # check if it is an invocation request for an internal utility function
            run_function = None
            if type(process) == str and (
                    process in self.connector_functions_mapping.keys() or process in self.non_parallel_connector_functions_mapping.keys()):
                process = self.connector_functions_mapping.get(process, process)
                if type(process) == str:
                    process = self.non_parallel_connector_functions_mapping[process]
                runtime_params['task_ID'] = task_ID
            elif type(process) == str and 'plugins.' in process:
                run_function = process.split('.')[-1]
                process = '.'.join(process.split('.')[:-1])

            if task_ID not in task_ID_to_task.keys():
                # merge the runtime params provided during declaration of the pipe and addition of the pipe!
                runtime_params = merge_dict(runtime_params, runtime_params_dict.get(name, {}))
                task = Task(name, process, resource_ID, self.plugin_collection, self.celerydreamer, run_function,
                            runtime_params, op_params)
                task_ID_to_task[task.get_task_ID()] = task
                if not silent:
                    print('Adding Node:', task_ID)
                task_graph.add_node(task_ID, process=process)
                new_nodes_created.append(task_ID)
            else:
                task = task_ID_to_task[task_ID]
            if i != 0:
                self.add_edge(task_prev.get_task_ID(), task.get_task_ID(), silent=silent)

            # add any explicitly provided resources for this task; these will be made available to any downstream tasks
            for resource_name, resource in resource_dict.get(name, {}).items():
                if task_ID not in self.added_resources[task_ID].keys():
                    self.added_resources[task_ID] = {}
                self.added_resources[task_ID][resource_name] = resource

            # add a new Operation object to the task, this will go into the process as a parameter and can be retrieved from the results
            task.objects['new_operation'] = Operation('new_operation')

            task_prev = task
        return {'new_nodes_created': new_nodes_created}

    def add_connection(self, s_resource_ID, s_name, t_resource_ID, t_name, silent=False, delayed=True):
        """
        To connect two tasks which have been already initialized using the function: add_pipes
        """
        if delayed==True:
            self._add_to_instructions(locals(), inspect.stack()[0][3])
            return

        if s_name in self.templates.keys():
            s_name=self.templates[s_name][-1][0]

        if t_name in self.templates.keys():
            t_name=self.templates[t_name][0][0]

        task_ID_A = Task.concoct_task_ID(s_name, s_resource_ID)
        task_ID_B = Task.concoct_task_ID(t_name, t_resource_ID)
        self.add_edge(task_ID_A, task_ID_B, silent=silent)

    def task_prep(self, task_ID):
        # print('\n')
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
        params['plugin_runner'] = self.plugin_collection

        return params

    def run_graph(self, processes=1, silent=False, no_celery=False):

        if len(self.instructions)!=0:
            print('Executing instructions:')
            self.execute_instructions()

        if processes < 1:
            processes = 1

        start = datetime.datetime.now()
        if processes > 1:
            # todo: make sure redis is running
            # start a single Celery worker that can spawn multiple processes
            # self.celerydreamer.start(concurrency=4)
            if no_celery:
                strigified_list="["+",".join(["\""+item+"\"" for item in self.include_plugins])+"]"
                subprocess.Popen(
                    shlex.split(
                        sys.executable + " -c  'from jpl.pipedreams import celeryapp; cd=celeryapp.CeleryDreamer("+strigified_list+",\""+self.redis_path+"\"); cd.start(concurrency="+str(processes)+")'"),
                    stdout=open(os.devnull, 'wb')
                )

        task_graph = self.task_graph
        next = set()
        added = set()
        completed = set()

        # find all nodes with 0 in-degree and add them to the 'next list'
        seed_tasks = [task_ID for task_ID in task_graph.nodes if task_graph.in_degree(task_ID) == 0]
        next.update(seed_tasks)
        task_completed_count = 0
        pbar = tqdm(total=len(task_graph.nodes))
        while (len(next) != 0 or len(added) != 0):

            # sweep the next queue and add tasks to workers or get them done
            to_remove = []
            to_add = []
            for next_task_ID in next:
                # check if all the parents are in the completed queue
                predecessors = task_graph.predecessors(next_task_ID)
                ripe = True
                for predecessor_ID in predecessors:
                    if predecessor_ID not in completed:
                        ripe = False
                # todo: the parallel and non-parallel execution has a lot of code duplication!
                if ripe:
                    next_task = self.task_ID_to_task[next_task_ID]
                    # gather params from parents
                    params = self.task_prep(next_task_ID)
                    if not silent:
                        print("Adding to Run Queue:", next_task_ID)
                        print("   ---> with inherited params (from parent(s) task result(s)):", params)
                        print("   ---> with self params:", next_task.params)
                    self.inherited_params[next_task_ID]=params
                    self.self_params[next_task_ID] = next_task.params
                    if processes == 1 or next_task_ID in self.non_parallel_connector_functions_mapping.keys():
                        time_task_begin=datetime.datetime.now()
                        next_task.run_task(single_process=True, **params)
                        rs = next_task.result
                        next_task.result = rs['result']
                        self.times[next_task_ID] = rs['time_taken']
                        next_task.postprocess_results()
                        if not silent:
                            print("Non-parallel Task Completed:", next_task_ID)
                            print("     ---> result:", next_task.result)
                        self.results[next_task_ID] = next_task.result
                        pbar.update(1)
                        completed.add(next_task_ID)
                        task_completed_count += 1
                        # see if the task had new instructions within
                        new_instructions=rs['new_operation'].instructions
                        self.instructions=new_instructions
                        new_nodes_created=self.execute_instructions()
                        # find which ones have 0 in degree and attach them to the current task_ID
                        for new_node_created in new_nodes_created:
                            if self.task_graph.in_degree(new_node_created)==0:
                                self.add_edge(next_task_ID, new_node_created, silent=silent, delayed=False)
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
            to_remove = []
            for added_task_ID in added:
                added_task = self.task_ID_to_task[added_task_ID]
                if str(added_task.result.state) == 'SUCCESS':
                    task_completed_count += 1
                    rs=added_task.result.get()
                    added_task.result = rs['result']
                    self.times[added_task_ID] =rs['time_taken']
                    added_task.postprocess_results()
                    if not silent:
                        print("Parallel Task Completed:", added_task_ID)
                        print("     ---> result:", added_task.result)
                    self.results[added_task_ID] = added_task.result
                    pbar.update(1)
                    completed.add(added_task_ID)
                    to_remove.append(added_task_ID)
                    # see if the task had new instructions within
                    new_instructions = rs['new_operation'].instructions
                    self.instructions = new_instructions
                    new_nodes_created = self.execute_instructions()
                    # find which ones have 0 in degree and attach them to the current task_ID
                    for new_node_created in new_nodes_created:
                        if self.task_graph.in_degree(new_node_created) == 0:
                            self.add_edge(added_task_ID, new_node_created, silent=silent, delayed=False)
                    # add the children to next
                    for next_task_ID in task_graph.successors(added_task_ID):
                        next.add(next_task_ID)

            for task_ID in to_remove:
                added.remove(task_ID)
        pbar.close()
        # kill celery worker
        if processes > 1:
            if no_celery:
                # self.celerydreamer.stop()
                subprocess.call(shlex.split("pkill -f \"celery\""))

        print('num nodes in task graph:', len(task_graph.nodes))
        print('num task completed:', task_completed_count)
        print('time taken:', datetime.datetime.now() - start)
