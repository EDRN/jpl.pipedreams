from celery import Celery
from .utils.misc_utils import ignore_unmatched_kwargs
import redis
import datetime

def obj_func_runner(obj, func_name, objects:dict=None, **kwargs):
    if objects is None:
        objects={}
    for object_name, objct in objects.items():
        kwargs[object_name]=objct
    task_begin = datetime.datetime.now()
    result = ignore_unmatched_kwargs(getattr(obj, func_name))(**kwargs)
    time_taken_in_seconds=(datetime.datetime.now()-task_begin).total_seconds()
    to_return= {'result': result, 'time_taken': time_taken_in_seconds}
    for object_name, objct in objects.items():
        to_return[object_name] = kwargs[object_name]
    return to_return

def indi_func_runner(func_object, objects:dict=None, **kwargs):
    if objects is None:
        objects={}
    for object_name, objct in objects.items():
        kwargs[object_name]=objct
    task_begin = datetime.datetime.now()
    result = ignore_unmatched_kwargs(func_object)(**kwargs)
    time_taken_in_seconds=(datetime.datetime.now()-task_begin).total_seconds()
    to_return = {'result': result, 'time_taken': time_taken_in_seconds}
    for object_name, objct in objects.items():
        to_return[object_name] = kwargs[object_name]
    return to_return

class CeleryDreamer():

    def __init__(self, plugin_list, redis_url=None):
        if redis_url[-1]!='/':
            redis_url+='/'
        # flush redis
        r = redis.Redis.from_url(redis_url)
        r.flushdb()
        self.BROKER_URL = redis_url+'0'
        self.BACKEND_URL = redis_url+'1'
        self.app = Celery('proj',
                          broker=self.BROKER_URL,
                          backend=self.BACKEND_URL,
                          include=plugin_list)
        # Optional configuration, see the application user guide.
        self.app.conf.update(
            result_expires=3600,
            serializer='pickle',
            result_serializer='pickle',
            task_serializer='pickle',
            accept_content=['pickle', 'json'],
            result_accept_content=['pickle', 'json']
        )
        self.celery_obj_func_runner = self.app.task(obj_func_runner)
        self.celery_indi_func_runner = self.app.task(indi_func_runner)

    def start(self, concurrency):
        self.app.control.purge()
        self.worker = self.app.Worker(concurrency=concurrency, loglevel="DEBUG")
        self.worker.start()

    def stop(self):
        self.worker.stop()

