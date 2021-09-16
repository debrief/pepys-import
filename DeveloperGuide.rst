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

    $ git clone https://github.com/debrief/pepys-import.git

(If preferred, you can clone using SSH by running ``git clone git@github.com:debrief/pepys-import.git``).

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

Alembic, which is used for Database migration, is in the requirements of the project. However, there is one post-installation step to run it without any problem.
You should install the pepys-import project in an editable mode. Please run the following command in the root of the cloned repository:

.. code-block:: bash

    $ pip install -e .

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

Pull request process
--------------------

Development is conducted using `Feature Branches <https://www.atlassian.com/git/tutorials/comparing-workflows/feature-branch-workflow>`_

Essentially each new piece of work (whether it be a fix or a new feature) is developed in its own branch.

Here is the flow:

1. unless you have a very good reason (minor cosmetic documentation update), the process starts with an issue.  Create the issue, if necessary, documenting the problem that is being solved, and the strategy for solving it

2. open your git client (command-line or graphical, the GitHub client integrates very well)

3. switch to the **develop** branch

4. **Pull** to update the **develop** branch

5. create a new branch, including the issue number and brief description in the title, eg: *433_solitaire_feature*

6. checkout the new branch

7. use commits as necessary to break down the workflow

8. once you're confident in your progress **Push** the branch to the repo (so we can create a draft/tracking PR)

9. in GitHub, switch to **Pull Requests**. You should see a yellow banner with the title of your branch

10. Click on the link in the yellow banner, to create a Pull Request (PR)

11. Give the PR a nice neat title

12. Mark the PR as **Draft**

13. In the PR description, if this PR will resolve the issue, start with **Fixes #433**.  If it won't resolve it, but will help it, write **Supports #433**

14. Continue with branch, pushing commits as necessary.  If you want early feedback, just ask for support via a PR URL in the team Slack channel

15. Once you're happy the PR is complete, and have completed the PR checklist, mark it as **Ready for review**, and add one or more reviewers

16. Reviewers provide feedback as comments on the PR **Conversation** tab, or alongside code in the **Files changed** tab.

17. Ultimately a project admin will **Merge** the code

Other tips:

1. try to avoid large-scale reformatting within a PR, since it obfuscates the logic changes. So, please do large scale reformatting in its own PR, for separate review.

2. don't forget to regularly click on **Update branch** to ensure your code is up to date with **develop**

3. these other things help with PR reviews:
   1. if the change is graphical a screenshot is useful
   2. if something dynamic is happening, a video recording helps (maybe via an app like Gyazo Pro)

GitHub Codespaces
-----------------

The following tips/steps allow use of GitHub codespaces for Pepys dev.

CodeSpaces aren't universally available, though @IanMayo has them available by registering for the Beta Program.

1. In GitHub (GH) select the branch (or create a new one)
2. In the ``Code`` drop-down select ``New CodeSpace``
3. The CodeSpace will open, and ``pip install`` will run, to load the dependencies
4. Run this code to check an import works: ``python -m pepys_import.cli --path tests/sample_data/track_files/rep_data/ --db test.db --resolver default``
4. Run this code to check things are installed: ``pytest tests/test_data_store_api_spatialite.py``