import os

from pepys_import.file.file_processor import FileProcessor
from pepys_import.core.store.data_store import DataStore
from pepys_import.file.nmea_importer import NMEAImporter
from pepys_import.file.replay_importer import ReplayImporter

FILE_PATH = os.path.abspath(__file__)
DIRECTORY_PATH = os.path.dirname(FILE_PATH)


data_store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
data_store.initialise()

processor = FileProcessor("descending.db")
processor.register_importer(ReplayImporter())
processor.register_importer(NMEAImporter())
processor.process(DIRECTORY_PATH, data_store, True)
