=============
Configuration
=============

Pepys-import can be configured by the use of a configuration file.
A default configuration file is provided in the root of the repository
with the name :code:`default_config.ini`. Rather than editing this directly,
it should be copied to a new location, and the environment variable
:code:`PEPYS_CONFIG_FILE` should be set to the full path to the new
configuration file.

Configuration file format
-------------------------
An example configuration file is shown below:

.. literalinclude:: ../default_config.ini

It consists of a number of sections, specified in square brackets, such as
:code:`[database]` and inside these sections are a number of individual variable
settings specified as :code:`<variable> = <value>`. Unneeded entries can be left
blank and will be filled with a default value.

Configuration file variables
----------------------------

:code:`[database]` section
##########################
These settings control how pepys-import connects to the database. The specific
variables are:

 - :code:`db_username`: Username used to connect to the database server (default: :code:`postgres`). Only used for PostgreSQL connections.
 - :code:`db_password`: Password used to connect to the database server (default: :code:`postgres`). Only used for PostgreSQL connections.
 - :code:`db_host`: Host (name or IP address) on which the database server is running (default: :code:`localhost`). Only used for PostgreSQL connections.
 - :code:`db_port`: Port on which the database server is accepting connections (default: :code:`5432`). Only used for PostgreSQL connections.
 - :code:`db_name`: Name of the database on the server (for PostgreSQL) or name of the database file to be used for SQLite (default: :code:`pepys`). Can be set to :code:`:memory:` for an in-memory SQLite database.
 - :code:`db_type`: Type of database to use: must be set to either :code:`sqlite` or :code:`postgres` (default: :code:`postgres`)

:code:`[archive]` section
##########################

These settings control where Pepys stores the archived input files, alongside the output and error
logs for an input The specific variables are:

 - :code:`user`: Username used to connect to the archiving location. Only used when the :code:`path` is a
   Windows shared folder (default: none).
 - :code:`password`: Password used to connect to the archiving location (default: none). Only used when the :code:`path` is a
   Windows shared folder (default: none).
 - :code:`path`: Full path to folder used to archive input files and store output logs (default: none).
   This should be either a local path to a folder (it will be created if it doesn't exist), or a path to a
   Windows shared network folder (also called a *SMB Share*) on another computer. For the latter, the
   path must start with :code:`\\` and be structured as :code:`\\SERVER\share\path\to\folder`. When running
   on Windows, the :code:`SERVER` part of the path can be specified as either a Windows hostname or an IP
   address. For all other platforms, the :code:`SERVER` part must be specified as an IP address.
   The username and password configured in the other two variables in this section will be used to connect
   to the shared folder.

:code:`[local]` section
##########################

These settings control how pepys-import finds custom locally-installed parsers and validation tests.
The specific variables are:

 - :code:`parsers`: Path to a folder containing custom parsers to be loaded by pepys-import (default: none)
 - :code:`basic_tests`: Path to a folder containing custom basic validation tests to be loaded by pepys-import (default: none)
 - :code:`enhanced_tests`: Path to a folder containing custom enhanced validation tests to be loaded by pepys-import (default: none)
 (default: none)
 