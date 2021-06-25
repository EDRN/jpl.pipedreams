# encoding: utf-8

import subprocess
import shlex

from .celery_task_registry import celery_obj_func_runner, celery_indi_func_runner
from .plugins.Test.testing import Testing
from .data_pipe import Operation
from .plugins.collection_specific.general.general_functions import temp_func

# 🤨 What is this
# sys.path.append('/Users/asitangmishra/PycharmProjects/labcas_publish_api/')

celery_process = subprocess.Popen(shlex.split("celery -A jpl.pipedreams.celeryapp:app worker -l INFO --concurrency=2 -n worker1"))

# from jpl.pipedreams.celeryapp import app
# argv = [
#     '-A jpl.pipedreams.celeryapp:app',
#         'worker',
#         '-l INFO',
#     '--concurrency=2',
#     '-n worker1'
#     ]
# app.worker_main(argv)

t=Testing()
print(t)
res=celery_obj_func_runner.delay(t, 'test', x=1)
print(res.get())

subprocess.call(shlex.split("pkill -f celery"))
subprocess.call(shlex.split("pkill -f python"))
basic_labcas_publishing=Operation('test_operation')
plugin_collection = basic_labcas_publishing.plugin_collection
plugin=plugin_collection.get_plugin('jpl.pipedreams.plugins.Test.testing')
func_name='test'
print(plugin)
res=celery_obj_func_runner.delay(plugin, 'test',  x=1)
print(res.get(timeout=3))

print(plugin.test(x=2))

# # this won't work!
# def temp_func(x):
#     return x+2

res=celery_indi_func_runner.delay(temp_func,  x=1)
print(res.get(timeout=3))

# add many functions

import datetime

start=datetime.datetime.now()
task_ids_to_tasks={}
for i in range(100):
    t=Testing()
    res=celery_obj_func_runner.delay(t, 'test_wait', x=i)
    task_ids_to_tasks[res.id]=res

while len(task_ids_to_tasks)!=0:
    to_remove=[]
    for task_id, res in task_ids_to_tasks.items():
        if res.status=='SUCCESS':
            print(res.get())
            to_remove.append(task_id)
    for task_id in to_remove:
        task_ids_to_tasks.pop(task_id)

print('time taken:', datetime.datetime.now()-start)