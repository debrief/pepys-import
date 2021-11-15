import os
import unittest
from datetime import datetime

import pytest
from pint import UnitRegistry

from importers.wecdis_importer import WecdisImporter
from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor
from tests.utils import check_errors_for_file_contents

FILE_PATH = os.path.dirname(__file__)
DATA_PATH = os.path.join(FILE_PATH, "sample_data/wecdis_files/wecdis_sample.log")
VNM_DATA_PATH = os.path.join(FILE_PATH, "sample_data/wecdis_files/wecdis_vnm.log")
DZA_DATA_PATH = os.path.join(FILE_PATH, "sample_data/wecdis_files/wecdis_dza.log")
CONTACT_DATA_PATH = os.path.join(FILE_PATH, "sample_data/wecdis_files/contact.log")
POSITION_DATA_PATH = os.path.join(FILE_PATH, "sample_data/wecdis_files/position.log")
TMA_NO_BRG_DATA_PATH = os.path.join(FILE_PATH, "sample_data/wecdis_files/tma_no_brg.log")
TMA_DATA_PATH = os.path.join(FILE_PATH, "sample_data/wecdis_files/tma_brg.log")
TMA_MISSING_DATA_PATH = os.path.join(FILE_PATH, "sample_data/wecdis_files/tma_missing.log")


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
                DummyToken.csv_to_tokens("$POSL,DZA,20201201,010230.123,012345678*21"), 1
            )
        assert importer.platform_name is None
        assert importer.timestamp is None

    @staticmethod
    def test_wecdis_parse_vnm_invalid_line():
        importer = WecdisImporter()
        check_errors_for_file_contents(
            "$POSL,VNM\nCHART, VER", "Not enough parts in line", importer
        )
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
        check_errors_for_file_contents(
            "$POSL,DZA,20101030\nCHART, VER", "Not enough parts in line", importer
        )

    @staticmethod
    def test_wecdis_parse_dza_invalid_timestamp():
        importer = WecdisImporter()
        check_errors_for_file_contents(
            "$POSL,DZA,20101035,999999.99,12343*AB\nCHART, VER",
            "Error in timestamp value",
            importer,
        )
        assert importer.platform_name is None
        assert importer.timestamp is None

    def test_wecdis_parse_contact(self):
        processor = FileProcessor(archive=False)
        processor.register_importer(WecdisImporter())

        # check states empty
        with self.store.session_scope():
            # there must be no contacts at the beginning
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
            # there must be contacts after the import
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
            ureg = UnitRegistry()

            assert round(stored_contact[0].soa.to(ureg.knot).magnitude) == 12

    def test_wecdis_parse_position(self):
        processor = FileProcessor(archive=False)
        processor.register_importer(WecdisImporter())

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
        processor.process(POSITION_DATA_PATH, self.store, False)

        # check data got created
        with self.store.session_scope():
            # there must be states after the import
            states = self.store.session.query(self.store.db_classes.State).all()
            self.assertEqual(len(states), 1)

            # there must be platforms after the import
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            self.assertEqual(len(platforms), 1)

            # there must be one datafile afterwards
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 1)

            state = self.store.session.query(self.store.db_classes.State).all()
            assert len(state) == 1
            assert state[0].time == datetime(2021, 11, 1, 1, 2, 30, 123000)
            assert round(state[0].location.latitude, 6) == 12.57613
            assert round(state[0].location.longitude, 6) == -0.514239
            ureg = UnitRegistry()
            assert round(state[0].speed.to(ureg.knot).magnitude, 1) == 2.8
            assert state[0].heading.to(ureg.degree).magnitude == 340

    def test_tma_ignore_sol_max(self):
        processor = FileProcessor(archive=False)
        processor.register_importer(WecdisImporter())

        # check states empty
        with self.store.session_scope():
            # there must be no contacts at the beginning
            contacts = self.store.session.query(self.store.db_classes.Contact).all()
            self.assertEqual(len(contacts), 0)

            # there must be no platforms at the beginning
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            self.assertEqual(len(platforms), 0)

            # there must be no datafiles at the beginning
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 0)

        # parse the folder
        processor.process(TMA_NO_BRG_DATA_PATH, self.store, False)

        # check data got created
        with self.store.session_scope():
            # there must be no contacts after the import
            contacts = self.store.session.query(self.store.db_classes.Contact).all()
            self.assertEqual(len(contacts), 0)

            # there must be no platforms after the import
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            self.assertEqual(len(platforms), 0)

            # there must be datafile afterwards
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 1)

    def test_wecdis_parse_tma(self):
        processor = FileProcessor(archive=False)
        processor.register_importer(WecdisImporter())

        # check states empty
        with self.store.session_scope():
            # there must be no contacts at the beginning
            contacts = self.store.session.query(self.store.db_classes.Contact).all()
            self.assertEqual(len(contacts), 0)

            # there must be no platforms at the beginning
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            self.assertEqual(len(platforms), 0)

            # there must be no datafiles at the beginning
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 0)

        # parse the folder
        processor.process(TMA_DATA_PATH, self.store, False)

        # check data got created
        with self.store.session_scope():
            # there must be no contacts after the import
            contacts = self.store.session.query(self.store.db_classes.Contact).all()
            self.assertEqual(len(contacts), 1)

            # there must be no platforms after the import
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            self.assertEqual(len(platforms), 1)

            # there must be datafile afterwards
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 1)

            stored_contact = self.store.session.query(self.store.db_classes.Contact).all()
            assert len(stored_contact) == 1
            assert stored_contact[0].time == datetime(2019, 11, 19, 1, 2, 34, 122000)
            ureg = UnitRegistry()
            assert round(stored_contact[0].location.latitude, 6) == 1.368723
            assert round(stored_contact[0].location.longitude, 6) == -12.568518
            assert round(stored_contact[0].bearing.to(ureg.degree).magnitude) == 270
            assert stored_contact[0].orientation is None  # No course given

    def test_wecdis_tma_missing_fields(self):
        processor = FileProcessor(archive=False)
        processor.register_importer(WecdisImporter())

        # check states empty
        with self.store.session_scope():
            # there must be no contacts at the beginning
            contacts = self.store.session.query(self.store.db_classes.Contact).all()
            self.assertEqual(len(contacts), 0)

            # there must be no platforms at the beginning
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            self.assertEqual(len(platforms), 0)

            # there must be no datafiles at the beginning
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 0)

        # parse the folder
        processor.process(TMA_MISSING_DATA_PATH, self.store, False)

        # check data got created
        with self.store.session_scope():
            # there must be no contacts after the import
            contacts = self.store.session.query(self.store.db_classes.Contact).all()
            self.assertEqual(len(contacts), 3)

            # there must be no platforms after the import
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            self.assertEqual(len(platforms), 1)

            # there must be datafile afterwards
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 1)

            stored_contacts = (
                self.store.session.query(self.store.db_classes.Contact)
                .order_by(self.store.db_classes.Contact.time)
                .all()
            )
            ureg = UnitRegistry()
            assert len(stored_contacts) == 3
            # The contact with all the info
            assert stored_contacts[0].time == datetime(2019, 11, 19, 1, 2, 34, 122000)
            assert round(stored_contacts[0].location.latitude, 6) == 1.368723
            assert round(stored_contacts[0].location.longitude, 6) == -12.568518
            assert round(stored_contacts[0].bearing.to(ureg.degree).magnitude) == 270
            assert round(stored_contacts[0].orientation.to(ureg.degree).magnitude) == 20
            assert stored_contacts[0].track_number == "BRG - all data"
            # Contact with course, but no location
            assert stored_contacts[1].time == datetime(2020, 11, 1, 1, 2, 34, 543000)
            assert stored_contacts[1].location is None
            assert round(stored_contacts[1].bearing.to(ureg.degree).magnitude) == 190
            assert round(stored_contacts[1].orientation.to(ureg.degree).magnitude) == 255
            assert stored_contacts[1].track_number == "BRG - no location"
            # Contact without course or location
            assert stored_contacts[2].time == datetime(2020, 12, 22, 1, 2, 34, 665000)
            assert stored_contacts[2].location is None
            assert round(stored_contacts[2].bearing.to(ureg.degree).magnitude) == 359
            assert stored_contacts[2].orientation is None
            assert stored_contacts[2].track_number == "BRG - no loc/course"

    def test_wecdis_multi_timestep_sample(self):
        processor = FileProcessor(archive=False)
        processor.register_importer(WecdisImporter())

        # check states empty
        with self.store.session_scope():
            # there must be no states at the beginning
            states = self.store.session.query(self.store.db_classes.State).all()
            self.assertEqual(len(states), 0)
            # there must be no contacts at the beginning
            contacts = self.store.session.query(self.store.db_classes.Contact).all()
            self.assertEqual(len(contacts), 0)

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
            self.assertEqual(len(states), 4)

            # there must be contacts after the import
            contacts = self.store.session.query(self.store.db_classes.Contact).all()
            self.assertEqual(len(contacts), 3)

            # there must be no platforms after the import
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            self.assertEqual(len(platforms), 1)

            # there must be datafile afterwards
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 1)

            stored_states = (
                self.store.session.query(self.store.db_classes.State)
                .order_by(self.store.db_classes.State.time)
                .all()
            )

            assert stored_states[0].time == datetime(2021, 11, 1, 1, 2, 30, 123000)
            assert stored_states[1].time == datetime(2021, 11, 1, 1, 2, 45, 10000)
            assert stored_states[2].time == datetime(2021, 11, 1, 1, 3, 5, 10000)
            assert stored_states[3].time == datetime(2021, 12, 12, 1, 3, 35, 10000)

            stored_contacts = (
                self.store.session.query(self.store.db_classes.Contact)
                .order_by(self.store.db_classes.Contact.time)
                .all()
            )
            ureg = UnitRegistry()
            assert round(stored_contacts[0].location.latitude, 6) == 12.566667
            assert round(stored_contacts[0].location.longitude, 6) == 12.899538
            assert round(stored_contacts[0].bearing.to(ureg.degree).magnitude) == 123
            assert round(stored_contacts[0].soa.to(ureg.knot).magnitude, 1) == 3.2

            assert stored_contacts[1].track_number == "BRG 2"
            assert round(stored_contacts[1].bearing.to(ureg.degree).magnitude) == 190
            assert stored_contacts[1].soa is None

            assert round(stored_contacts[2].bearing.to(ureg.degree).magnitude) == 180
            assert round(stored_contacts[2].soa.to(ureg.knot).magnitude, 1) == 12.5


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
