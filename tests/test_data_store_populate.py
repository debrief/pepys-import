import unittest
import os

from pepys_import.core.store.data_store import DataStore
from unittest import TestCase

FILE_PATH = os.path.dirname(__file__)
TEST_DATA_PATH = os.path.join(FILE_PATH, "sample_data", "csv_files")


class TestDataStorePopulate(TestCase):
    def setUp(self):
        self.sqlite = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.sqlite.initialise()

    def tearDown(self):
        pass

    def test_populate_reference(self):
        """Test whether CSVs successfully imported to SQLite"""

        # Check tables are created but empty
        with self.sqlite.session_scope() as session:
            nationalities = self.sqlite.get_nationalities()
            platform_types = self.sqlite.get_platform_types()

        # There must be no entities at the beginning
        self.assertEqual(len(nationalities), 0)
        self.assertEqual(len(platform_types), 0)

        # Import CSVs to the related tables
        with self.sqlite.session_scope() as session:
            self.sqlite.populate_reference(TEST_DATA_PATH)

        # Check tables filled with correct data
        with self.sqlite.session_scope() as session:
            nationalities = self.sqlite.get_nationalities()
            platform_types = self.sqlite.get_platform_types()
            nationality_object = self.sqlite.search_nationality("UNITED KINGDOM")
            platform_type_object = self.sqlite.search_platform_type("TYPE-1")

            # Check whether they are not empty anymore and filled with correct data
            self.assertNotEqual(len(nationalities), 0)
            self.assertNotEqual(len(platform_types), 0)

            self.assertIn(nationality_object.name, "UNITED KINGDOM")
            self.assertIn(platform_type_object.name, "TTYPE-1")

    def test_populate_metadata(self):
        # reference tables must be filled first
        with self.sqlite.session_scope() as session:
            self.sqlite.populate_reference(TEST_DATA_PATH)

        # get all table values
        with self.sqlite.session_scope() as session:
            platforms = self.sqlite.get_platforms()
            datafiles = self.sqlite.get_datafiles()
            sensors = self.sqlite.get_sensors()

        # There must be no entities at the beginning
        self.assertEqual(len(platforms), 0)
        self.assertEqual(len(datafiles), 0)
        self.assertEqual(len(sensors), 0)

        # Import CSVs to the related tables
        with self.sqlite.session_scope() as session:
            self.sqlite.populate_metadata(TEST_DATA_PATH)

        with self.sqlite.session_scope() as session:
            platforms = self.sqlite.get_platforms()
            datafiles = self.sqlite.get_datafiles()
            sensors = self.sqlite.get_sensors()

            platform_object = self.sqlite.search_platform("PLATFORM-1")
            datafile_object = self.sqlite.search_datafile("DATAFILE-1")
            sensor_object = self.sqlite.search_sensor("SENSOR-1")

            # Check whether they are not empty anymore and filled with correct data
            self.assertNotEqual(len(platforms), 0)
            self.assertNotEqual(len(datafiles), 0)
            self.assertNotEqual(len(sensors), 0)

            # The following assertions filter objects by foreign key ids and
            # compares values with the data from CSV

            # Platform Object: PLATFORM-1, UNITED KINGDOM, TYPE-1, PRIVACY-1
            nationality = (
                self.sqlite.session.query(self.sqlite.db_classes.Nationality)
                .filter_by(nationality_id=platform_object.nationality_id)
                .first()
            )
            self.assertEqual(nationality.name, "UNITED KINGDOM")
            platform_type = (
                self.sqlite.session.query(self.sqlite.db_classes.PlatformType)
                .filter_by(platform_type_id=platform_object.platform_type_id)
                .first()
            )
            self.assertEqual(platform_type.name, "TYPE-1")
            privacy = (
                self.sqlite.session.query(self.sqlite.db_classes.Privacy)
                .filter_by(privacy_id=platform_object.privacy_id)
                .first()
            )
            self.assertEqual(privacy.name, "PRIVACY-1")

            # Datafile Object: DATAFILE-1, True, PRIVACY-1, DATAFILE-TYPE-1
            self.assertEqual(datafile_object.simulated, True)
            privacy = (
                self.sqlite.session.query(self.sqlite.db_classes.Privacy)
                .filter_by(privacy_id=datafile_object.privacy_id)
                .first()
            )
            self.assertEqual(privacy.name, "PRIVACY-1")
            datafile_type = (
                self.sqlite.session.query(self.sqlite.db_classes.DatafileType)
                .filter_by(datafile_type_id=datafile_object.datafile_type_id)
                .first()
            )
            self.assertEqual(datafile_type.name, "DATAFILE-TYPE-1")

            # Sensor Object: SENSOR-1, SENSOR-TYPE-1, PLATFORM-1
            sensor_type = (
                self.sqlite.session.query(self.sqlite.db_classes.SensorType)
                .filter_by(sensor_type_id=sensor_object.sensor_type_id)
                .first()
            )
            self.assertEqual(sensor_type.name, "SENSOR-TYPE-1")
            platform = (
                self.sqlite.session.query(self.sqlite.db_classes.Platform)
                .filter_by(platform_id=sensor_object.platform_id)
                .first()
            )
            self.assertEqual(platform.name, "PLATFORM-1")


if __name__ == "__main__":
    unittest.main()
