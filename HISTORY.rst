=======
History
=======


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
