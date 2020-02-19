# Installation instructions for Windows 10
These instructions are to install pepys-import for _development_ on Windows 10 - not for deployment on the client's machines. For those instructions see TODO.

1. Install Python 3.7 from www.python.org

2. Create a `pepys` folder, which contains a `libs` folder.

2. Download the 64-bit sqlite3 DLL from https://www.sqlite.org/download.html

3. Unzip that DLL to `libs\sqlite-python`

4. Navigate to the `<python>\DLLs` folder, copy `_sqlite3.pyd` to `libs\sqlite-python`

5. Add the `libs\sqlite-python` folder to your `%PYTHONPATH%` environment variable (create the variable if necessary)

6. Download spatialite from http://www.gaia-gis.it/gaia-sins/windows-bin-NEXTGEN-amd64/mod_spatialite-NG-win-amd64.7z

7. Unzip and put the folder `mod_spatialite-NG-win-amd64` inside the `libs` folder

8. Add that folder to your `%PATH%` variable

9. Install PostreSQL by downloading version 12.2 for Windows x86-64 from https://www.enterprisedb.com/downloads/postgres-postgresql-downloads

10. Go through the installation wizard making sure that you choose to load the 'Stack Builder' application when you exit the wizard.

11. Use the StackBuilder application to install PostGIS, follow the wizard through to the end.

12. Add the Postgres bin directory to the `%PATH%` - eg. `C:\Program Files\PostgreSQL\12\bin\` - but make sure it comes _after_ the `mod_spatialite` folder (hint: using [Rapid Environment Editor](https://www.rapidee.com/en/about) makes it easy to re-arrange entries in the PATH)

12. Clone the [pepys-import](https://github.com/debrief/pepys-import) repository into a folder _inside_ the `pepys` folder

13. Navigate to the `pepys` folder and run `python -m venv venv` to create a virtual environment in a folder called `venv`

14. Run `.\venv\Scripts\activate.bat` to activate the virtual environment

15. Run `pip install -r requirements.txt`

17. Run `pip install -e git+https://github.com/tk0miya/testing.postgresql.git#egg=testing.postgresql` to install the development version of `testing.postgresql` (**TODO:** this can be removed once another PR updating the requirements files is merged)

18. Everything should be installed now, in that virtual environment. Remember to activate it before doing any work on pepys!

Notes on why we have to do it this way:

 - The sqlite DLL that comes with Python 3.7 doesn't have support for RTrees compiled in, and these are required for using spatialite - so we need to use a new sqlite DLL downloaded directly from the SQLite website. To load this version rather than the version that comes with Python requires changing the `%PYTHONPATH%` variable to ensure this new directory (`pepys\libs\sqlite-python`) is searched first.
 - The current stable version of spatialite isn't compatible with the version of sqlite that Python 3.7 requires. We have to use the 'Next Generation' version - which is very nearly the stable release (and was released in Aug 2018 so has been around for a while!)
 - We're using Python 3.7 as that's what the Navy use on their machines
 - The development version of `testing.postgresql` is required as the latest release doesn't support Windows properly (it tries to send an unsupported OS signal to the postgres server to shut it down, which fails and also leaves all the test postgres servers running which causes utter chaos!)
