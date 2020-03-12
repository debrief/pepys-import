import os
import unittest

from importers.nmea_importer import NMEAImporter
from pepys_import.file.file_processor import FileProcessor
from pepys_import.core.store.data_store import DataStore

FILE_PATH = os.path.dirname(__file__)
DATA_PATH = os.path.join(FILE_PATH, "sample_data/track_files/NMEA")


class TestLoadNMEA(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_load_NMEA_data(self):
        processor = FileProcessor()
        processor.register_importer(NMEAImporter())

        # check states empty
        with self.store.session_scope():
            # there must be no states at the beginning
            states = self.store.session.query(self.store.db_classes.State).all()
            self.assertEqual(len(states), 0)

            # there must be no platforms at the beginning
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            self.assertEqual(len(platforms), 0)

            # there must be no datafiles at the beginning
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 0)

        # parse the folder
        processor.process(DATA_PATH, self.store, False)

        # check data got created
        with self.store.session_scope():
            # there must be states after the import
            states = self.store.session.query(self.store.db_classes.State).all()
            self.assertEqual(len(states), 11400)

            # there must be platforms after the import
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            self.assertEqual(len(platforms), 1)

            # there must be one datafile afterwards
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 1)


if __name__ == "__main__":
    unittest.main()
