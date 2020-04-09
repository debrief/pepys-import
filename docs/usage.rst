=====
Usage
=====

Pepys-Import
------------

The Pepys-Import command-line interface is used to import data into the pepys database. This can be run
in two ways:

 - **Send To:** On a Windows deployment, the import command is available in the *Send To* menu. Right-click on a folder or 
   file you want to import, and choose either :code:`Pepys Import` to import using the default settings
   or :code:`Pepys Import (no archive)` to import without archiving the imported files.

 - **Manually:** Run :code:`python -m pepys_import.cli <options>` on the command-line, ensuring that the `python`
   executable on your PATH is the one for which pepys-import has been installed.

Command-line options
^^^^^^^^^^^^^^^^^^^^

.. code-block:: none

  usage: cli.py [-h] [--path PATH] [--archive] [--db DB]
                  [--resolver RESOLVER]

  optional arguments:
    -h, --help           show this help message and exit
    --path PATH          The path to import data from (The default value is the
                        directory of the script)
    --archive            Instruction to archive (move) imported files to
                        designated archive folder
    --db DB              SQLite database file to use (overrides config file
                        database settings). Use `:memory:` for temporary in-
                        memory instance
    --resolver RESOLVER  Resolver to use for unknown entities. Valid values:
                        'default' (resolves using static default values),
                        'command-line' (resolves using interactive command-line
                        interface, default option)

Pepys-Admin
-----------
The Pepys-Admin interface allows you to export data from the pepys database, initialise or clear the
database, and get database status. This can be run in two ways:

 - **Start Menu:** On a Windows deployment... **TODO: Not implemented yet**

 - **Manually:** Run :code:`python -m pepys_admin.cli <options>` on the command-line, ensuring that the `python`
   executable on your PATH is the one for which pepys-import has been installed.

.. code-block:: none

  usage: cli.py [-h] [--path PATH] [--db DB]

  Pepys Admin CLI

  optional arguments:
    -h, --help   show this help message and exit
    --path PATH  CSV files path
    --db DB      SQLite database file to use (overrides config file database
                settings). Use `:memory:` for temporary in-memory instance

Windows batch files
-------------------
On a Windows deployment, there are various batch files in the `bin` directory of the pepys-import
installation. Some of these are run by the shortcuts in the *Send To* menu, and others are used
to support these scripts, or for debugging/development purposes.

  - :code:`create_shortcuts.bat` and :code:`create_shortcuts.ps1`: These create shortcuts to run
    pepys-import in the user's *Send To* directory. The :code:`.bat` file runs the underlying
    :code:`.ps1` file with the relevent permissions.
  - :code:`pepys_import.bat`: Runs the import CLI, passing the first argument received to the
    :code:`--path` argument of the CLI script. This is called by the shortcut in the *Send To* folder,
    where the first argument passed is automatically the full path to the file or folder to be sent.
  - :code:`pepys_import_no_archive.bat`: Same as above, but runs without the :code:`--archive` option,
    thus not moving the input files to the archive folder.
  - :code:`set_paths.bat`: Sets up the :code:`%PATH%` environment variable so that Python and the required
    libraries (such as modspatialite) can be found on the system path. This is used by most of the other
    batch files, but can be run on its own in a Windows Command Prompt to create an environment where
    all the pepys-import tools are available.
  - :code:`run_python.bat`: Runs the pepys Python interpreter, passing through any arguments passed to
    the batch file. Can be used as a shortcut to running :code:`set_path.bat` and then calling Python.

For example, you can use the :code:`set_paths.bat` script in the following way:

1. Open a Windows Command Prompt
2. Change to the directory containing the pepys-import installation
3. Run :code:`cd bin` to change to the bin directory
4. Run :code:`set_paths.bat` to set up the relevant paths to Python and its dependencies
5. Run :code:`cd ..` to change back to the main directory

You can now run anything using the pepys-provided Python. For example:

 - :code:`python` will run the Python interpreter with all the pepys-import packages available,
   allowing you to interactively try out parts of the pepys-import code
 - :code:`python -m pytest tests/ -m "not postgres"` will run all of the tests, excluding the PostgreSQL
   tests
 - :code:`python -m pepys_admin.cli <options>` will run the pepys-admin CLI.