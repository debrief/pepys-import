Code coverage
===============

We're aiming for 100% code coverage on the project, track our progress here:

.. image:: https://codecov.io/gh/debrief/pepys-import/branch/develop/graph/badge.svg
    :target: https://codecov.io/gh/debrief/pepys-import/branch/develop

Online documentation
===============

Learn more here

.. image:: https://readthedocs.org/projects/pepys-import/badge/?version=latest
    :target:  https://pepys-import.readthedocs.io/

Code Style
===============
Black is used on the project:

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/python/black

It is suggested to install a pre-commit hook in order to apply Black before pushing commits::

    $ pip install pre-commit
    $ pre-commit install


Jupyter demo
===============

Link to working demo of datafile import:

.. image:: https://mybinder.org/badge_logo.svg
    :target: https://mybinder.org/v2/gh/debrief/pepys-import/develop?filepath=examples%2Fnotebooks%2Fdata_store_sqlite.ipynb

Work in progress
===============

View the project Kanban board `here <https://github.com/debrief/pepys-import/projects/3>`_

Setup
===============

To prepare for running ensure these tools and packages are installed:

* Python 3 - at least Python 3.6.4 or later
* SQL Alchemy 1.3

For Postgres support and unit tests these packages are also required:

* geoalchemy2
* psycopg2
* nose2 (0.9.1)

Dependencies
--------------

Install the python dependencies with: :code:`pip install -r requirements.txt`

(Was: To install packages use :code:`pip install <package>` or :code:`py -3 -m pip install <package>` depending on your installation.)

Unit tests
--------------

* Run the unit test suite with:  :code:`coverage3 run -m unittest discover -v`
* View the unit test coverage with: :code:`coverage report`

Command Line Instructions
--------------

To run from the command line go to the top level directory of the library in your bash shell or terminal program

Run by specifying the program as a module with :code:`-m` and leaving off the .py file extension

The exact executable name for invoking python will depend how you have it installed, but most commonly it's just :code:`python`
  
For example run the Sqlite example using:  
:code:`python -m Experiments.DataStore_sqliteExperiment`

IntelliJ Instructions
--------------

To run from inside IntelliJ open the project  
Mark the :code:`Store` package as source by right clicking on the directory and selecting :code:`Mark Directory as -> Source Root`

Open any python module you want to run in the main editor window, right click anywhere in the editor and choose the :code:`Run` or :code:`Debug` option


