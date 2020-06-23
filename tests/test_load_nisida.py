import datetime
import os
import unittest

from importers.nisida_importer import NisidaImporter
from pepys_import.core.formats import unit_registry
from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor

FILE_PATH = os.path.dirname(__file__)
DATA_PATH = os.path.join(FILE_PATH, "sample_data/track_files/nisida/nisida_split_narrative.txt")


class TestLoadNisida(unittest.TestCase):
    def setUp(self):
        if os.path.exists("nisida.sqlite"):
            os.remove("nisida.sqlite")
        self.store = DataStore("", "", "", 0, "nisida.sqlite", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_process_nisida_data(self):
        processor = FileProcessor(archive=False)
        processor.register_importer(NisidaImporter())

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

        # parse the file
        processor.process(DATA_PATH, self.store, False)

        # check data got created
        with self.store.session_scope():
            pass
            # # there must be 4 states after the import
            # states = self.store.session.query(self.store.db_classes.State).all()
            # self.assertEqual(len(states), 4)

            # # there must be 1 platform after the import
            # platforms = self.store.session.query(self.store.db_classes.Platform).all()
            # self.assertEqual(len(platforms), 1)

            # # there must be one datafile afterwards
            # datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            # self.assertEqual(len(datafiles), 1)

            # # Get all the States entries
            # states = self.store.session.query(self.store.db_classes.State).all()

            # assert round(states[0].location.longitude, 2) == -1.4
            # assert round(states[0].location.latitude, 2) == 51
            # assert round(states[0].elevation, 0) == 1500 * unit_registry.metre
            # assert states[0].heading == 98.2 * unit_registry.degrees

            # assert states[0].time == datetime.datetime(2020, 3, 5, 10, 15, 7)

            # assert round(states[3].location.longitude, 2) == -1.3
            # assert round(states[3].location.latitude, 2) == 52
            # assert states[3].heading == 156.8 * unit_registry.degrees
            # assert states[3].time == datetime.datetime(2020, 3, 5, 10, 15, 27)


if __name__ == "__main__":
    unittest.main()
