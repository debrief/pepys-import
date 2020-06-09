================================
Importing initial reference data
================================

Pepys allows the import of initial data for the reference and metadata tables. In practical terms,
this means that Pepys can be initialised with lists of Platform Types, Nationalities, Platforms, Sensors
and so on, which will significantly reduce the workload of analysts importing datafiles into Pepys. To
import new initial data into the Pepys databases, follow the instructions below. Before starting,
make sure you know the full path to the folder of CSV files to be imported - it will look something like
:code:`c:\path\to\folder`

1. Open the Windows Command prompt by opening the *Start Menu* and searching for *Command Prompt*.

2. Type :code:`pepys_admin.bat --path
   <PATH_TO_CSV_FILES>`, replacing :code:`<PATH_TO_CSV_FILES>` with the full path to the folder
   containing the CSV files. The full command will look like
   :code:`pepys_admin.bat --path c:\path\to\folder`.
   Press *Enter*. This will open the Pepys Admin application.

3. Press :code:`1` followed by *Enter* to select the :code:`Initialise/Clear` option.

4. **WARNING: Only perform this step if you intend to delete all data in the Pepys database.** 
   This step is not necessary if new reference/metadata entries are being added to an existing database,
   it is only required if reference/metadata entries have been *modified* from previous versions imported.
   Press :code:`2` followed by *Enter* to select the :code:`Clear database schema`
   option.

5. You will be back a list of options. Choose option :code:`4`. This will import the
   reference data from the CSV files, and a message will appear saying this has completed and which file
   was used, followed by the menu appearing again.

6. Now choose option :code:`5` to import the metadata. If there are any errors in the CSV files,
   these will be displayed. The entries with errors will not have been imported, so changes
   can be made to these entries and the import run again without needing to clear the database
   by running step 4.

7. Choose option :code:`0` and then option :code:`0` again to exit Pepys Admin.

8. Close the Command Prompt
