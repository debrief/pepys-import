=============
Configuration
=============

Pepys-import can be configured by the use of a configuration file.
A default configuration file is provided in the root of the repository
with the name :code:`default_config.ini`. Rather than editing this directly,
it should be copied to a new location, and the environment variable
:code:`PEPYS_CONFIG_FILE` should be set to the full path to the new
configuration file. If the configuration file needs to be set differently
on a specific computer, and network configuration (for example, a Group Policy)
forces :code:`PEPYS_CONFIG_FILE` to a specific value, then the :code:`PEPYS_CONFIG_FILE_USER`
variable can be set to the path to the configuration file instead, and this will override
the :code:`PEPYS_CONFIG_FILE` variable.

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

 - :code:`database_username`: Username used to connect to the database server (default: :code:`postgres`). Only used for PostgreSQL connections. Can be encrypted.
 - :code:`database_password`: Password used to connect to the database server (default: :code:`postgres`). Only used for PostgreSQL connections. Can be encrypted.
 - :code:`database_host`: Host (name or IP address) on which the database server is running (default: :code:`localhost`). Only used for PostgreSQL connections.
 - :code:`database_port`: Port on which the database server is accepting connections (default: :code:`5432`). Only used for PostgreSQL connections.
 - :code:`database_name`: Name of the database on the server (for PostgreSQL) or name of the database file to be used for SQLite (default: :code:`pepys`). Can be set to :code:`:memory:` for an in-memory SQLite database.
 - :code:`database_type`: Type of database to use: must be set to either :code:`sqlite` or :code:`postgres` (default: :code:`postgres`)

:code:`[archive]` section
##########################
These settings control how pepys-import archives files after importing them.
The specific variables are:

 - :code:`user`: Username used to connect to the archiving location (default: none). Can be encrypted.
 - :code:`password`: Password used to connect to the archiving location (default: none). Can be encrypted.
 - :code:`path`: Full path to folder used to archive input files and store output logs (default: none)

:code:`[local]` section
##########################
These settings control how pepys-import finds custom locally-installed parsers and validation tests.
The specific variables are:

 - :code:`parsers`: Path to a folder containing custom parsers to be loaded by pepys-import (default: none)
 - :code:`basic_tests`: Path to a folder containing custom basic validation tests to be loaded by pepys-import (default: none)
 - :code:`enhanced_tests`: Path to a folder containing custom enhanced validation tests to be loaded by pepys-import (default: none)

Encryption
##########
Various fields can be specified in an encrypted form (see notes above). To do this,
encrypt the value and add a :code:`_` to the beginning and end of the encrypted string. For
example, :code:`_aghiejf_`. Then use this as the value of the configuration option.