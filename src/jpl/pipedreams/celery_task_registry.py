# encoding: utf-8

'''Celery task registry'''

from .celeryapp import app
from .utils.misc_utils import ignore_unmatched_kwargs


@app.task
def celery_obj_func_runner(obj, func_name, **kwargs):
    result = ignore_unmatched_kwargs(getattr(obj, func_name))(**kwargs)
    return result


@app.task
def celery_indi_func_runner(func_object, **kwargs):
    result = ignore_unmatched_kwargs(func_object)(**kwargs)
    return result
