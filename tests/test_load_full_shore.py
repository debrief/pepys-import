# Important tests:
# - Test both formats
# - Lat/long parsing
# - Ownship vs contact
# - Certain vs uncertain positional data
# - Skip delete lines
import os
import unittest
from datetime import datetime

from importers.full_shore_importer import FullShoreImporter
from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor

FILE_PATH = os.path.dirname(__file__)
SAMPLE_1_PATH = os.path.join(FILE_PATH, "sample_data/full_shore/full_shore_sample_1.csv")
SAMPLE_2_PATH = os.path.join(FILE_PATH, "sample_data/full_shore/full_shore_sample_2.csv")


class FullShoreTests(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_process_full_shore_v1_data(self):
        processor = FileProcessor(archive=False)
        processor.register_importer(FullShoreImporter())

        # check states empty
        with self.store.session_scope():
            # there must be no states at the beginning
            states = self.store.session.query(self.store.db_classes.State).all()
            assert len(states) == 0

            # there must be no platforms at the beginning
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            assert len(platforms) == 0

            # there must be no datafiles at the beginning
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            assert len(datafiles) == 0

        # parse the data
        processor.process(SAMPLE_1_PATH, self.store, False)

        # check data got created
        with self.store.session_scope():
            # there must be states after the import
            states = self.store.session.query(self.store.db_classes.State).all()
            assert len(states) == 1

            # there must be platforms after the import
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            assert len(platforms) == 1

            # there must be one datafile afterwards
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            assert len(datafiles) == 1

    @staticmethod
    def test_parse_valid_date():
        result = FullShoreImporter.parse_timestamp("29/11/2021", "09:30:01")
        assert result == datetime(2021, 11, 29, 9, 30, 1)

    @staticmethod
    def test_parse_wrong_days_in_month():
        result = FullShoreImporter.parse_timestamp("31/11/2021", "12:34:56")
        assert result is None

    @staticmethod
    def test_parse_wrong_date_format():
        result = FullShoreImporter.parse_timestamp("18-02-1992", "12:56:59")
        assert result is None

    @staticmethod
    def test_parse_wrong_time_format():
        result = FullShoreImporter.parse_timestamp("10/11/2012", "125659")
        assert result is None
