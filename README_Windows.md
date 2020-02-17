# Installation instructions for Windows 10


1. Install Python 3.7 from www.python.org

2. Rename `<installation-path>\DLLs\sqlite3.dll` (eg. `C:\Python37\DLLs\sqlite3.dll`) to `sqlite3OLD.dll`

3. Download the 64-bit sqlite3 DLL from https://www.sqlite.org/download.html

4. Unzip that DLL to a path of your choice (eg. `c:\sqlite3\`)

5. Add that path to your `$PATH` variable (hint: using [Rapid Environment Editor](https://www.rapidee.com/en/about) makes this easy)

6. Download spatialite from http://www.gaia-gis.it/gaia-sins/windows-bin-NEXTGEN-amd64/mod_spatialite-NG-win-amd64.7z

7. Unzip and put the folder `mod_spatialite-NG-win-amd64` somewhere of your choice (eg. `c:\mod_spatialite-NG-win-amd64`)

8. Add that folder to your `$PATH` variable

9. Install PostreSQL by downloading version 12.2 for Windows x86-64 from https://www.enterprisedb.com/downloads/postgres-postgresql-downloads

10. Go through the installation wizard making sure that you choose to load the 'Stack Builder' application when you exit the wizard.

11. Use the StackBuilder application to install PostGIS

12. Clone the [pepys-import](https://github.com/debrief/pepys-import) repository into a folder of your choice

13. Navigate to the folder and run `python -m venv env` to create a virtual environment in a folder called `env`

14. Run `.\env\Scripts\activate.bat` to activate the virtual environment

15. Run `pip install -r requirements.txt`

16. Run `pip install pytest` (TODO: Add pytest to list of dependencies)

17. Run `pip install -e git+https://github.com/tk0miya/testing.postgresql.git#egg=testing.postgresql` to install the development version of `testing.postgresql`


Notes on why we have to do it this way:

 - The sqlite DLL that comes with Python 3.7 doesn't have support for RTrees compiled in, and these are required for using spatialite
 - The current stable version of spatialite isn't compatible with the version of sqlite that Python 3.7 requires. We have to use the 'Next Generation' version - which is very nearly the stable release (and was released in Aug 2018 so has been around for a while!)
 - We're using Python 3.7 as that's what the Navy use on their machines
 - The development version of `testing.postgresql` is required as the latest release doesn't support Windows properly (it tries to send an unsupported OS signal to the postgres server to shut it down, which fails and also leaves all the test postgres servers running which causes utter chaos!)
