# 🔬 Pipe Dreams

### Do you want to:
- Organize your huge pile of loose scripts ?
- Create neat and reusable python pipelines to process your data or run jobs ?
- Have a graph (DAG) based parallelization without too much fuss ?  
Well, you are at the right place. Pipe Dreams is a super duper light application programmer interface (API) to support the construction and processing of data pipes for scientific data. It was built primarily for the [Laboratory Catalog and Archive System](https://github.com/EDRN/labcas-backend), but now open-ended for other systems.

### How do we do it:
- We use Python Dictionaries to encapsulate all your intermediate results/data flowing through the pipeline, so you can not only declare and run a sequence of functions but also wire the individual output variables to some specific input parameters. What's more, you can rename, merge and exercise other fine grain control over your intermediate results.
- We provide a Plugin class that can be subclassed to organize your python functions and then call these using their relative string paths in our framework.
- We use [Celery](https://pypi.org/project/celery/), [Redis](https://redis.io/) and [NetworkX](https://pypi.org/project/networkx/) to parallelize your workflows with minimal setup on the users part.  

## 🚗 Starting Redis

The Pipe Dreams API requires [Redis](https://redis.io/) (although apparently not—try it without, it seems to work) to run. To start Redis, run:

```console
$ docker container run \
    --name labcas-redis \
    --publish 5002:5002 \
    --detach \
    redis:6.2.4-alpine
```

## 💿 Installing Pipe Dreams

Pipe Dreams is an open source, installable Python packge. It requires [Python 3.7](https://www.python.org/) or later. Typically, you'd install it into [Python virtual environment](https://docs.python.org/3/tutorial/venv.html), but you can also put it into a [Conda](https://docs.conda.io/en/latest/) or—if you must—your system's Python.

To use a virtual environment, run:

```console
$ python3 -m venv venv
$ venv/bin/pip install --upgrade setuptools pip wheel
$ venv/bin/pip install jpl.pipedreams
```

Once this is done, you can run `venv/bin/python` as your Python interpreter and it will have the Pipe Dreams API (and all its dependencies) ready for use.


## 👩‍💻 Customizing the Workflow

The next step is to create a workflow to define the processing steps to publish the data. As an example, see the `demo/demo.py` which is [available from the GitHub release of this package](https://github.com/EDRN/jpl.pipedreams/releases/).

In summary you need to

1.  Create an `Operation` instance.
2.  Add pipes (a sequence of named functions) to the instance.
3.  Run the operation in either single or multi process(es).  

## 📗 Publishing the Data

Finally, with Redis running (or not—seems to work in any case) and a custom workflow defined, you can then execute the publication. For example, using the `demo.py` the GitHub release:

```console
$ python3 -m venv venv
$ venv/bin/pip install --upgrade setuptools pip wheel
$ venv/bin/pip install jpl.pipedreams
$ curl -LO https://github.com/EDRN/jpl.pipedreams/releases/download/v1.0.1/demo.py
$ curl -L https://github.com/EDRN/jpl.pipedreams/releases/download/v1.0.1/test-data.tar.gz | tar xzf -
$ venv/bin/python demo.py
Adding Node: hello_world_read|+|mydata0.txt
…
num nodes in task graph: 7
num task completed: 7
time taken: 0:00:00.306140
```

That's it 🥳
