
# encoding: utf-8


from jpl.pipedreams.examples.data_pipe.plugins_ops import PluginCollection
import networkx as nx


class Resource(object):

    def __init__(self, ID: str, **kwargs):
        self.ID = ID
        self.resources = kwargs


class Task(object):

    def __init__(self, name:str, process, resource_ID:str, loading_resources:dict, teardown_resources:dict, runtime_params:dict, plugin_collection:PluginCollection):

        if runtime_params is None:
            runtime_params={}

        is_plugin = False
        if type(process) == str:
            process_name=str(process)
            process = plugin_collection.get_plugin(process)
            process.load_resources(**loading_resources)
            is_plugin=True
        elif hasattr(process, '__call__'):
            process_name = process.__name__
        else:
            pass # todo : throw error
            print('process type not recognized: '+ str(type(process)))
            return

        self.name=name
        self.resource_ID=resource_ID
        self.process=process
        self.process_name=process_name
        self.is_plugin=is_plugin
        self.loading_resources=loading_resources
        self.teardown_resources=teardown_resources
        self.result={}
        self.runtime_params=runtime_params

    @staticmethod
    def concoct_task_ID(name, resource_ID):
        return name + '|+|' + resource_ID

    def get_task_ID(self):
        return Task.concoct_task_ID(self.name, self.resource_ID)

    def run_task(self, **kwargs):
        for k, v in self.runtime_params.items():
            kwargs[k]=v

        if self.is_plugin:
            self.result=self.process.run(**kwargs)
        else:
            self.result=self.process(**kwargs)

        # attach a process metadata about which processes have been applied to the artifact so far
        process_undergone = kwargs.get('processes_undergone', list())
        process_undergone.append(self.process_name)
        self.result['processes_undergone'] = process_undergone

    def run_tear_down(self):
        if self.is_plugin:
            self.process.load_resources(self.teardown_resources)


class Operation(object):

    def __init__(self, name: str):
        self.task_graph=nx.DiGraph()
        self.name = name
        self.task_ID_to_task={}
        self.plugin_collection=PluginCollection()

    def add_pipes(self, resource_ID:str, processes:list, runtime_params_dict:dict):
        """
        processes: a list of tuples (process_name, process)
        runtime_params_dict: {process_name:runtime_params_as_dict}}
        """

        task_graph=self.task_graph
        task_ID_to_task=self.task_ID_to_task

        task_prev=None
        for i, (name, process, loading_resources, teardown_resources) in enumerate(processes):
            task_ID=Task.concoct_task_ID(name, resource_ID)
            if task_ID not in task_ID_to_task.keys():
                task=Task(name, process, resource_ID, loading_resources, teardown_resources, runtime_params_dict.get(name, None), self.plugin_collection)
                task_ID_to_task[task.get_task_ID()] = task
                print('Adding new Node:', task_ID)
                task_graph.add_node(task_ID, process=process)
            else:
                task=task_ID_to_task[task_ID]
            if i!=0:
                print("Adding edge: "+task_prev.get_task_ID()+" --> "+ task.get_task_ID())
                task_graph.add_edge(task_prev.get_task_ID(), task.get_task_ID())
                # check if the above breaks the DAG assumptions
                if not nx.is_directed_acyclic_graph(task_graph):
                    task_graph.remove_edge(task_prev.get_task_ID(), task.get_task_ID())
                    print(task_prev.get_task_ID()+" and "+task.get_task_ID()+" could not be added because it will create a loop!")
            task_prev=task

    def run_pipes(self):
        task_graph=self.task_graph
        task_ID_to_task=self.task_ID_to_task
        for task_ID in nx.topological_sort(task_graph): # todo: do parallelization
            task=task_ID_to_task[task_ID]
            # gather the results from the parent tasks
            params={}
            for parent_task_ID in task_graph.predecessors(task_ID):
                parent_task=task_ID_to_task[parent_task_ID]
                for k, v in parent_task.result.items():
                    params[k]=v
            print("Running:", task_ID)
            task.run_task(**params)
            print("-->result:", task.result)


if __name__ == '__main__':

    # create an operation. Each operation contains a single graph (a DAG) that needs to be declared and materialized before running.
    operation=Operation('my_first_operation')

    # declare a series/pipe of processes (plugins in this case)
    # 🤨 This value for ``base_dir`` seems wrong
    process_series_1 = [("read_json", "plugins.read.json", {"base_dir":"/Users/asitangmishra/PycharmProjects/labcas_publish_api/publish_pipeline/examples/data_pipe"}, {}),
                 ("stringify", "plugins.process_meta.basic", {}, {})]
    resource_id="data/test1.json"
    runtime_params_dict = {"read_json": {"file_path": resource_id}}
    # materialize and add the processes into the graph:
    #   - creates a single task per process
    operation.add_pipes(resource_ID=resource_id, processes=process_series_1, runtime_params_dict = runtime_params_dict)

    # declare another series, as a continuation of the already declared one!
    process_series_2= [("stringify", "plugins.process_meta.basic", {}, {}),
                 ("initify_and_add", "plugins.process_meta.basic_2", {}, {}),
                 ("stringify_again", "plugins.process_meta.basic", {}, {})]
    resource_id="data/test1.json"
    runtime_params_dict = {"read_json": {"file_path": resource_id}}
    # since some of names of the processes are the same and with same 'resource_ID', it will use already materialized tasks!
    operation.add_pipes(resource_ID=resource_id, processes=process_series_2, runtime_params_dict = runtime_params_dict)

    # reuse one of the declared series to materialize inw tasks in the graph using a new resource_ID
    resource_id = "data/test2.json"
    runtime_params_dict = {"read_json": {"file_path": resource_id}}
    operation.add_pipes(resource_ID=resource_id, processes=process_series_1, runtime_params_dict = runtime_params_dict)

    # retrieve and print the task DAG
    print("Task DAG: "+str(operation.task_graph.edges))
    # run the operation
    operation.run_pipes()


"""
If two tasks, say A->B are connected, it means:
    1. A needs to be completed before B starts
    2. A's output will be available for B to use
"""


