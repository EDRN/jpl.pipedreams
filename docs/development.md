# 👩‍💻 Development

If you're a _user_ of this package, see the README for instructions on using the pipe dreams API.

If you're a _developer of this package_ or wish to contribute to it, then these instructions are for you!


## Requirements

To develop, fix bugs for, enhance, or update the LabCAS Publshing API, you'll need:

- Python 3.7 or later
- A Redis instance—or Docker in order to simplify running one
- Git version 2.30 or later

👉 _Note:_ Redis is required for parallel pipe processing; if you keep `process=1` when you `run_graph` don't worry about it.


## Setting Up the Development Environment

Clone the source code from GitHub using a terminal or command prompt as follows:

```console
$ git clone https://github.com/EDRN/jpl.pipedreams.git
$ cd jpl.pipedreams
```

(You can choose to use the `ssh` protocol or the GitHub CLI if you prefer.)

Once inside the `jpl.pipedreams` source directory, create a Python virtual environment. It's always best to do Python work in a virtual environment since it shelters your system or other Python installations from conflicting packages and conflicting version requirements. Do the following:


```console
$ python3 -m venv venv
$ venv/bin/pip install --upgrade setuptools pip wheel
$ venv/bin/pip install --editable .
$ source venv/bin/activate  # or activate.csh or activate.fish as needed
```

The first command creates the virtual environment in a subdirectory called `venv`. The second command upgrades the `setuptools`, `pip`, and `wheel` packages. And the final command installs the source code into the virtual environment in editable mode, meaning that changes you make to Python and other files in `src` are immediately reflected in the virtual environment. The last command "activates" the virtual environment, essentially putting its programs ahead of others in your execution path. This is deprecated, but needed for now to ensure `celery` is on your `PATH`.

You can then run `venv/bin/python` and it will have local development-version of LabCAS Publishing API (as well as its dependencies) ready for use.


## Running the Demo from Development

The `demo` directory contains an example workflow `demo.py` and test data. To run it from the development environment, follows the steps above to set up the environment. Then, start Redis (see the README). Finally, do:

```console
$ cd demo
$ ../venv/bin/pip install --requirement requirements.txt
$ ../venv/bin/python demo.py
```
