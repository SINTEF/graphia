# Graphia
Webapp for viewing and exploring knowledge graphs.


## Install

### Using uv (preferred)
Create a virtual environment and install Graphia

    uv venv
    uv sync
    uv sync --extra dev  # for developers

Optionally activate the environment to run tools and scripts as with pip

    source .venv/bin/activate
    pytest

Alternatively, run tools or scripts with uv. For example

    uv run pytest


### Using pip
Create a virtual environment

    python -m venv .venv
    source .venv/bin/activate

Install Graphia

    pip install .


## For developers
Developers should install pre-commit such that the code can be checked before
it is committed to GitHub.
That can be done with:

    pip install -e .[pre-commit]
    pre-commit install
