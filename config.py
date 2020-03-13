import os

from configparser import ConfigParser

from pepys_import.utils.config_utils import process

config = ConfigParser(allow_no_value=True)
DEFAULT_CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), "default_config.ini")
CONFIG_FILE_PATH = os.getenv("PEPYS_CONFIG_FILE", DEFAULT_CONFIG_FILE_PATH)

if not os.path.exists(CONFIG_FILE_PATH):
    raise Exception(f"No such file: '{CONFIG_FILE_PATH}'.")
elif not os.path.isfile(CONFIG_FILE_PATH):
    raise Exception(
        f"Your environment variable doesn't point to a file: '{CONFIG_FILE_PATH}'."
    )

# Read the config file
config.read(CONFIG_FILE_PATH)

assert config.has_section("database"), "'database' section couldn't find."

# Fetch database section
DB_USERNAME = config.get("database", "db_username", fallback="postgres")
DB_PASSWORD = config.get("database", "db_password", fallback="postgres")
DB_HOST = config.get("database", "db_host", fallback="localhost")
DB_PORT = config.getint("database", "db_port", fallback="5432")
DB_NAME = config.get("database", "db_name", fallback="pepys")

# Process username and password if necessary
if DB_USERNAME.startswith("_") and DB_USERNAME.endswith("_"):
    DB_USERNAME = process(DB_USERNAME[1:-1])
if DB_PASSWORD.startswith("_") and DB_PASSWORD.startswith("_"):
    DB_PASSWORD = process(DB_PASSWORD[1:-1])

# Fetch archive section
ARCHIVE_USER = config.get("archive", "user")
ARCHIVE_PASSWORD = config.get("archive", "password")
ARCHIVE_PATH = config.get("archive", "path")

# Process user and password if necessary
if ARCHIVE_USER.startswith("_") and ARCHIVE_USER.endswith("_"):
    ARCHIVE_USER = process(ARCHIVE_USER[1:-1])
if ARCHIVE_PASSWORD.startswith("_") and ARCHIVE_PASSWORD.endswith("_"):
    ARCHIVE_PASSWORD = process(ARCHIVE_PASSWORD[1:-1])

# Fetch local section
LOCAL_PARSERS = config.get("local", "parsers")
LOCAL_BASIC_TESTS = config.get("local", "basic_tests")
LOCAL_ENHANCED_TESTS = config.get("local", "enhanced_tests")
