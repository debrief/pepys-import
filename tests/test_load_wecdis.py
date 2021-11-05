import os
import unittest
from datetime import datetime

import pytest

from importers.wecdis_importer import WecdisImporter
from pepys_import.core.store.data_store import DataStore

FILE_PATH = os.path.dirname(__file__)
DATA_PATH = os.path.join(FILE_PATH, "sample_data/wecdis/wecdis_sample.log")


class TestWecdisImporter(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    @staticmethod
    def test_wecdis_ownship_track():
        pass

    @staticmethod
    def test_wecdis_contact():
        pass

    @staticmethod
    def test_wecdis_parse_vnm():
        importer = WecdisImporter()
        assert importer.platform_name != "NONSUCH"
        importer.handle_vnm(DummyToken.csv_to_tokens("$POSL,VNM,NONSUCH*5D"))
        assert importer.platform_name == "NONSUCH"

    @staticmethod
    def test_wecdis_parse_vnm_only_parses_vnm():
        importer = WecdisImporter()
        with pytest.raises(TypeError):
            importer.handle_vnm(DummyToken.csv_to_tokens("$POSL,XYZ,NONSUCH*5D"))
        with pytest.raises(TypeError):
            importer.handle_vnm(
                DummyToken.csv_to_tokens("$POSL,DZA,20201201,010230.123,012345678*21")
            )
        assert importer.platform_name is None
        assert importer.timestamp is None

    @staticmethod
    def test_wecdis_parse_vnm_invalid_line():
        importer = WecdisImporter()
        # Manually initialise the errors because this is only normally done on load
        importer.errors = list()
        importer.handle_vnm(DummyToken.csv_to_tokens("$POSL,VNM"))
        assert importer.platform_name is None
        assert len(importer.errors) == 1

    @staticmethod
    def test_wecdis_parse_dza():
        importer = WecdisImporter()
        assert importer.timestamp is None
        importer.handle_dza(DummyToken.csv_to_tokens("$POSL,DZA,20201201,010230.123,012345678*21"))
        assert importer.timestamp == datetime(2020, 12, 1, 1, 2, 30, 123000)

    @staticmethod
    def test_wecdis_parse_dza_only_parses_dza():
        importer = WecdisImporter()
        with pytest.raises(TypeError):
            importer.handle_dza(DummyToken.csv_to_tokens("$POSL,XYZ,1234,NONSUCH*5D"))
        assert importer.timestamp is None

    @staticmethod
    def test_wecdis_parse_dza_invalid_line():
        importer = WecdisImporter()
        # Manually initialise the errors because this is only normally done on load
        importer.errors = list()
        importer.handle_dza(DummyToken.csv_to_tokens("$POSL,DZA,20101030"))
        assert importer.platform_name is None
        assert len(importer.errors) == 1

    @staticmethod
    def test_wecdis_parse_dza_invalid_timestamp():
        importer = WecdisImporter()
        # Manually initialise the errors because this is only normally done on load
        importer.errors = list()
        importer.handle_dza(DummyToken.csv_to_tokens("$POSL,DZA,20101035,999999.99,12343*AB"))
        assert importer.platform_name is None
        assert len(importer.errors) == 1


class DummyToken:
    """A dummy token to make testing without real-tokens easier"""

    def __init__(self, text):
        self.text = text
        self.children = []
        self.highlighted_file = None

    def record(self):
        pass

    @staticmethod
    def csv_to_tokens(string):
        """Take a CSV string and split it into tokens"""
        return [DummyToken(text) for text in string.split(",")]
