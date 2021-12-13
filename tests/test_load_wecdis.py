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
INVALID_LAT_DATA_PATH = os.path.join(FILE_PATH, "sample_data/wecdis_files/invalid_lat.log")
INVALID_LON_DATA_PATH = os.path.join(FILE_PATH, "sample_data/wecdis_files/invalid_lon.log")
DEPTH_DATA_PATH = os.path.join(FILE_PATH, "sample_data/wecdis_files/depth.log")
# INVALID_TTM_PATH = os.path.join(FILE_PATH, "sample_data/wecdis_files/ttm_invalid.log")
DATA_MULTI_POS_HDG_VEL_SOURCES_PATH = os.path.join(
    FILE_PATH, "sample_data/wecdis_files/multiple_pos_hdg_vel_sources.log"
)


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
            "$POSL,VNM\n$POSL,CHART,VER", "Not enough parts in line", importer
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
            importer.handle_timestamp(DummyToken.csv_to_tokens("$POSL,XYZ,1234,NONSUCH*5D"), 1)
        assert importer.timestamp is None

    @staticmethod
    def test_wecdis_parse_dza_invalid_line():
        importer = WecdisImporter()
        check_errors_for_file_contents(
            "$POSL,DZA,20101030\n$POSL,CHART,VER,", "Not enough parts in line", importer
        )

    @staticmethod
    def test_wecdis_parse_depth_invalid_value():
        importer = WecdisImporter()
        check_errors_for_file_contents(
            "$POSL,PDS,U,M\n$POSL,CHART,", "Couldn't convert to a number", importer
        )

    @staticmethod
    def test_wecdis_parse_dza_invalid_timestamp():
        importer = WecdisImporter()
        check_errors_for_file_contents(
            "$POSL,DZA,20101035,999999.99,12343*AB\n$POSL,VER,",
            "Error in timestamp value",
            importer,
        )
        assert importer.platform_name is None
        assert importer.timestamp is None

    def test_wecdis_parse_depth(self):
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
        processor.process(DEPTH_DATA_PATH, self.store, False)

        # check data got created
        with self.store.session_scope():
            # there must be states after the import
            states = self.store.session.query(self.store.db_classes.State).all()
            self.assertEqual(len(states), 3)

            # there must be platforms after the import
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            self.assertEqual(len(platforms), 1)

            # there must be one datafile afterwards
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 1)

            stored_states = self.store.session.query(self.store.db_classes.State).all()

            ureg = UnitRegistry()
            # 1 - subsurface
            assert stored_states[0].elevation.to(ureg.meter).magnitude == -123
            # 2 - aircraft
            assert stored_states[1].elevation.to(ureg.meter).magnitude == 456
            # 3 - foot based
            assert round(stored_states[2].elevation.to(ureg.foot).magnitude) == 789

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
            self.assertEqual(len(states), 3)

            # there must be platforms after the import
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            self.assertEqual(len(platforms), 1)

            # there must be one datafile afterwards
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 1)
            # POS
            states = self.store.session.query(self.store.db_classes.State).all()
            assert states[0].time == datetime(2021, 11, 1, 1, 2, 30, 123000)
            assert round(states[0].location.latitude, 6) == 12.57613
            assert round(states[0].location.longitude, 6) == -12.57613
            ureg = UnitRegistry()
            assert states[0].speed is None
            assert states[0].heading is None
            assert states[0].sensor.name == "GPS"
            assert states[0].sensor.sensor_type.name == "Location-Satellite"
            # CPOS
            assert states[1].time == datetime(2021, 11, 1, 1, 2, 30, 123000)
            assert round(states[1].location.latitude, 6) == -12.57613
            assert round(states[1].location.longitude, 6) == -0.514239
            assert round(states[1].speed.to(ureg.knot).magnitude, 1) == 2.8
            assert states[1].heading.to(ureg.degree).magnitude == 340
            assert states[1].sensor.name == "ABC_XY"
            assert states[1].sensor.sensor_type.name == "Location-Satellite"
            # POS2
            assert states[2].time == datetime(2021, 11, 1, 1, 2, 30, 123000)
            assert round(states[2].location.latitude, 6) == 12.500054
            assert round(states[2].location.longitude, 6) == 1.170567
            assert states[2].speed is None
            assert states[2].heading is None
            assert states[2].sensor.name == "SENSOR1"
            assert states[2].sensor.sensor_type.name == "Location-Satellite"

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
            self.assertEqual(len(contacts), 2)

            # there must be platforms after the import
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            self.assertEqual(len(platforms), 1)

            # there must be datafile afterwards
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 1)

            stored_contacts = self.store.session.query(self.store.db_classes.Contact).all()

            assert stored_contacts[0].time == datetime(2019, 11, 19, 1, 2, 34, 122000)
            ureg = UnitRegistry()
            assert round(stored_contacts[0].location.latitude, 6) == 1.368723
            assert round(stored_contacts[0].location.longitude, 6) == -12.568518
            assert round(stored_contacts[0].bearing.to(ureg.degree).magnitude) == 270
            assert stored_contacts[0].orientation is None  # No course given
            assert stored_contacts[0].sensor.sensor_type.name == "Position"

            assert stored_contacts[1].time == datetime(2021, 12, 12, 1, 13, 35, 156000)
            assert stored_contacts[1].sensor.sensor_type.name == "Position"

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

            # there must be platforms after the import
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
            assert stored_contacts[0].track_number == "5th ABC 20Ab_BRG - all data"
            # Contact with course, but no location
            assert stored_contacts[1].time == datetime(2020, 11, 1, 1, 2, 34, 543000)
            assert stored_contacts[1].location is None
            assert round(stored_contacts[1].bearing.to(ureg.degree).magnitude) == 190
            assert round(stored_contacts[1].orientation.to(ureg.degree).magnitude) == 255
            assert stored_contacts[1].track_number == "5th ABC 20Ab_BRG - no location"
            # Contact without course or location
            assert stored_contacts[2].time == datetime(2020, 12, 22, 1, 2, 34, 665000)
            assert stored_contacts[2].location is None
            assert round(stored_contacts[2].bearing.to(ureg.degree).magnitude) == 359
            assert stored_contacts[2].orientation is None
            assert stored_contacts[2].track_number == "5th ABC 20Ab_BRG - no loc/course"

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
            self.assertEqual(len(states), 8)

            # there must be contacts after the import
            contacts = self.store.session.query(self.store.db_classes.Contact).all()
            self.assertEqual(len(contacts), 3)

            # there must be platforms after the import
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
            ureg = UnitRegistry()

            assert stored_states[0].time == datetime(2021, 11, 1, 1, 2, 30, 123000)
            assert stored_states[0].sensor.name == "GPS"
            assert stored_states[0].sensor.sensor_type.name == "Location-Satellite"
            assert stored_states[0].speed is None
            assert stored_states[0].heading is None
            assert stored_states[1].time == datetime(2021, 11, 1, 1, 2, 30, 123000)
            assert stored_states[1].sensor.name == "ABC_XY"
            assert stored_states[1].sensor.sensor_type.name == "Location-Satellite"
            assert stored_states[2].time == datetime(2021, 11, 1, 1, 2, 45, 10000)
            assert stored_states[2].speed is None
            assert stored_states[2].heading == 200 * ureg.degree
            assert stored_states[4].time == datetime(2021, 11, 1, 1, 3, 5, 10000)
            assert stored_states[6].time == datetime(2021, 12, 12, 1, 3, 35, 10000)
            assert round(stored_states[6].speed.to(ureg.knot).magnitude, 3) == 3.08
            assert round(stored_states[6].heading.to(ureg.degree).magnitude, 3) == 201.2
            assert stored_states[0].elevation.to(ureg.meter).magnitude == -11.1
            assert stored_states[1].elevation.to(ureg.meter).magnitude == -11.1
            assert stored_states[5].elevation.to(ureg.meter).magnitude == -11.1
            assert stored_states[6].elevation.to(ureg.meter).magnitude == -19.7

            stored_contacts = (
                self.store.session.query(self.store.db_classes.Contact)
                .order_by(self.store.db_classes.Contact.time)
                .all()
            )

            assert round(stored_contacts[0].location.latitude, 6) == 12.566667
            assert round(stored_contacts[0].location.longitude, 6) == 12.899538
            assert stored_contacts[0].bearing is None
            assert round(stored_contacts[0].soa.to(ureg.knot).magnitude, 1) == 3.2

            assert stored_contacts[1].track_number == "5th ABC 20Ab_BRG 2"
            assert round(stored_contacts[1].bearing.to(ureg.degree).magnitude) == 190
            assert stored_contacts[1].soa is None

            assert stored_contacts[2].bearing is None
            assert round(stored_contacts[2].soa.to(ureg.knot).magnitude, 1) == 12.5

            # assert round(stored_contacts[3].bearing.to(ureg.degree).magnitude, 2) == 270.52
            # assert round(stored_contacts[3].range.to(ureg.kilometer).magnitude, 2) == 3.96
            # assert stored_contacts[3].track_number == "TTM_18_a"

            # assert round(stored_contacts[4].bearing.to(ureg.degree).magnitude, 2) == 12.53
            # assert round(stored_contacts[4].range.to(ureg.kilometer).magnitude, 2) == 12.79
            # assert stored_contacts[4].track_number == "TTM_18_b"

    def test_wecdis_multi_pos_sources_sample(self):
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
        processor.process(DATA_MULTI_POS_HDG_VEL_SOURCES_PATH, self.store, False)

        # check data got created
        with self.store.session_scope():
            # there must be states after the import
            states = self.store.session.query(self.store.db_classes.State).all()
            self.assertEqual(len(states), 6)

            # there must be no contacts after the import
            contacts = self.store.session.query(self.store.db_classes.Contact).all()
            self.assertEqual(len(contacts), 0)

            # there must be platforms after the import
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
            ureg = UnitRegistry()

            assert stored_states[0].time == datetime(2021, 11, 1, 1, 2, 30, 123000)
            assert stored_states[0].sensor.name == "GPS"
            assert stored_states[0].sensor.sensor_type.name == "Location-Satellite"
            assert stored_states[0].speed is None
            assert stored_states[0].heading is None

            assert stored_states[1].time == datetime(2021, 11, 1, 1, 2, 33, 10000)
            assert stored_states[1].sensor.name == "GPS"
            assert stored_states[1].sensor.sensor_type.name == "Location-Satellite"
            assert stored_states[1].speed is None
            assert stored_states[1].heading.to(ureg.degree).magnitude == 200

            assert stored_states[2].time == datetime(2021, 11, 1, 1, 3, 5, 10000)
            assert stored_states[2].sensor.name == "GPS"
            assert stored_states[2].sensor.sensor_type.name == "Location-Satellite"
            assert stored_states[2].speed is None
            assert round(stored_states[2].heading.to(ureg.degree).magnitude, 3) == 201.0

            assert stored_states[3].time == datetime(2021, 11, 1, 1, 3, 5, 10000)
            assert stored_states[3].sensor.name == "GPS2"
            assert stored_states[3].sensor.sensor_type.name == "Location-Satellite"
            assert stored_states[3].speed is None
            assert round(stored_states[3].heading.to(ureg.degree).magnitude, 3) == 199.43

            assert stored_states[4].time == datetime(2021, 12, 12, 1, 3, 35, 10000)
            assert stored_states[4].sensor.name == "GPS"
            assert stored_states[4].sensor.sensor_type.name == "Location-Satellite"
            assert round(stored_states[4].speed.to(ureg.knot).magnitude, 2) == 3.08
            assert round(stored_states[4].heading.to(ureg.degree).magnitude, 3) == 201.2

            assert stored_states[5].time == datetime(2021, 12, 12, 1, 3, 35, 10000)
            assert stored_states[5].sensor.name == "GPS2"
            assert stored_states[5].sensor.sensor_type.name == "Location-Satellite"
            assert round(stored_states[5].speed.to(ureg.knot).magnitude, 3) == 6.6
            assert round(stored_states[5].heading.to(ureg.degree).magnitude, 3) == 199.43

    def test_invalid_lat(self):
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
        processor.process(INVALID_LAT_DATA_PATH, self.store, False)

        # check data got created
        with self.store.session_scope():
            # there must be no states after the import
            states = self.store.session.query(self.store.db_classes.State).all()
            self.assertEqual(len(states), 0)

            # there must be no contacts after the import
            contacts = self.store.session.query(self.store.db_classes.Contact).all()
            self.assertEqual(len(contacts), 0)

            # there must be platforms after the import
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            self.assertEqual(len(platforms), 1)

            # there must be no datafile afterwards
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 0)

            # just one importer has run
            assert len(processor.importers) == 1
            # just one error reported
            assert len(processor.importers[0].errors) == 1
            # error related to latitude length
            self.assertTrue("incorrect length for latitude", processor.importers[0].errors[0])

    def test_invalid_lon(self):
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
        processor.process(INVALID_LON_DATA_PATH, self.store, False)

        # check data got created
        with self.store.session_scope():
            # there must be no states after the import - invalid location
            states = self.store.session.query(self.store.db_classes.State).all()
            self.assertEqual(len(states), 0)

            # there must be platforms after the import
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            self.assertEqual(len(platforms), 1)

            # there won't be datafile afterwards - failed import
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 0)

            assert len(processor.importers[0].errors) == 1

    # def test_ttm_invalid_values(self):
    #     processor = FileProcessor(archive=False)
    #     processor.register_importer(WecdisImporter())

    #     # check states empty
    #     with self.store.session_scope():
    #         # there must be no contacts at the beginning
    #         contacts = self.store.session.query(self.store.db_classes.Contact).all()
    #         self.assertEqual(len(contacts), 0)

    #         # there must be no platforms at the beginning
    #         platforms = self.store.session.query(self.store.db_classes.Platform).all()
    #         self.assertEqual(len(platforms), 0)

    #         # there must be no datafiles at the beginning
    #         datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
    #         self.assertEqual(len(datafiles), 0)

    #     # parse the folder
    #     processor.process(INVALID_TTM_PATH, self.store, False)

    #     # check data got created
    #     with self.store.session_scope():
    #         # there must be no states after the import - invalid location
    #         states = self.store.session.query(self.store.db_classes.Contact).all()
    #         self.assertEqual(len(states), 0)

    #         # there must be platforms after the import
    #         platforms = self.store.session.query(self.store.db_classes.Platform).all()
    #         self.assertEqual(len(platforms), 1)

    #         # there won't be datafile afterwards - failed import
    #         datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
    #         self.assertEqual(len(datafiles), 0)

    #         assert len(processor.importers[0].errors) == 4

    # Datetime tests for formats that we don't have in sample data but are in NMEA
    @staticmethod
    def test_timestamp_short_form_date():
        timestamp = WecdisImporter.parse_timestamp("210504", "120000")
        assert timestamp == datetime(2021, 5, 4, 12)

    @staticmethod
    def test_timestamp_milliseconds_time():
        timestamp = WecdisImporter.parse_timestamp("20210504", "120000.1201")
        assert timestamp == datetime(2021, 5, 4, 12, 0, 0, 120100)


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
