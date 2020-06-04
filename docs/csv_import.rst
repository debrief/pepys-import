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

2. Type :code:`pepys_admin.bat` and press *Enter*. This will open the Pepys Admin application

3. Press :code:`1` followed by *Enter* to select the :code:`Initialise/Clear` option.

4. **WARNING: Only perform this step if you intend to delete all data in the Pepys database.** 
   This step is not necessary if new reference/metadata entries are being added to an existing database.
   Press :code:`2` followed by *Enter* to select the :code:`Clear database schema`
   option.

5. Press :code:`0` followed by *Enter*, and then :code:`0` followed by *Enter* again to exit Pepys Admin.

6. You will now be back at an empty command prompt. Type :code:`pepys_admin.bat --path
   <PATH_TO_CSV_FILES>`, replacing :code:`<PATH_TO_CSV_FILES>` with the full path to the folder
   containing the CSV files. The full command will look like :code:`pepys_admin.bat --path c:\path\to\folder`.
   Press *Enter*.

7. Choose option :code:`1`, then option :code:`4`. This will import the reference data, and a message
   will appear saying this has completed, followed by the menu appearing again.

8. Now choose option :code:`5` to import the metadata.

9. Choose option :code:`0` and then option :code:`0` again to exit Pepys Admin.

10. Close the Command Prompt
