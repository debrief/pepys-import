import os
import sys
from configparser import ConfigParser

from pepys_import.utils.config_utils import process

config = ConfigParser(allow_no_value=True)
DEFAULT_CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), "default_config.ini")

# Try PEPYS_CONFIG_FILE_USER first, if it exists
CONFIG_FILE_PATH = os.getenv("PEPYS_CONFIG_FILE_USER")
if CONFIG_FILE_PATH is None:
    # If not, fallback to PEPYS_CONFIG_FILE, and then to the default path
    CONFIG_FILE_PATH = os.getenv("PEPYS_CONFIG_FILE", DEFAULT_CONFIG_FILE_PATH)

if not os.path.exists(CONFIG_FILE_PATH):
    print(f"Pepys config file not found at location: '{CONFIG_FILE_PATH}'.")
    sys.exit(1)
elif not os.path.isfile(CONFIG_FILE_PATH):
    print(f"Your environment variable doesn't point to a file: '{CONFIG_FILE_PATH}'.")
    sys.exit(1)

# Read the config file
config.read(CONFIG_FILE_PATH)

if not config.has_section("database"):
    print(f"Couldn't find 'database' section in '{CONFIG_FILE_PATH}'!")
    sys.exit(1)

# Error if database type is not found
if not config.has_option("database", "database_type"):
    # Config file is likely an older version
    print(
        "Config file contains variable names used in legacy versions of Pepys that provided insufficient support for database migration. \n Please contact your system administrator to discuss renaming db_xxx to database_xxx."
    )
    sys.exit(1)

# Fetch database section
DB_USERNAME = config.get("database", "database_username", fallback="")
DB_PASSWORD = config.get("database", "database_password", fallback="")
DB_HOST = config.get("database", "database_host", fallback="")
DB_PORT = config.getint("database", "database_port", fallback=0)
DB_NAME = config.get("database", "database_name")
DB_TYPE = config.get("database", "database_type")

# Process username and password if necessary
if DB_USERNAME.startswith("_") and DB_USERNAME.endswith("_"):
    DB_USERNAME = process(DB_USERNAME[1:-1])
if DB_PASSWORD.startswith("_") and DB_PASSWORD.startswith("_"):
    DB_PASSWORD = process(DB_PASSWORD[1:-1])

# Fetch archive section
# TODO: The following username and password might be necessary when files are tried to be moved to
# the archive path
ARCHIVE_USER = config.get("archive", "user", fallback="")
ARCHIVE_PASSWORD = config.get("archive", "password", fallback="")
ARCHIVE_PATH = config.get("archive", "path", fallback=None)

# Process user and password if necessary
if ARCHIVE_USER.startswith("_") and ARCHIVE_USER.endswith("_"):
    ARCHIVE_USER = process(ARCHIVE_USER[1:-1])
if ARCHIVE_PASSWORD.startswith("_") and ARCHIVE_PASSWORD.endswith("_"):
    ARCHIVE_PASSWORD = process(ARCHIVE_PASSWORD[1:-1])

# Fetch local section
LOCAL_PARSERS = config.get("local", "parsers", fallback="")
LOCAL_BASIC_TESTS = config.get("local", "basic_tests", fallback="")
LOCAL_ENHANCED_TESTS = config.get("local", "enhanced_tests", fallback="")
