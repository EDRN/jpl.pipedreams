# 🔬 Pipe Dreams

This is an application programmer interface (API) to support the construction and processing of data pipes for scientific data, primarily for the [Laboratory Catalog and Archive System](https://github.com/EDRN/labcas-backend), but open-ended for other systems.


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

The next step is to create a workflow to define the processing steps to publish the data. As an example, see the `demo.py` which is [available from the GitHub release of this package](https://github.com/EDRN/jpl.pipedreams/releases/).

In summary you need to

1.  Create an `Operation` instance.
2.  Add pipes to the instance.
3.  Run the instance's graph.


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
