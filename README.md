# Graphia
Webapp for viewing and exploring knowledge graphs.


## Install
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


## Run the web application
Make sure to install the components needed for the webapp `pip install -e ".[webapp]"` and run it from the `webapp` folder using `panel serve app.py`