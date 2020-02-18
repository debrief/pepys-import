Welcome
=======

Pepys-import is a Python library to be used in the parsing and
collation of data to be used in platform based spatial analysis.

The library provides tools to help work through text data-files, and then
push data measurements (and supporting metadata) to a databaes.

PostGres and SQLite databases are currently supported, with SQLite being
the low-friction option favoured for getting started with Pepys-Import, or
for project maintainers.

Here's a working demonstrator of datafile import: |binder|

.. |binder| image:: https://mybinder.org/badge_logo.svg
  :target: https://mybinder.org/v2/gh/debrief/pepys-import/develop?filepath=examples%2Fnotebooks%2Fdata_store_sqlite.ipynb

Online documentation
--------------------

Learn more here: |docs|

.. |docs| image:: https://readthedocs.org/projects/pepys-import/badge/?version=latest
  :target:  https://pepys-import.readthedocs.io/


Development
===========

Code coverage
-------------

We're aiming for 100% code coverage on the project, track our progress
here: |code_cov|

.. |code_cov| image:: https://codecov.io/gh/debrief/pepys-import/branch/develop/graph/badge.svg
   :target: https://codecov.io/gh/debrief/pepys-import/branch/develop

Upstream security
-----------------

We have continuous vulnerability testing on the Open Source libraries
we depend upon for development: |dev_req| and production: |plain_req|

.. |plain_req| image:: https://snyk.io/test/github/debrief/pepys-import/badge.svg?targetFile=requirements.txt
   :target: https://snyk.io/test/github/debrief/pepys-import?targetFile=requirements.txt

.. |dev_req| image:: https://snyk.io/test/github/debrief/pepys-import/badge.svg?targetFile=requirements_dev.txt
   :target: https://snyk.io/test/github/debrief/pepys-import?targetFile=requirements_dev.txt

Code Style
----------
Black is used on the project: |black|

.. |black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
 :target: https://github.com/python/black

It is suggested to install a pre-commit hook in order to apply Black before pushing commits::

    $ pip install pre-commit
    $ pre-commit install


Project Progress
----------------

View the project Kanban board `here <https://github.com/debrief/pepys-import/projects/3>`_

Setup
-----

To prepare for running ensure Python 3.7 or later are installed in your system.
You can check your Python 3 version with the following command::

    $ python3 --version

If you don't have Python 3.7+ in your system, please download it from `python.org <https://www.python.org/downloads/>`_

Pip is also necessary to create virtual environment. If you don't have it in your system, please download it::

    $ sudo apt-get install python3-pip
    $ pip3 install virtualenv

It is possible to verify pip installation with the following command::

    $ pip3 --version

----------
For Ubuntu
----------

Installing Spatialite
*********************
1. Easy Way
"""""""""""

Open a terminal and run the following command::

    $ sudo apt install spatialite-bin

2. Alternative Way (Compiling From Source)
""""""""""""""""""""""""""""""""""""""""""

On Debian-based distributions the following libraries are necessary to run SpatiaLite::

    $ sudo apt install zlib1g-dev libfreexl1
    $ sudo apt-get install sqlite3 libsqlite3-dev
    $ sudo apt-get install -y libsqlite3-mod-spatialite
    $ sudo apt-get install binutils libproj-dev gdal-bin libgeos-dev libxml2-dev

After all libraries are installed, it is necessary to download and run the latest SpatiaLite version::

    $ wget https://www.gaia-gis.it/gaia-sins/libspatialite-sources/libspatialite-X.Y.Z.tar.gz
    $ tar xaf libspatialite-X.Y.Z.tar.gz
    $ cd libspatialite-X.Y.Z
    $ ./configure
    $ make
    $ sudo make install

Installing PostGIS
******************

The best way to install PostGIS is running the codes as follows::

    sudo apt-get install libpq-dev python-dev
    sudo add-apt-repository ppa:ubuntugis/ubuntugis-unstable
    sudo apt-get update
    sudo apt-get install postgis

Cloning the Repository
**********************
Navigate to folder you would like to download the repository and run the following command::

    $ git clone https://github.com/debrief/pepys-import.git

Creating Python Environment
***************************
Virtual Environment might be used to run the project. For creating a proper one,
the following commands must be executed respectively in your project directory (please change X with your Python version)::

    $ virtualenv --python=python3.X venv

**Note:** If you downloaded virtualenv in the current session, virtualenv command won't work,
please try to run it after rebooting your machine.

It is also possible to create a virtual environment with the following code::

    $ python3.X -m virtualenv venv

When environment is created successfully, please run the following commands::

    $ source venv/bin/activate
    $ pip install -r requirements.txt

Unit tests
----------

* In order to run the tests, please install requirements_dev: :code:`pip install -r requirements_dev.txt`
* Run the unit test suite with:  :code:`coverage3 run -m unittest discover -v`
* View the unit test coverage with: :code:`coverage report`

Command Line Instructions
-------------------------

To run from the command line go to the top level directory of the library in
your bash shell or terminal program

Run by specifying the program as a module with :code:`-m` and
leaving off the .py file extension

The exact executable name for invoking python will depend how
you have it installed, but most commonly it's just :code:`python`

For example run the Sqlite example using:
:code:`python -m Experiments.DataStore_sqliteExperiment`

IntelliJ Instructions
---------------------

To run from inside IntelliJ open the project
Mark the :code:`Store` package as source by right clicking on
the directory and selecting :code:`Mark Directory as -> Source Root`

Open any python module you want to run in the main editor
window, right click anywhere in the editor and choose the
:code:`Run` or :code:`Debug` option


