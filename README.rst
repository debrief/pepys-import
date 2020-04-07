Pepys-import
=============

Pepys-import is a Python library to be used in the parsing and
collation of data to be used in platform-based spatial analysis.

The library provides tools to help work through text data-files, and then
push data measurements (and supporting metadata) to a databases.

PostgreSQL and SQLite databases are currently supported, with SQLite being
the low-friction option favoured for getting started with Pepys-import, or
for project maintainers.

**Note:** This README file is aimed at *users* of pepys-import - please see the `Developer Guide
<https://github.com/debrief/pepys-import/blob/develop/DeveloperGuide.rst>`_ for information on
getting started as a developer.

Installation
------------
Deployable releases of pepys-import are available on the `Releases
<https://github.com/debrief/pepys-import/releases>`_ page. Download the latest release and follow the
instructions below to install:

1. Extract the contents of the downloaded zip file into a folder of your choice (note, this can be
anywhere, including on a shared network drive). This zip file contains everything that is needed
to run pepys-import - including a standalone installation of Python, all of the Python dependencies,
various required DLLs and the pepys-import code itself.

2. Once for each user who will use pepys-import, run ``create_shortcuts.bat`` in the ``bin`` directory.
This will create shortcuts to the relevant pepys-import batch files (from the ``bin`` directory) and copy
them to the user's *Send To* folder.

Usage
-----
To import datafiles using pepys-import, right-click on an individual datafile or a folder containing datafiles
and choose either *Pepys Import* or *Pepys Import (No archive)* from the *Send To* sub-menu.

*Pepys Import* will simply try importing the file and display any errors, whereas *Pepys Import (No archive)* will
import into a SQLite database called ``pepys.db`` located in the same folder as the imported datafiles.

To run the standalone Python distribution included with pepys-import, run the ``run_python.bat`` file in the
``bin`` directory. This can either be called with no arguments, in which case it will load an interactive
Python interpreter session, or with any arguments that can usually be passed to the Python executable. For
example, ``run_python.bat filename.py`` will run ``filename.py`` in the standalone Python distribution.

Online documentation
--------------------

More details on the structure and API of pepys-import is available in the full documentation: |docs|

.. |docs| image:: https://readthedocs.org/projects/pepys-import/badge/?version=latest
  :target:  https://pepys-import.readthedocs.io/


