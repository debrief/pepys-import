===============
Getting started
===============

This guide will take you through your first steps using Pepys - from first install, through
importing some files, to checking the contents of the database and exporting some files.

1. Download and install Pepys
-----------------------------

Follow the instructions at :doc:`installation` to install Pepys.

2. Run an import using Pepys Import
-----------------------------------

Navigate to the :code:`tests/sample_data/track_files/gpx` folder inside the Pepys install folder.
We're going to be working with a file called :code:`gpx_1_0.gpx`. Right-click thie file and choose
:code:`Open with` and select to open the file with Notepad. You'll see that this is a text file in a
XML format called GPX - a format that is commonly used by the handheld GPS trackers popularised by
cyclists & walkers. The file contains some introductory metadata, followed by 5 position records.
Pepys contains a series of importer modules, one of which can recognise and load :code:`*.gpx` files.

To run the import, right-click on :code:`gpx_1_0.gpx` and in the *Send To* menu choose :code:`Pepys Import
(no archive)`. This will tell Pepys to import this GPX file into the database. (If you don't have
that item in your *Send To* menu, then make sure you ran Step 4 of the :doc:`Installation` instructions.)

A command-line window will open, showing the Pepys welcome banner, followed by a table showing the
status of the Pepys database before the import was run. As this is your first import, the number of
rows in each table will be zero.

You will then get an interactive interface allowing you to define the metadata for the various
'objects' that are being imported. In Pepys, these represent real-world objects such as Platforms (a
vessel such as a ship or submarine), Sensors (some sort of measurement/sensing device on a Platform)
and Datafiles (a file that is being imported into Pepys). All these objects have metadata associated
with them. For example, a Platform has a Nationality and a Platform Type, and all objects have a
Classification for security purposes.

The first question asks you to provide a classification for the datafile. Choose to :code:`Search an
existing classification`, and start typing :code:`Private` and you'll see that an autocompletion
menu pops up. Press Tab to complete what you've typed, and Enter to continue. This will set the
classification of the datafile to `Private`. You will then be given all the information about the
datafile, to allow you to confirm everything is set correctly - just choose option `1` to confirm
and continue.

The next set of questions are about the Platform. You should choose to add a new platform (option
:code:`2`), and then you'll be asked for details. It doesn't matter what name or details you give
it, as this is just an example - but note that some fields are optional. Next is the search for a
nationality (the nationality :code:`UK` is already defined for you), and you can add a new Platform
Type of :code:`Frigate`. Finally, you'll be asked for a classification for the platform - again, you
can just select the existing classification :code:`Private`.

The next stage is entering data about the sensor used to collect the data that we're importing. In
this case, we're importing a GPX file, which is a file format used by GPS systems - so the sensor
name is pre-filled as :code:`GPS`. So, choose to add a new sensor (option :code:`2`), add a
classification and confirm the details are correct.

You've now finished adding metadata, and the import itself will take place and a progress bar will
(very quickly) move up to 100% completed. You will then see a summary of the database status after
the import - it should show 5 States, and 1 Platform are now in the database. This matches our
expectations from the datafile - it had 5 position reports, and they were all about one platform.

3. Check the database status using Pepys Admin
----------------------------------------------

Run *Pepys Admin* from the Start Menu (you can either navigate to the *Pepys* folder and choose
*Pepys Admin* or just search for it and press enter). If you can't find *Pepys Admin* in the Start
Menu, then ensure you ran Step 2 of the :doc:`installation` instructions.

The Pepys Admin command-line window will appear. Note that it shows the welcome banner, and states
which database it is connecting to (this should be the same database that you configured in the
configuration file). Choose option :code:`(2) Status`. Summary tables will be displayed showing the
number of rows of different types in the database: it should show that there are 5 States, plus a
single Sensor, Platform, Datafile and Change, and 15 Changes.

4. Try to import the same file again
------------------------------------

Pepys keeps track of which files have been imported already, so that we don't accidentally import
them multiple times. In this case, there is already an entry in the Datafiles table for the
`gpx_1_0.gpx` file that we just imported, so if we try and import it again we'll just get a message
telling us it has already been imported (note: the date and time given in the message is in UTC, so
may be different to your local time). Try this by doing exactly what you did before: right-click on
:code:`gpx_1_0.gpx` and in the *Send To* menu choose :code:`Pepys Import (no archive)`.

5. Export a data file using Pepys Admin
---------------------------------------

Now choose option :code:`(4) Export by Platform and sensor`. You will need to select a platform -
there is only one, so just press Enter. It will then give you a list of sensors and the periods they
were active. Again there is only one, so just enter :code:`1` and press Enter. Press Enter to accept
the default value for the output filename. You should then see a message saying :code:`Objects
successfully exported to exported_GPX.rep.`. Exit Pepys Admin by choosing option :code:`(0) Exit`.

If you open the file :code:`exported_GPX.rep` in a text editor, you should see contents like the
following (here we chose :code:`NELSON` as the name of the platform):

.. code-block:: none

    120427 162938.000	NELSON	AA	22 11 10.63 N	021 41 52.3702 W	0	8.75	0.0
    120427 163038.000	NELSON	AA	22 17 10.63 N	021 47 52.3702 W	0	10.69	0.0
    120427 163138.000	NELSON	AA	22 29 10.63 N	021 17 52.3702 W	0	14.58	0.0
    120427 163238.000	NELSON	AA	22 11 10.63 N	021 35 52.3702 W	0	18.47	0.0
    120427 163338.000	NELSON	AA	22 23 10.63 N	021 11 52.3702 W	0	6.80	0.0

6. Import a file with errors
----------------------------

First, copy the entire :code:`track_files` folder from :code:`tests\sample_data` in the Pepys
installation folder to a new folder in the root of the pepys installation folder, called
:code:`track_files_test`.

Open the Windows Command Prompt (open the *Start Menu* and type :code:`cmd` and press Enter) and
use the :code:`cd` command to navigate to the Pepys install folder. Then navigate to the :code:`bin`
directory and run :code:`set_paths.bat`. Move back to the main Pepys install folder with :code:`cd ..`,
and run the following:

.. code-block:: none

    python -m pepys_import.cli --path .\track_files_test\rep_data\rep_test1_bad.rep --resolver default --archive

This will run the Pepys Import command, telling it to import the :code:`rep_test1_bad.rep` file with
the default resolver (so it doesn't ask you questions during import) and telling it to archive the file
once it has successfully been processed.

The import process will run, and will produce a summary table at the beginning and end: you will
notice that these show the same statistics, showing that nothing has been imported. This is
expected, because the file we imported has errors in it.

To view these errors, navigate to the :code:`archive` directory in the Pepys install folder. There
will be a series of folders underneath this folder which together define a date - for example
:code:`2020\03\31\15\23\18` for the 31st March 2020 at 15:23:18. Navigate down to the lowest
directory, and you will find two folders :code:`reports` and :code:`sources`. Look in the
:code:`sources` folder: it should be empty. This is because source files are only copied here if the
import has been successful.

Look in the :code:`reports` folder: you should see a file called :code:`rep_test1_bad_errors.log`. If
you open this file in a text editor, you will see contents like:

.. code-block:: none

    [
        {
            "REP Comment Importer - Parsing error on rep_test1_bad.rep": "Error on line 8. Not enough tokens: ;NARRATIVE:     100112 120800"
        },
        {
            "REP Comment Importer - Parsing error on rep_test1_bad.rep": "Error on line 24. Not enough tokens: ;NARRATIVE2: 100112   121200 SEARCH_PLATFORM OBSERVATION"
        }
    ]

The two errors are saying that specific lines of the input file don't have enough tokens for
processing to succeed.

7. Fix the errors and re-import
-------------------------------

To fix the errors in the file, open :code:`track_files_test\rep_data\rep_test1_bad.rep`
in a text editor and delete line 8 entirely, and add some text like :code:`Test observation` to the
end of line 24 (which will be line 23 after you've deleted line 8!).

Try importing the file again, using exactly the same command as before:

.. code-block:: none

    python -m pepys_import.cli --path .\track_files_test\rep_data\rep_test1_bad.rep --resolver default --archive

Now, if you look in the :code:`sources` directory under :code:`archive`, you will find a copy of the
file that was imported - and this file will have been deleted from its original location.

If you look in the :code:`reports` directory, you will find two files:
:code:`rep_test1_bad_output.log` and :code:`rep_test1_bad_highlighted.html`. Open the log file in a
text editor and you should see something like this:

.. code-block:: none

    6 measurements extracted by REP Comment Importer.
    7 measurements extracted by REP Contact Importer.
    8 measurements extracted by REP Importer.

This shows that three different importers have operated on this file, importing different parts of
the file. To see exactly which bits of the file were imported by which importer, open the HTML file
and hover over the highlighted parts.

8. Check the database contents
------------------------------

The Pepys Admin application has the ability to view the raw database tables themselves. To do this,
run Pepys Admin from the Start Menu, and then choose option `6` (View Data), and then option `1`
(View Table). This will give you a list of database tables - start typing `Platform` and then select
it from the list using the arrow keys.

You'll see the contents of the Platforms table displayed: this should include the platform that you
created manually the first time you ran Pepys Import, plus various other platforms added
automatically by the default resolver including `SPLENDID` and `SEARCH_PLATFORM`. You'll see each
platform has a nationality and platform type. In fact, the database stores more information about
platforms (including pennant numbers, trigraphs and more) but for ease of visualisation these are
left out of the database display here.

Now look at some other tables: choose option `1` again and look at the `States` table, in which
you'll see entries for the individual measurements that have been imported. Here we're only showing
a few columns, so you can't see the actual location, speed, bearing and so on, but you can see what
sensor was used and the time of the measurement. Don't worry that this list seems short - it is only
showing a limited number of rows: you can see from the database status output that was displayed
earlier that there are actually many hundreds of rows in the States table.

Similarly, look at the `Changes` table. This shows the reason for various changes to the database -
here you can see various reasons including `Importing reference data` and importing various
filenames. This allows all data in the database to be traced back to the files it came from.

Feel free to investigate the other tables in the database.

9. Clean up
------------

Delete the :code:`track_files_test` and :code:`archive` folders in the root of the Pepys install folder.