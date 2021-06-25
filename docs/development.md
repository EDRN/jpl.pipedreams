# 👩‍💻 Development

If you're a _user_ of this package, see the README for instructions on using the publishing API.

If you're a _developer of this package_ or wish to contribute to it, then these instructions are for you!


## Requirements

To develop, fix bugs for, enhance, or update the LabCAS Publshing API, you'll need:

- Python 3.7 or later
- A Redis instance—or Docker in order to simplify running one
- Git version 2.30 or later

👉 _Note:_ Redis doesn't seem to be actually required; the `demo.py` pipeline in the source works fine without it. It may be masking an error, but that's what [the issue tracker is for](https://github.com/EDRN/jpl.pipedreams/issues).


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
```

The first command creates the virtual environment in a subdirectory called `venv`. The second command upgrades the `setuptools`, `pip`, and `wheel` packages. And the final command installs the source code into the virtual environment in editable mode, meaning that changes you make to Python and other files in `src` are immediately reflected in the virtual environment.

You can then run `venv/bin/python` and it will have local development-version of LabCAS Publishing API (as well as its dependencies) ready for use.

For example, you can now run the `demo.py` demonstration pipeline:

```console
$ venv/bin/python demo.py
```
