# MACOS PATH
# EXTENSION_PATH = "/usr/local/lib/mod_spatialite.dylib"

# Linux PATH
EXTENSION_PATH = "/usr/lib/x86_64-linux-gnu/mod_spatialite.so"


def load_spatialite(connection, connection_record):
    connection.enable_load_extension(True)
    connection.load_extension(EXTENSION_PATH)
