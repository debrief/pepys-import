import os
import unittest

from pepys_import.file.e_trac_parser import ETracParser
from pepys_import.file.file_processor import FileProcessor
from pepys_import.core.store.data_store import DataStore


FILE_PATH = os.path.dirname(__file__)
DATA_PATH = os.path.join(FILE_PATH, "sample_data/track_files/other_data")
TEST_DATA_PATH = os.path.join(FILE_PATH, "sample_data", "csv_files")


class ETracTests(unittest.TestCase):
    def test_process_e_trac_data(self):
        print("started")
        processor = FileProcessor("trac.db")

        store = DataStore(
            "", "", "", 0, ":memory:", db_type="sqlite", show_welcome=False
        )
        store.initialise()
        store.populate_reference(TEST_DATA_PATH)
        store.populate_metadata(TEST_DATA_PATH)
        store.populate_measurement(TEST_DATA_PATH)

        processor.register(ETracParser())

        # now good one
        processor.process(DATA_PATH, store, False)

        # check data got created


if __name__ == "__main__":
    unittest.main()
