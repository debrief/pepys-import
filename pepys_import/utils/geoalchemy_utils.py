import os
import platform

SYSTEM = platform.system()
if SYSTEM == "Linux":
    PLATFORM_EXTENSION_PATH = "/usr/lib/x86_64-linux-gnu/mod_spatialite.so"
elif SYSTEM == "Darwin":  # Darwin is MacOS
    PLATFORM_EXTENSION_PATH = "/usr/local/lib/mod_spatialite.dylib"
elif SYSTEM == "Windows":
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
