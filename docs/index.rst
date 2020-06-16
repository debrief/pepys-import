.. pepys_import documentation master file, created by
   sphinx-quickstart on Fri Nov  8 20:34:08 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to pepys-import
=======================

Introduction
============

Pepys-import is a Python library to be used in the parsing and
collation of data to be used in platform-based spatial analysis.

The library provides tools to help work through text data-files, and then
push data measurements (and supporting metadata) to a databases.

PostgreSQL and SQLite databases are currently supported, with SQLite being
the low-friction option favoured for getting started with Pepys-import, or
for project maintainers.

To try out Pepys without installing anything, click this button to run the *Getting Started*
guide in an interactive notebook on the Binder platform: |binder|

.. |binder| image:: https://mybinder.org/badge_logo.svg
 :target: https://mybinder.org/v2/gh/debrief/pepys-import/develop?filepath=docs%2FPepys%20Getting%20Started%20-%20Binder.ipynb

For further information, use the links on the left or the full Table of Contents below to read the
full Pepys documentation.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   getting_started
   usage
   configuration
   csv_import
   developer_guide
   deployment
   Source documentation <modules>
   importer_dev_guide
   database_migration
   contributing
   documentation
   history

Indices and tables
==================
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
