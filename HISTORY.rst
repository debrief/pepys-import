=======
History
=======


0.0.33 (2021-11-29)
-------------------

* Support for Unknown Platforms in bulk import
* Add validation in Tasks UI for start time before end time
* Show warning if database requires migration
* Introduce updated platform icons in timeline
* Allow filtered export of measurement data


0.0.31 (2021-10-12)
-------------------

* Fix for Link16 importer handling unexpected binary content in CSV

0.0.30 (2021-10-05)
-------------------

* Incorporate Link16 importer
* Include some performance upgrades, esp for Pepys-Admin

0.0.29 (2021-09-29)
-------------------

* Record extractions to database for future data audit
* Performance improvement in generating table summaries
* Performance improvement in opening some tables in Maintenance GUI

0.0.28 (2021-09-24)
-------------------

* Minor fixes for timeline (-100%, include_in_timeline, default_interval)
* Fix error for viewing Platform Entry in GUI
* Improve speed of generating table summaries (affects import performance)

0.0.27 (2021-09-16)
-------------------

* Formally release first version of TimeLine (Dashboard)
* Introduce `Export to CSV` in Maintenance pages
* Make database migration more robust, including logging
* New importer for Aircraft CSV data
* Assorted bug-fixes

0.0.26 (2021-08-16)
-------------------

* Formally release Pepys maintenance tools (verified in SW/21)
* Formally release support for tasks & participations (verified in SW/21)
* Incorporate current beta of Pepys-Timeline
* Include version & buid-date when logging imports

0.0.25 (2021-01-15)
-------------------

* Don't check ability to write to Archive folder if in (No archive) mode
* Introduce ability to view config file contents in Pepys-Admin
* Reduce instances where NISIDA import used (files ending in .txt, beginning with UNIT)
* Add support for highlighting XML files

0.0.24 (2020-12-10)
-------------------

* Don't allow users to create new entries in Reference tables
* Add "training" mode, using private Pepys database
* Use bold/colored text in application
* Add "viewer" mode/app for Pepys-Admin for read-only interactions
* Add context-sensitive help for all prompts
* Copy tutorial content to user's Home folder on installation
* Lots and lots of minor usability improvements

0.0.23 (2020-09-23)
-------------------

* Make UI more responsive for very large imports (10s of Mb)

0.0.22 (2020-09-15)
-------------------

* New URL for Spatialite sources

0.0.21 (2020-09-14)
-------------------

* Sort tables in alpha order when selecting to view
* Increase number of records shown in view table (500)
* Add ability to export database table to CSV
* Allow enhanced validator to be relaxed

0.0.20 (2020-07-28)
-------------------

* Allow local override of Pepys config file
* Improve importer writing guide
* Associate SQLite database files with Pepys Admin (right-click editing)
* Make highlight colors more distinctive
* Fix to allow prompts to better handle spaces
* Fix issues with EAG importer
* Check that deployed database is at same version as master when merging

0.0.19 (2020-07-03)
-------------------

* Hotfix for trailing field in Nisida file
* Improve robustness of Import CSV
* Support CSV load of GeometrySubTypes
* Show path for archive folder location at end of import

0.0.18 (2020-07-01)
-------------------

* Add support for Nisida file format
* Add guidance for exporting and merging snapshots
* Add steps to verify installation
* Consistent use of "." to exit Pepys-Admin

0.0.17 (2020-06-16)
-------------------

* Improve display of database version (diagnostics)
* Multi-column unique constraints
* Pause when Pepys-Admin closes (diagnostics)
* Connect to database immediately when Pepys-Admin opens (diagnostics)
* Introduce ability to merge snapshots back in
* Add importer for EAG data
* Double-check with user before destructive admin changes

0.0.16 (2020-06-09)
-------------------

* Improve database migration error handling (hotfix) 

0.0.15 (2020-06-09)
-------------------

* Add ordering for Privacy levels
* Import synonyms from CSV
* Force user to enter name & identifier for platform

0.0.14 (2020-06-05)
-------------------

* Reorganise top level of Pepys Admin
* Distribute docs in deployment, make available from Pepys Admin
* Add progress bar when loading large files

0.0.13 (2020-05-28)
-------------------

* Offer default vaues in Command Line Resolver
* Export snapshot of database to SQLite

0.0.11 (2020-05-20)
-------------------

* Use caching to improve import performance
* Use database migration to allow updates to "live" databases
* Add ability to view database contents from Admin interface

0.0.9 (2020-04-04)
------------------

* Introduce getting started tutorial
* Export datafiles by platform and sensor
* Progress bar when importing data
* Don't try to load a duplicate file
* Enable/disable move (archive) of parsed files
* Parse REPLAY sensor data
* Log import process
* Force use of quantities (value plus units) in importers
* Introduce data validation tests 

0.0.7 (2020-03-10)
------------------

* Support spaces in import path
* Integrate Extraction Highlighter
* Don't create new platform for every line of NMEA
* Introduce Replay comment parser

0.0.6 (2020-03-03)
------------------

* Fix for loading folder twice
* Incorporate all current parsers

0.0.5 (2020-03-02)
------------------

* Include GPS & E-Trac
* Introduce elevation field
* Run automated tests for QA of data before committing to database
* Include deployment scripts

0.0.4 (2020-02-15)
------------------

* Refactor datastore code to match design API

0.0.3 (2019-11-12)
------------------

* Now looping through files in folder, processed using multiple parsers

0.0.2 (2019-11-09)
------------------

* Resolve packaging issues for PyPI

0.0.1 (2019-11-06)
------------------

* First release on PyPI.
