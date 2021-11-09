import os
import unittest
from datetime import datetime

import pytest

from importers.wecdis_importer import WecdisImporter
from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor
from tests.utils import check_errors_for_file_contents

FILE_PATH = os.path.dirname(__file__)
DATA_PATH = os.path.join(FILE_PATH, "sample_data/wecdis_files/wecdis_sample.log")
VNM_DATA_PATH = os.path.join(FILE_PATH, "sample_data/wecdis_files/wecdis_vnm.log")
DZA_DATA_PATH = os.path.join(FILE_PATH, "sample_data/wecdis_files/wecdis_dza.log")
CONTACT_DATA_PATH = os.path.join(FILE_PATH, "sample_data/wecdis_files/contact.log")


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

    def test_wecdis_parse_vnm(self):
        importer = WecdisImporter()
        processor = FileProcessor(archive=False)
        processor.register_importer(importer)
        assert importer.platform_name != "NONSUCH"
        processor.process(VNM_DATA_PATH, self.store, False)
        assert importer.platform_name == "NONSUCH"

    @staticmethod
    def test_wecdis_parse_vnm_only_parses_vnm():
        importer = WecdisImporter()
        with pytest.raises(TypeError):
            importer.handle_vnm(DummyToken.csv_to_tokens("$POSL,XYZ,NONSUCH*5D"), 1)
        with pytest.raises(TypeError):
            importer.handle_vnm(
                DummyToken.csv_to_tokens("$POSL,DZA,20201201,010230.123,012345678*21")
            )
        assert importer.platform_name is None
        assert importer.timestamp is None

    @staticmethod
    def test_wecdis_parse_vnm_invalid_line():
        importer = WecdisImporter()
        check_errors_for_file_contents("$POSL,VNM", "Not enough parts in line", importer)
        assert importer.platform_name is None

    def test_wecdis_parse_dza(self):
        importer = WecdisImporter()
        processor = FileProcessor(archive=False)
        processor.register_importer(importer)

        assert importer.timestamp is None
        # parse the file
        processor.process(DZA_DATA_PATH, self.store, False)
        assert importer.timestamp == datetime(2020, 12, 1, 1, 2, 30, 123000)

    @staticmethod
    def test_wecdis_parse_dza_only_parses_dza():
        importer = WecdisImporter()
        with pytest.raises(TypeError):
            importer.handle_dza(DummyToken.csv_to_tokens("$POSL,XYZ,1234,NONSUCH*5D"), 1)
        assert importer.timestamp is None

    @staticmethod
    def test_wecdis_parse_dza_invalid_line():
        importer = WecdisImporter()
        check_errors_for_file_contents("$POSL,DZA,20101030", "Not enough parts in line", importer)

    @staticmethod
    def test_wecdis_parse_dza_invalid_timestamp():
        importer = WecdisImporter()
        check_errors_for_file_contents(
            "$POSL,DZA,20101035,999999.99,12343*AB", "Error in timestamp value", importer
        )
        assert importer.platform_name is None
        assert importer.timestamp is None

    def test_wecdis_parse_contact(self):
        processor = FileProcessor(archive=False)
        processor.register_importer(WecdisImporter())

        # check states empty
        with self.store.session_scope():
            # there must be no states at the beginning
            contacts = self.store.session.query(self.store.db_classes.Contact).all()
            self.assertEqual(len(contacts), 0)

            # there must be no platforms at the beginning
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            self.assertEqual(len(platforms), 0)

            # there must be no datafiles at the beginning
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 0)

        # parse the folder
        processor.process(CONTACT_DATA_PATH, self.store, False)

        # check data got created
        with self.store.session_scope():
            # there must be states after the import
            contacts = self.store.session.query(self.store.db_classes.Contact).all()
            self.assertEqual(len(contacts), 1)

            # there must be platforms after the import
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            self.assertEqual(len(platforms), 1)

            # there must be one datafile afterwards
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 1)

            stored_contact = self.store.session.query(self.store.db_classes.Contact).all()
            assert len(stored_contact) == 1
            assert stored_contact[0].time == datetime(2020, 11, 1, 12, 34, 5, 678000)
            assert stored_contact[0].speed == 12


# Contact tests TODO - contact before position info, missing data


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
