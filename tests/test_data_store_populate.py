import unittest
import os

from datetime import datetime
from unittest import TestCase
from sqlalchemy.sql.ddl import DropSchema
from testing.postgresql import Postgresql
from sqlalchemy.exc import OperationalError
from sqlalchemy import event
from pepys_import.core.store.data_store import DataStore
from pepys_import.core.store.db_base import BasePostGIS

from contextlib import redirect_stdout
from io import StringIO


FILE_PATH = os.path.dirname(__file__)
TEST_DATA_PATH = os.path.join(FILE_PATH, "sample_data", "csv_files")
NOT_IMPLEMENTED_PATH = os.path.join(
    FILE_PATH, "sample_data", "csv_files", "for_not_implemented_methods"
)


class DataStorePopulateSpatiaLiteTestCase(TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_populate_reference(self):
        """Test whether CSVs successfully imported to SQLite"""

        # Check tables are created but empty
        with self.store.session_scope() as session:
            nationalities = self.store.session.query(
                self.store.db_classes.Nationality
            ).all()
            platform_types = self.store.session.query(
                self.store.db_classes.PlatformType
            ).all()

        # There must be no entities at the beginning
        self.assertEqual(len(nationalities), 0)
        self.assertEqual(len(platform_types), 0)

        # Import CSVs to the related tables
        with self.store.session_scope() as session:
            self.store.populate_reference()

        # Check tables filled with correct data
        with self.store.session_scope() as session:
            nationalities = self.store.session.query(
                self.store.db_classes.Nationality
            ).all()
            platform_types = self.store.session.query(
                self.store.db_classes.PlatformType
            ).all()
            nationality_object = self.store.search_nationality("UNITED KINGDOM")
            platform_type_object = self.store.search_platform_type("TYPE-1")

            # Check whether they are not empty anymore and filled with correct data
            self.assertNotEqual(len(nationalities), 0)
            self.assertNotEqual(len(platform_types), 0)

            self.assertIn(nationality_object.name, "UNITED KINGDOM")
            self.assertIn(platform_type_object.name, "TTYPE-1")

    def test_populate_metadata(self):
        # reference tables must be filled first
        with self.store.session_scope() as session:
            self.store.populate_reference()

        # get all table values
        with self.store.session_scope() as session:
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            sensors = self.store.session.query(self.store.db_classes.Sensor).all()

        # There must be no entities at the beginning
        self.assertEqual(len(platforms), 0)
        self.assertEqual(len(datafiles), 0)
        self.assertEqual(len(sensors), 0)

        # Import CSVs to the related tables
        with self.store.session_scope() as session:
            self.store.populate_metadata()

        with self.store.session_scope() as session:
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            sensors = self.store.session.query(self.store.db_classes.Sensor).all()

            platform_object = self.store.search_platform("PLATFORM-1")
            datafile_object = self.store.search_datafile("DATAFILE-1")
            sensor_object = self.store.search_sensor("SENSOR-1")

            # Check whether they are not empty anymore and filled with correct data
            self.assertNotEqual(len(platforms), 0)
            self.assertNotEqual(len(datafiles), 0)
            self.assertNotEqual(len(sensors), 0)

            # The following assertions filter objects by foreign key ids and
            # compares values with the data from CSV

            # Platform Object: PLATFORM-1, UNITED KINGDOM, TYPE-1, PRIVACY-1
            nationality = (
                self.store.session.query(self.store.db_classes.Nationality)
                .filter_by(nationality_id=platform_object.nationality_id)
                .first()
            )
            self.assertEqual(nationality.name, "UNITED KINGDOM")
            platform_type = (
                self.store.session.query(self.store.db_classes.PlatformType)
                .filter_by(platform_type_id=platform_object.platform_type_id)
                .first()
            )
            self.assertEqual(platform_type.name, "TYPE-1")
            privacy = (
                self.store.session.query(self.store.db_classes.Privacy)
                .filter_by(privacy_id=platform_object.privacy_id)
                .first()
            )
            self.assertEqual(privacy.name, "PRIVACY-1")

            # Datafile Object: DATAFILE-1, True, PRIVACY-1, DATAFILE-TYPE-1
            self.assertEqual(datafile_object.simulated, True)
            privacy = (
                self.store.session.query(self.store.db_classes.Privacy)
                .filter_by(privacy_id=datafile_object.privacy_id)
                .first()
            )
            self.assertEqual(privacy.name, "PRIVACY-1")
            datafile_type = (
                self.store.session.query(self.store.db_classes.DatafileType)
                .filter_by(datafile_type_id=datafile_object.datafile_type_id)
                .first()
            )
            self.assertEqual(datafile_type.name, "DATAFILE-TYPE-1")

            # Sensor Object: SENSOR-1, SENSOR-TYPE-1, PLATFORM-1
            sensor_type = (
                self.store.session.query(self.store.db_classes.SensorType)
                .filter_by(sensor_type_id=sensor_object.sensor_type_id)
                .first()
            )
            self.assertEqual(sensor_type.name, "SENSOR-TYPE-1")

    def test_populate_measurement(self):
        # reference and metadata tables must be filled first
        with self.store.session_scope() as session:
            self.store.populate_reference()
            self.store.populate_metadata()

        # get all table values
        with self.store.session_scope() as session:
            states = self.store.session.query(self.store.db_classes.State).all()

        # There must be no entities at the beginning
        self.assertEqual(len(states), 0)

        # Import CSVs to the related tables
        with self.store.session_scope() as session:
            self.store.populate_measurement()

        # Check tables filled with correct data
        with self.store.session_scope() as session:
            states = self.store.session.query(self.store.db_classes.State).all()
            first_state = self.store.session.query(self.store.db_classes.State).first()

            # Check whether they are not empty anymore and filled with correct data
            self.assertNotEqual(len(states), 0)

            # The following assertions filter objects by foreign key ids and
            # compares values with the data from CSV

            # first_state = 2019-01-12 12:10:00, SENSOR-1, DATAFILE-1,46.000 32.000,,,,
            # PRIVACY-1
            self.assertEqual(
                first_state.time,
                datetime.strptime("2019-01-12 12:10:00", "%Y-%m-%d %H:%M:%S"),
            )

            privacy = (
                self.store.session.query(self.store.db_classes.Privacy)
                .filter_by(privacy_id=first_state.privacy_id)
                .first()
            )
            self.assertEqual(privacy.name, "PRIVACY-1")
            datafile = (
                self.store.session.query(self.store.db_classes.Datafile)
                .filter_by(datafile_id=first_state.source_id)
                .first()
            )
            self.assertEqual(datafile.reference, "DATAFILE-1")
            sensor = (
                self.store.session.query(self.store.db_classes.Sensor)
                .filter_by(sensor_id=first_state.sensor_id)
                .first()
            )
            self.assertEqual(sensor.name, "SENSOR-1")


class DataStorePopulatePostGISTestCase(TestCase):
    def setUp(self) -> None:
        self.postgres = None
        self.store = None
        try:
            self.postgres = Postgresql(
                database="test",
                host="localhost",
                user="postgres",
                password="postgres",
                port=55527,
            )
        except RuntimeError:
            print("PostgreSQL database couldn't be created! Test is skipping.")
            return
        try:
            self.store = DataStore(
                db_name="test",
                db_host="localhost",
                db_username="postgres",
                db_password="postgres",
                db_port=55527,
            )
            self.store.initialise()
        except OperationalError:
            print("Database schema and data population failed! Test is skipping.")

    def tearDown(self) -> None:
        try:
            event.listen(
                BasePostGIS.metadata, "before_create", DropSchema("datastore_schema")
            )
            self.postgres.stop()
        except AttributeError:
            return

    def test_populate_reference(self):
        """Test whether CSVs successfully imported to PostGIS"""

        # Check tables are created but empty
        with self.store.session_scope() as session:
            nationalities = self.store.session.query(
                self.store.db_classes.Nationality
            ).all()
            platform_types = self.store.session.query(
                self.store.db_classes.PlatformType
            ).all()

        # There must be no entities at the beginning
        self.assertEqual(len(nationalities), 0)
        self.assertEqual(len(platform_types), 0)

        # Import CSVs to the related tables
        with self.store.session_scope() as session:
            self.store.populate_reference()

        # Check tables filled with correct data
        with self.store.session_scope() as session:
            nationalities = self.store.session.query(
                self.store.db_classes.Nationality
            ).all()
            platform_types = self.store.session.query(
                self.store.db_classes.PlatformType
            ).all()
            nationality_object = self.store.search_nationality("UNITED KINGDOM")
            platform_type_object = self.store.search_platform_type("TYPE-1")

            # Check whether they are not empty anymore and filled with correct data
            self.assertNotEqual(len(nationalities), 0)
            self.assertNotEqual(len(platform_types), 0)

            self.assertIn(nationality_object.name, "UNITED KINGDOM")
            self.assertIn(platform_type_object.name, "TTYPE-1")

    def test_populate_metadata(self):
        # reference tables must be filled first
        with self.store.session_scope() as session:
            self.store.populate_reference()

        # get all table values
        with self.store.session_scope() as session:
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            sensors = self.store.session.query(self.store.db_classes.Sensor).all()

        # There must be no entities at the beginning
        self.assertEqual(len(platforms), 0)
        self.assertEqual(len(datafiles), 0)
        self.assertEqual(len(sensors), 0)

        # Import CSVs to the related tables
        with self.store.session_scope() as session:
            self.store.populate_metadata()

        with self.store.session_scope() as session:
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            sensors = self.store.session.query(self.store.db_classes.Sensor).all()

            platform_object = self.store.search_platform("PLATFORM-1")
            datafile_object = self.store.search_datafile("DATAFILE-1")
            sensor_object = self.store.search_sensor("SENSOR-1")

            # Check whether they are not empty anymore and filled with correct data
            self.assertNotEqual(len(platforms), 0)
            self.assertNotEqual(len(datafiles), 0)
            self.assertNotEqual(len(sensors), 0)

            # The following assertions filter objects by foreign key ids and
            # compares values with the data from CSV

            # Platform Object: PLATFORM-1, UNITED KINGDOM, TYPE-1, PRIVACY-1
            nationality = (
                self.store.session.query(self.store.db_classes.Nationality)
                .filter_by(nationality_id=platform_object.nationality_id)
                .first()
            )
            self.assertEqual(nationality.name, "UNITED KINGDOM")
            platform_type = (
                self.store.session.query(self.store.db_classes.PlatformType)
                .filter_by(platform_type_id=platform_object.platform_type_id)
                .first()
            )
            self.assertEqual(platform_type.name, "TYPE-1")
            privacy = (
                self.store.session.query(self.store.db_classes.Privacy)
                .filter_by(privacy_id=platform_object.privacy_id)
                .first()
            )
            self.assertEqual(privacy.name, "PRIVACY-1")

            # Datafile Object: DATAFILE-1, True, PRIVACY-1, DATAFILE-TYPE-1
            self.assertEqual(datafile_object.simulated, True)
            privacy = (
                self.store.session.query(self.store.db_classes.Privacy)
                .filter_by(privacy_id=datafile_object.privacy_id)
                .first()
            )
            self.assertEqual(privacy.name, "PRIVACY-1")
            datafile_type = (
                self.store.session.query(self.store.db_classes.DatafileType)
                .filter_by(datafile_type_id=datafile_object.datafile_type_id)
                .first()
            )
            self.assertEqual(datafile_type.name, "DATAFILE-TYPE-1")

            # Sensor Object: SENSOR-1, SENSOR-TYPE-1, PLATFORM-1
            sensor_type = (
                self.store.session.query(self.store.db_classes.SensorType)
                .filter_by(sensor_type_id=sensor_object.sensor_type_id)
                .first()
            )
            self.assertEqual(sensor_type.name, "SENSOR-TYPE-1")

    def test_populate_measurement(self):
        # reference and metadata tables must be filled first
        with self.store.session_scope() as session:
            self.store.populate_reference()
            self.store.populate_metadata()

        # get all table values
        with self.store.session_scope() as session:
            states = self.store.session.query(self.store.db_classes.State).all()

        # There must be no entities at the beginning
        self.assertEqual(len(states), 0)

        # Import CSVs to the related tables
        with self.store.session_scope() as session:
            self.store.populate_measurement()

        # Check tables filled with correct data
        with self.store.session_scope() as session:
            states = self.store.session.query(self.store.db_classes.State).all()
            first_state = self.store.session.query(self.store.db_classes.State).first()

            # Check whether they are not empty anymore and filled with correct data
            self.assertNotEqual(len(states), 0)

            # The following assertions filter objects by foreign key ids and
            # compares values with the data from CSV

            # first_state = 2019-01-12 12:10:00, SENSOR-1, DATAFILE-1,46.000 32.000,,,,
            # PRIVACY-1
            self.assertEqual(
                first_state.time,
                datetime.strptime("2019-01-12 12:10:00", "%Y-%m-%d %H:%M:%S"),
            )

            privacy = (
                self.store.session.query(self.store.db_classes.Privacy)
                .filter_by(privacy_id=first_state.privacy_id)
                .first()
            )
            self.assertEqual(privacy.name, "PRIVACY-1")
            datafile = (
                self.store.session.query(self.store.db_classes.Datafile)
                .filter_by(datafile_id=first_state.source_id)
                .first()
            )
            self.assertEqual(datafile.reference, "DATAFILE-1")
            sensor = (
                self.store.session.query(self.store.db_classes.Sensor)
                .filter_by(sensor_id=first_state.sensor_id)
                .first()
            )
            self.assertEqual(sensor.name, "SENSOR-1")


# TODO: This test case should fail when all add_to_XXX methods are implemented.
#  Remove it when there are add methods for each DB table.
class DataStorePopulateNotImplementedMethodTestCase(TestCase):
    """Test whether populate methods print correct table name and message
    when the corresponding add method is not found"""

    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_populate_reference(self):
        with self.store.session_scope() as session:
            temp_output = StringIO()
            with redirect_stdout(temp_output):
                self.store.populate_reference(NOT_IMPLEMENTED_PATH)
            output = temp_output.getvalue()
            self.assertIn("Method(add_to_confidence_levels) not found!", output)

    def test_populate_metadata(self):
        with self.store.session_scope() as session:
            temp_output = StringIO()
            with redirect_stdout(temp_output):
                self.store.populate_reference(NOT_IMPLEMENTED_PATH)
                self.store.populate_metadata(NOT_IMPLEMENTED_PATH)
            output = temp_output.getvalue()
            self.assertIn("Method(add_to_confidence_levels) not found!", output)
            self.assertIn("Method(add_to_tags) not found!", output)

    def test_populate_measurement(self):
        with self.store.session_scope() as session:
            temp_output = StringIO()
            with redirect_stdout(temp_output):
                self.store.populate_reference(NOT_IMPLEMENTED_PATH)
                self.store.populate_metadata(NOT_IMPLEMENTED_PATH)
                self.store.populate_measurement(NOT_IMPLEMENTED_PATH)
            output = temp_output.getvalue()
            self.assertIn("Method(add_to_confidence_levels) not found!", output)
            self.assertIn("Method(add_to_tags) not found!", output)
            self.assertIn("Method(add_to_media) not found!", output)


if __name__ == "__main__":
    unittest.main()
