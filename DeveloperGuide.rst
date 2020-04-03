===============
Developer Setup
===============

This document provides instructions for setting up pepys-import for development, along with contributers
guidance on code style, testing and so on.

To prepare for running ensure Python 3.6 or later is installed on your system.
You can check your Python 3 version with the following command::

    $ python --version

**Note:** Depending on the set up on your computer, you may need to run ``python3`` or ``python3.7`` rather
than ``python`` in this and all following commands.

If you don't have Python 3.6+ in your system, please download it from `python.org <https://www.python.org/downloads/>`_

Pip is also necessary to install dependencies. If you don't have it in your system, please download it::

    $ sudo apt-get install python3-pip

It is possible to verify pip installation with the following command::

    $ pip --version

**Note:** Depending on the set up on your computer, you may need to run ``pip3`` rather than ``pip`` in
this and all following commands. Alternatively, you can run ``python -m pip``.


Platform-specific Setup
-----------------------

Once Python and pip are installed, follow the relevant instructions below for your platform:



Linux (Ubuntu 18.04 LTS)
^^^^^^^^^^^^^^^^^^^^^^^^

Installing Spatialite
*********************

1. Easy Way
"""""""""""

Open a terminal and run the following command::

    $ sudo apt install spatialite-bin
    $ sudo apt-get install -y libsqlite3-mod-spatialite

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

Install Git
**********************

Run the following command::

    $ sudo apt install git


Mac OS X
^^^^^^^^

**Note:** These instructions are not complete due to not having a bare OS X machine to test on. However,
they should give you some hints as to how to get an OS X machine set up to develop pepys-import.

**TODO - Complete instructions here**


Windows
^^^^^^^

1. Create a ``pepys`` folder, which contains a ``lib`` folder.

2. Download the 64-bit sqlite3 DLL from https://www.sqlite.org/download.html

3. Unzip that DLL to ``lib\sqlite-python``

4. Navigate to the ``<python installation directory>\DLLs`` folder, copy ``_sqlite3.pyd`` to ``lib\sqlite-python``

5. Add the ``lib\sqlite-python`` folder to your `%PYTHONPATH%` environment variable (create the variable if necessary)

6. Download spatialite from http://www.gaia-gis.it/gaia-sins/windows-bin-NEXTGEN-amd64/mod_spatialite-NG-win-amd64.7z

7. Unzip and put the folder ``mod_spatialite-NG-win-amd64`` inside the `lib` folder

8. Add that folder to your ``%PATH%`` variable

9. Install PostreSQL by downloading version 12.2 for Windows x86-64 from https://www.enterprisedb.com/downloads/postgres-postgresql-downloads

10. Go through the installation wizard, accepting the default settings and choosing to load the Stack Builder application after installation

11. Use the StackBuilder application to install PostGIS, and follow the wizard through to the end.


12. Add the Postgres bin directory to the ``%PATH%`` - eg. ``C:\Program Files\PostgreSQL\12\bin\`` - but make
sure it comes *after* the ``mod_spatialite`` folder (hint: using
`Rapid Environment Editor <https://www.rapidee.com/en/about>`_ makes it easy to re-arrange entries in the PATH)

13. Install Git from https://git-scm.com/downloads.

Clone the repository
--------------------

Clone the pepys-import repository into a folder of your choice by running::

    $ git clone git@github.com:debrief/pepys-import.git

Create Python virtual environment and install dependencies
----------------------------------------------------------

Following best practice, a Python virtual environment will be used to run the project.
To create a virtual environment, move to the folder in which you cloned the repository, and run::

    $ python -m venv venv

This will create a virtual environment in a folder called ``venv``.

When environment is created successfully, please run the following commands to activate the environment
and install the Python dependencies::

    $ source venv/bin/activate # Linux and OS X
    $ .\venv\Scripts\activate.bat # Windows
    $ pip install -r requirements.txt
    $ pip install -r requirements_dev.txt

Run the unit tests
------------------

To run the unittests run::

    $ pytest tests/

To run the unittests excluding the tests that require PostgreSQL (for example, if you couldn't install
PostgreSQL earlier)::

    $ pytest tests/ -m "not postgres"

To view the coverage of the test suite, run::

    $ coverage run -m pytest tests/

and then view the report with::

    $ coverage report

Creating a deployable release
=============================

For significant releases, the `pepys-import` version should be incremented,
using:
```
bumpversion patch
```

Note 1: once the version has been incremented, a new entry should be
included in `History.rst`.

Note 2: _currently_ the substitution files on `pepys_import/__init__.py` and `setup.py`,
and will need to be tidied manually.

Pepys-import is deployed by providing a zip file to the client containing everything necessary to run
pepys-import on a Windows 10 computer. For instructions on how to install from a deployable zip file,
see `the user-focused README <https://github.com/debrief/pepys-import/blob/develop/README.rst>`_.

To create a deployable release, follow the instructions below on a Windows 10 machine (this *cannot* be
done from any other sort of computer):

1. Clone a new copy of the `pepys-import repository <https://github.com/debrief/pepys-import/>`_, and make sure
it is at the relevant commit for the version you want to release (we recommend creating a git tag for the commit
you use as the basis for a release). (**Note:** Do not create a deployable release from a previously-cloned
version of the repository that you have developed in - always clone a clean copy, otherwise extraneous files
will be included in the release).

2. Run the ``create_deployment.bat`` file in the root of the cloned repository. This will run the ``create_deployment.ps1``
Powershell script. This script obtains all the required binary dependencies (including a standalone
version of Python) and places them in the correct place in the folder hierarchy, and then zips up the
entire folder, resulting in a file in the root of the cloned repository called ``pepys-import_HASH.zip``,
where ``HASH`` is the git commit hash that the release was created from.

3. Upload the resulting zip file to the Github Releases page.