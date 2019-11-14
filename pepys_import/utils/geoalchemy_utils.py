import platform

SYSTEM = platform.system()
if SYSTEM == "Linux":
    EXTENSION_PATH = "/usr/lib/x86_64-linux-gnu/mod_spatialite.so"
elif SYSTEM == "Darwin":  # Darwin is MacOS
    EXTENSION_PATH = "/usr/local/lib/mod_spatialite.dylib"
elif SYSTEM == "Windows":
    # TODO: mod_spatialite path for Windows should be added
    EXTENSION_PATH = None


def load_spatialite(connection, connection_record):
    connection.enable_load_extension(True)
    connection.load_extension(EXTENSION_PATH)
