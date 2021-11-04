import os
import unittest

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

    def test_wecdis_ownship_track(self):
        pass

    def test_wecdis_contact(self):
        pass

    def test_wecdis_parse_vnm(self):
        importer = WecdisImporter()
        assert importer.platform_name != "NONSUCH"
        importer.handle_vnm(DummyToken.string_to_dummy_tokens("$POS,VNM,NONSUCH*5D"))
        assert importer.platform_name == "NONSUCH"

    def test_wecdis_parse_vnm_only_parses_vnm(self):
        importer = WecdisImporter()
        with pytest.raises(TypeError):
            importer.handle_vnm(DummyToken.string_to_dummy_tokens("$POS,XYZ,NONSUCH*5D"))
        assert importer.platform_name is None

    def test_wecdis_parse_vnm_invalid_line(self):
        importer = WecdisImporter()
        importer.handle_vnm(DummyToken.string_to_dummy_tokens("$POS,VNM"))
        assert importer.platform_name is None
        assert len(importer.errors) > 1


class DummyToken:
    def __init__(self, text):
        self.text = text

    def record(self):
        pass

    @staticmethod
    def string_to_dummy_tokens(string):
        return [DummyToken(text) for text in string.split(",")]
