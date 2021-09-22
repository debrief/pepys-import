import unittest

from importers.link_16_importer import Link16Importer
from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor

class TestLoadLink16(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_process_link16_v1_data(self):
        processor = FileProcessor(archive=False)
        processor.register_importer(Link16Importer)


    