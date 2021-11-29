# Important tests:
# - Test both formats
# - Lat/long parsing
# - Ownship vs contact
# - Certain vs uncertain positional data
import os
import unittest
from datetime import datetime

from importers.full_shore_importer import FullShoreImporter
from pepys_import.core.store.data_store import DataStore

FILE_PATH = os.path.dirname(__file__)


class FullShoreTests(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

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
