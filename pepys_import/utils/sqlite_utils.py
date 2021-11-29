import os
import platform

SYSTEM = platform.system()
if SYSTEM == "Linux":
    PLATFORM_EXTENSION_PATH = "mod_spatialite"
elif SYSTEM == "Darwin":  # Darwin is MacOS  pragma: no cover (tests only run on Linux)
    PLATFORM_EXTENSION_PATH = "mod_spatialite"
elif SYSTEM == "Windows":  # pragma: no cover (tests only run on Linux)
    PLATFORM_EXTENSION_PATH = "mod_spatialite"


def load_spatialite(connection, connection_record):
    """
    Loads the spatialite library into the SQLite database

    Tries to load the library located in the PEPYS_SPATIALITE_PATH environment variable first
    and otherwise falls back to the platform-specific paths defined in this file
    """
    connection.enable_load_extension(True)

    environment_path = os.environ.get("PEPYS_SPATIALITE_PATH")

    if environment_path:
        connection.load_extension(environment_path)
    else:
        connection.load_extension(PLATFORM_EXTENSION_PATH)


def set_sqlite_foreign_keys_on(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
