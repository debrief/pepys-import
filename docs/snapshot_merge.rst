===============================
Exporting and merging snapshots
===============================

Pepys has the ability to export a snapshot of the current state of the database into a SQLite
database file. This is a single file, which can be copied to another computer and used with Pepys
for importing and querying data. If modifications have then been made to this file (for example, by
importing new datafiles or adding new objects such as Platforms and Sensors), the changes can be
merged back in to the original database.

Exporting a snapshot
--------------------

To export a snapshot from Pepys Admin, choose option :code:`(4) Snapshot`, and then choose to export
either reference tables only (option :code:`(1)`) or reference and metadata tables (option
:code:`2`). You will be asked to give a filename to export to, and then asked to choose which
privacy levels to export. You can either choose a single privacy level to export, by selecting an
entry and pressing Enter, or you can export multiple privacy levels by selecting each privacy in
turn and pressing the Tab key, followed by Enter once you have selected all of the relevant entries.

For a reference table export, the snapshot will only contain the contents of the reference tables,
such as lists of Nationalities, Platform Types, Sensor Types and so on. For a reference and metadata
export, the snapshot will also contain data from the Platforms, Sensors and Synonyms tables.

Merging a snapshot
------------------

A snapshot file that has been exported as detailed above can be editied separately to the main
database, and then merged back in. This functionality is available under the :code:`(4) Snapshot`
menu in Pepys Admin, as :code:`(3) Merge databases`. First, you will be asked to select a SQLite
database file to merge back in (you can use Tab to autocomplete folder and file names), and then
asked to confirm the merge.

Merging will examine every entry in the chosen SQLite database, and assess whether it is a new
entry that requires adding, a duplicate entry that may require modifying, or an entry that is
already there. Each of these categories of entries are dealt with separately, and any conflicts
are automatically managed. Full technical details of the merging process are available at
:ref:`Merging API documentation <merge_docs>`.

Example workflow
----------------

1. A Pepys installation is use at an analysis facility, with a Master Postgres database containing
   significant volumes of data.

2. An analyst is to be deployed offsite, and needs to be able to perform analysis of data using Pepys, 
   but without any connection to the Master database.

3. A snapshot is created before the analyst departs, containing reference and metadata from the
   Master database.  Since this snapshot contains the reference & metadata, any new data added
   will be consistent with that in the Master.

4. This snapshot is copied to a laptop for the analyst to taken offsite, and Pepys is configured
   on that laptop to connect to this snapshot database.

5. While offsite, the analysis imports new datafiles to Pepys, and creates new metadata
   and reference entries such as Platforms, Sensors and Platform Types.

6. The analyst returns from the offsite deployment, and uses the merge functionality
   to bring all of the data from their database into the Master database.
