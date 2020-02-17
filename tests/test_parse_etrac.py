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
        processor = FileProcessor()

        store = DataStore(
            "postgres", "postgres", "localhost", 5432, "test",
            db_type="postgres", show_welcome=False
        )
        store.initialise()
        store.populate_reference(TEST_DATA_PATH)

        processor.register_importer(ETracParser())

        # check states empty
        with store.session_scope():
            # there must be no states at the beginning
            states = store.session.query(store.db_classes.State).all()
            self.assertEqual(len(states), 0)

            # there must be no platforms at the beginning
            platforms = store.session.query(store.db_classes.Platform).all()
            self.assertEqual(len(platforms), 0)

            # there must be no datafiles at the beginning
            datafiles = store.session.query(store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 0)

        # parse the folder
        processor.process(DATA_PATH, store, False)
        # processor.process("Z:/MacDownloads/reetracdatafiles/db", store, False)

        # check data got created
        with store.session_scope():
            # there must be states after the import
            states = store.session.query(store.db_classes.State).all()
            self.assertEqual(len(states), 44)

            # there must be platforms after the import
            platforms = store.session.query(store.db_classes.Platform).all()
            self.assertEqual(len(platforms), 18)

            # there must be one datafile afterwards
            datafiles = store.session.query(store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 1)

if __name__ == "__main__":
    unittest.main()
