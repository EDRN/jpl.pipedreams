from celery import Celery
from .utils.misc_utils import ignore_unmatched_kwargs

def celery_obj_func_runner(obj, func_name, **kwargs):
    result = ignore_unmatched_kwargs(getattr(obj, func_name))(**kwargs)
    return result

def celery_indi_func_runner(func_object, **kwargs):
    result = ignore_unmatched_kwargs(func_object)(**kwargs)
    return result

class CeleryDreamer():

    def __init__(self, plugin_list, redis_url=None):
        if redis_url[-1]!='/':
            redis_url+='/'
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
        self.celery_obj_func_runner = self.app.task(celery_obj_func_runner)
        self.celery_indi_func_runner = self.app.task(celery_indi_func_runner)

    def start(self, concurrency):
        self.worker = self.app.Worker(concurrency=concurrency)
        self.worker.start()

    def stop(self):
        self.worker.stop()

