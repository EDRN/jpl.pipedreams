import glob
import re
import traceback
import os
import functools
import inspect
import json

class MyException(Exception):
    pass

def get_file_ext(filename):
    # TODO: get a better implementation
    return filename.split('.')[-1] if '.' in filename else ''


def camel_case_split(str):
    return ' '.join(re.findall(r'[A-Z](?:[a-z]+|[A-Z]*(?=[A-Z]|$))', str))


def insensitive_glob(pattern):
    def either(c):
        return '[%s%s]' % (c.lower(), c.upper()) if c.isalpha() else c
    return glob.glob(''.join(map(either, pattern)))

def error_catch(func):
    def func_wrapper(*args, **kwargs):
        try:
           return func(*args, **kwargs)

        except Exception as e:
            print({'status': 'error', 'reason':str(e), 'details':traceback.format_exc()})
            return json.dumps({'status': 'error', 'reason':str(e), 'details':traceback.format_exc()})

    func_wrapper.__name__ = func.__name__
    # if you do not give this, it gives an error:
    #   https://stackoverflow.com/questions/17256602/assertionerror-view-function-mapping-is-overwriting-an-existing-endpoint-functi

    return func_wrapper

def collect_dict(dict_a, dict_b):
    """
    collect everything from dict_a and dict_b in this manner:
    dict_a={A:B, C:D}
    dict_b={A:E}

    return {A:[B, E], C:D}
    """

    dict_return={}
    intersect=set(dict_a.keys()).intersection(set(dict_b.keys()))
    for key in intersect:
        if type(dict_a[key])!=list:
            dict_a[key]=[dict_a[key]]
        if type(dict_b[key])!=list:
            dict_b[key]=[dict_b[key]]

        dict_return[key]=list(set(dict_a[key]+dict_b[key])) # merge and deduplicate

    for key in set(dict_a.keys())-intersect:
        dict_return[key]=dict_a[key]

    for key in set(dict_b.keys())-intersect:
        dict_return[key]=dict_b[key]

    return dict_return

def collect_dicts(list_of_dict):

    if type(list_of_dict)!=list:
        list_of_dict=[list_of_dict]

    combined_dict= {}
    for i, dict in enumerate(list_of_dict):
        if i==0:
            combined_dict=dict
            continue
        combined_dict=collect_dict(combined_dict, dict)

    return combined_dict

def merge_dict(dict_a, dict_b):
    """
    _b replaces _b for any duplicate keys
    """
    merged_dict={}
    for k, v in dict_a.items():
        merged_dict[k]=v
    for k, v in dict_b.items():
        merged_dict[k]=v
    return merged_dict

def merge_dicts(list_of_dict):

    if type(list_of_dict)!=list:
        list_of_dict=[list_of_dict]

    merged_dict= {}
    for i, dict in enumerate(list_of_dict):
        if i==0:
            merged_dict=dict
            continue
        merged_dict=merge_dict(merged_dict, dict)

    return merged_dict

def remove_keys(dict_, list_of_keys, **kwargs):
    for k in list_of_keys:
        if k in dict_.keys():
            dict_.pop(k)
    return dict_

def boolit(str):
    if str in ['True', 'true']:
        return True
    else:
        return False

def ignore_unmatched_kwargs(f):

    """
    ref: https://stackoverflow.com/questions/26515595/how-does-one-ignore-unexpected-keyword-arguments-passed-to-a-function
    Make function ignore unmatched kwargs.

    If the function already has the catch all **kwargs, do nothing.
    """
    if any(param.kind == inspect.Parameter.VAR_KEYWORD for param in inspect.signature(f).parameters.values()):
        return f

    #
    @functools.wraps(f)
    def inner(*args, **kwargs):
        # For each keyword arguments recognised by f,
        # take their binding from **kwargs received
        filtered_kwargs = {
            name: kwargs[name]
            for name, param in inspect.signature(f).parameters.items() if (
                                                                                  param.kind is inspect.Parameter.KEYWORD_ONLY or
                                                                                  param.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
                                                                          ) and
                                                                          name in kwargs
        }
        return f(*args, **filtered_kwargs)

    return inner

def nested_set(dic, keys, value):
    if len(keys)==0:
        dic=value
        return dic
    for key in keys[:-1]:
        dic = dic.setdefault(key, {})
    dic[keys[-1]] = value
    return dic


