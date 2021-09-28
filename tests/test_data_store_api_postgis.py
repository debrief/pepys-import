import os
import unittest
from contextlib import redirect_stdout
from datetime import datetime
from io import StringIO
from sqlite3 import OperationalError
from unittest import TestCase
from unittest.mock import patch

import pytest
from testing.postgresql import Postgresql

from pepys_import.core.store import constants
from pepys_import.core.store.data_store import DataStore
from pepys_import.core.store.db_status import TableTypes
from pepys_import.core.validators import constants as validation_constants
from pepys_import.file.file_processor import FileProcessor
from pepys_import.file.importer import Importer
from tests.utils import side_effect

FILE_PATH = os.path.dirname(__file__)
TEST_DATA_PATH = os.path.join(FILE_PATH, "sample_data", "csv_files")
REP_DATA_PATH = os.path.join(FILE_PATH, "sample_data", "track_files", "rep_data", "rep_test1.rep")


@pytest.mark.postgres
class DataStoreCacheTestCase(TestCase):
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
            raise Exception("Testing Postgres server could not be started/accessed")
        try:
            self.store = DataStore(
                db_name="test",
                db_host="localhost",
                db_username="postgres",
                db_password="postgres",
                db_port=55527,
                db_type="postgres",
            )
            self.store.initialise()
            with self.store.session_scope():
                self.change_id = self.store.add_to_changes(
                    "TEST", datetime.utcnow(), "TEST"
                ).change_id
        except Exception:
            raise Exception("Testing postgres server could not be started/accessed")

    def tearDown(self) -> None:
        try:
            self.postgres.stop()
        except AttributeError:
            return

    def test_cached_comment_types(self):
        """Test whether a new comment type entity cached and returned"""
        with self.store.session_scope():
            comment_types = self.store.session.query(self.store.db_classes.CommentType).all()

            # there must be no entity at the beginning
            self.assertEqual(len(comment_types), 0)

            comment_type_1 = self.store.add_to_comment_types("Comment-1", self.change_id)
            # This one shouldn't duplicate, it must return existing entity
            comment_type_2 = self.store.add_to_comment_types("Comment-1", self.change_id)

            # objects must be the same since the second object
            # is cached of first the one
            self.assertEqual(comment_type_1, comment_type_2)

            comment_types = self.store.session.query(self.store.db_classes.CommentType).all()
            # there must be only one entity at the beginning
            self.assertEqual(len(comment_types), 1)

    def test_cached_platform_types(self):
        """Test whether a new platform type entity cached and returned"""
        with self.store.session_scope():
            platform_types = self.store.session.query(self.store.db_classes.PlatformType).all()

            # there must be no entity at the beginning
            self.assertEqual(len(platform_types), 0)

            platform_type_1 = self.store.add_to_platform_types(
                name="test", change_id=self.change_id
            )
            # This one shouldn't duplicate, it should return existing entity
            platform_type_2 = self.store.add_to_platform_types(
                name="test", change_id=self.change_id
            )

            # objects must be the same
            self.assertEqual(platform_type_1, platform_type_2)
            platform_types = self.store.session.query(self.store.db_classes.PlatformType).all()

            # there must be only one entity at the beginning
            self.assertEqual(len(platform_types), 1)

    def test_cached_nationalities(self):
        """Test whether a new nationality entity cached and returned"""
        with self.store.session_scope():
            nationalities = self.store.session.query(self.store.db_classes.Nationality).all()

            # there must be no entity at the beginning
            self.assertEqual(len(nationalities), 0)

            nationality_1 = self.store.add_to_nationalities(name="test", change_id=self.change_id)
            # This one shouldn't duplicate, it should return existing entity
            nationality_2 = self.store.add_to_nationalities(name="test", change_id=self.change_id)

            # objects must be the same
            self.assertEqual(nationality_1, nationality_2)
            nationalities = self.store.session.query(self.store.db_classes.Nationality).all()

            # there must be only one entity at the beginning
            self.assertEqual(len(nationalities), 1)

    def test_cached_privacies(self):
        """Test whether a new privacy entity cached and returned"""
        with self.store.session_scope():
            privacies = self.store.session.query(self.store.db_classes.Privacy).all()

            # there must be no entity at the beginning
            self.assertEqual(len(privacies), 0)

            privacy_1 = self.store.add_to_privacies(name="test", level=0, change_id=self.change_id)
            # This one shouldn't duplicate, it should return existing entity
            privacy_2 = self.store.add_to_privacies(name="test", level=0, change_id=self.change_id)

            # objects must be the same
            self.assertEqual(privacy_1, privacy_2)
            privacies = self.store.session.query(self.store.db_classes.Privacy).all()

            # there must be only one entity at the beginning
            self.assertEqual(len(privacies), 1)

    def test_cached_datafile_types(self):
        """Test whether a new datafile type entity cached and returned"""
        with self.store.session_scope():
            datafile_types = self.store.session.query(self.store.db_classes.DatafileType).all()

            # there must be no entity at the beginning
            self.assertEqual(len(datafile_types), 0)

            datafile_type_1 = self.store.add_to_datafile_types(
                name="test", change_id=self.change_id
            )
            # This one shouldn't duplicate, it should return existing entity
            datafile_type_2 = self.store.add_to_datafile_types(
                name="test", change_id=self.change_id
            )

            # objects must be the same
            self.assertEqual(datafile_type_1, datafile_type_2)
            datafile_types = self.store.session.query(self.store.db_classes.DatafileType).all()

            # there must be only one entity at the beginning
            self.assertEqual(len(datafile_types), 1)

    def test_cached_sensor_types(self):
        """Test whether a new sensor type entity cached and returned"""
        with self.store.session_scope():
            sensor_types = self.store.session.query(self.store.db_classes.SensorType).all()

            # there must be no entity at the beginning
            self.assertEqual(len(sensor_types), 0)

            sensor_type_1 = self.store.add_to_sensor_types(name="test", change_id=self.change_id)
            # This one shouldn't duplicate, it should return existing entity
            sensor_type_2 = self.store.add_to_sensor_types(name="test", change_id=self.change_id)

            # objects must be the same
            self.assertEqual(sensor_type_1, sensor_type_2)
            sensor_types = self.store.session.query(self.store.db_classes.SensorType).all()

            # there must be only one entity at the beginning
            self.assertEqual(len(sensor_types), 1)

    def test_cached_geometry_type(self):
        """Test whether a new geometry type entity cached and returned"""
        with self.store.session_scope():
            geometry_types = self.store.session.query(self.store.db_classes.GeometryType).all()

            # there must be no entity at the beginning
            self.assertEqual(len(geometry_types), 0)

            geometry_type_1 = self.store.add_to_geometry_types(
                name="test", change_id=self.change_id
            )
            # This one shouldn't duplicate, it should return existing entity
            geometry_type_2 = self.store.add_to_geometry_types(
                name="test", change_id=self.change_id
            )

            # objects must be the same
            self.assertEqual(geometry_type_1, geometry_type_2)
            geometry_types = self.store.session.query(self.store.db_classes.GeometryType).all()

            # there must be only one entity at the beginning
            self.assertEqual(len(geometry_types), 1)

    def test_cached_geometry_sub_type(self):
        """Test whether a new geometry sub type entity cached and returned"""
        with self.store.session_scope():
            geometry_sub_types = self.store.session.query(
                self.store.db_classes.GeometrySubType
            ).all()

            # there must be no entity at the beginning
            self.assertEqual(len(geometry_sub_types), 0)

            # Create Geometry Type as parent
            geometry_type = self.store.add_to_geometry_types(
                name="Test Parent", change_id=self.change_id
            )

            geometry_sub_type_1 = self.store.add_to_geometry_sub_types(
                name="test", parent_name=geometry_type.name, change_id=self.change_id
            )
            # This one shouldn't duplicate, it should return existing entity
            geometry_sub_type_2 = self.store.add_to_geometry_sub_types(
                name="test", parent_name=geometry_type.name, change_id=self.change_id
            )

            # objects must be the same
            self.assertEqual(geometry_sub_type_1, geometry_sub_type_2)
            geometry_sub_types = self.store.session.query(
                self.store.db_classes.GeometrySubType
            ).all()

            # there must be only one entity at the beginning
            self.assertEqual(len(geometry_sub_types), 1)


@pytest.mark.postgres
class LookUpDBAndAddToCacheTestCase(TestCase):
    """Test searching functionality and adding existing DB entities to the cache of
    DataStore"""

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
            raise Exception("Testing Postgres server could not be started/accessed")
        try:
            self.store = DataStore(
                db_name="test",
                db_host="localhost",
                db_username="postgres",
                db_password="postgres",
                db_port=55527,
                db_type="postgres",
            )
            self.store.initialise()
            with self.store.session_scope():
                self.change_id = self.store.add_to_changes(
                    "TEST", datetime.utcnow(), "TEST"
                ).change_id
        except OperationalError:
            raise Exception("Creating database schema in testing Postgres database failed")

    def tearDown(self) -> None:
        try:
            self.postgres.stop()
        except AttributeError:
            return

    def test_comment_types(self):
        with self.store.session_scope():
            comment_type = self.store.db_classes.CommentType(name="test")
            self.store.session.add(comment_type)
            self.store.session.flush()

            comment_types = self.store.session.query(self.store.db_classes.CommentType).all()

            # there must be one entity at the beginning
            self.assertEqual(len(comment_types), 1)

            self.store.add_to_comment_types("test", self.change_id)

            comment_types = self.store.session.query(self.store.db_classes.CommentType).all()

            # there must be only one entity again
            self.assertEqual(len(comment_types), 1)

    def test_platform_types(self):
        with self.store.session_scope():
            platform_type = self.store.db_classes.PlatformType(name="test")
            self.store.session.add(platform_type)
            self.store.session.flush()

            platform_types = self.store.session.query(self.store.db_classes.PlatformType).all()

            # there must be one entity at the beginning
            self.assertEqual(len(platform_types), 1)

            self.store.add_to_platform_types("test", self.change_id)

            platform_types = self.store.session.query(self.store.db_classes.PlatformType).all()

            # there must be only one entity again
            self.assertEqual(len(platform_types), 1)

    def test_nationalities(self):
        with self.store.session_scope():
            nationality = self.store.db_classes.Nationality(name="test")
            self.store.session.add(nationality)
            self.store.session.flush()

            nationalities = self.store.session.query(self.store.db_classes.Nationality).all()

            # there must be one entity at the beginning
            self.assertEqual(len(nationalities), 1)

            self.store.add_to_nationalities("test", self.change_id)

            nationalities = self.store.session.query(self.store.db_classes.Nationality).all()

            # there must be only one entity again
            self.assertEqual(len(nationalities), 1)

    def test_privacies(self):
        with self.store.session_scope():
            privacy = self.store.db_classes.Privacy(name="test", level=0)
            self.store.session.add(privacy)
            self.store.session.flush()

            privacies = self.store.session.query(self.store.db_classes.Privacy).all()

            # there must be one entity at the beginning
            self.assertEqual(len(privacies), 1)

            self.store.add_to_privacies("test", 0, self.change_id)

            privacies = self.store.session.query(self.store.db_classes.Privacy).all()

            # there must be only one entity again
            self.assertEqual(len(privacies), 1)

    def test_datafile_types(self):
        with self.store.session_scope():
            datafile_type = self.store.db_classes.DatafileType(name="test")
            self.store.session.add(datafile_type)
            self.store.session.flush()

            datafile_types = self.store.session.query(self.store.db_classes.DatafileType).all()

            # there must be one entity at the beginning
            self.assertEqual(len(datafile_types), 1)

            self.store.add_to_datafile_types("test", self.change_id)

            datafile_types = self.store.session.query(self.store.db_classes.DatafileType).all()

            # there must be only one entity again
            self.assertEqual(len(datafile_types), 1)

    def test_sensor_types(self):
        with self.store.session_scope():
            sensor_type = self.store.db_classes.SensorType(name="test")
            self.store.session.add(sensor_type)
            self.store.session.flush()

            sensor_types = self.store.session.query(self.store.db_classes.SensorType).all()

            # there must be one entity at the beginning
            self.assertEqual(len(sensor_types), 1)

            self.store.add_to_sensor_types("test", self.change_id)

            sensor_types = self.store.session.query(self.store.db_classes.SensorType).all()

            # there must be only one entity again
            self.assertEqual(len(sensor_types), 1)


@pytest.mark.postgres
class PlatformAndDatafileTestCase(TestCase):
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
            raise Exception("Testing Postgres server could not be started/accessed")
        try:
            self.store = DataStore(
                db_name="test",
                db_host="localhost",
                db_username="postgres",
                db_password="postgres",
                db_port=55527,
                db_type="postgres",
            )
            self.store.initialise()
            with self.store.session_scope():
                self.change_id = self.store.add_to_changes(
                    "TEST", datetime.utcnow(), "TEST"
                ).change_id
                self.nationality = self.store.add_to_nationalities(
                    "test_nationality", self.change_id
                ).name
                self.platform_type = self.store.add_to_platform_types(
                    "test_platform_type", self.change_id
                ).name
                self.privacy = self.store.add_to_privacies("test_privacy", 0, self.change_id).name
        except OperationalError:
            raise Exception("Creating database schema in testing Postgres database failed")

    def tearDown(self) -> None:
        try:
            self.postgres.stop()
        except AttributeError:
            return

    def test_new_datafile_added_successfully(self):
        """Test whether a new datafile is created successfully or not"""

        with self.store.session_scope():
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()

        # there must be no entry at the beginning
        self.assertEqual(len(datafiles), 0)

        with self.store.session_scope():
            self.store.get_datafile("test_file.csv", "csv", 0, "HASHED", self.change_id)

        # there must be one entry
        with self.store.session_scope():
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 1)
            self.assertEqual(datafiles[0].reference, "test_file.csv")

    def test_present_datafile_not_added(self):
        """Test whether present datafile is not created"""

        with self.store.session_scope():
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()

        # there must be no entry at the beginning
        self.assertEqual(len(datafiles), 0)

        with self.store.session_scope():
            self.store.get_datafile("test_file.csv", "csv", 0, "HASHED-1", self.change_id)
            self.store.get_datafile("test_file.csv", "csv", 0, "HASHED-2", self.change_id)

            # there must be one entry
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 1)
            self.assertEqual(datafiles[0].reference, "test_file.csv")

    def test_find_datafile(self):
        """Test whether find_datafile method returns the correct Datafile entity"""
        with self.store.session_scope():
            # Create a datafile
            datafile = self.store.get_datafile(
                "test_file.csv", "csv", 0, "HASHED-1", self.change_id
            )
            self.store.get_datafile("test_file_2.csv", "csv", 0, "HASHED-2", self.change_id)
            found_datafile = self.store.find_datafile("test_file.csv")

            self.assertEqual(datafile.datafile_id, found_datafile.datafile_id)
            self.assertEqual(found_datafile.reference, "test_file.csv")

    def test_find_datafile_synonym(self):
        """Test whether find_datafile method finds the correct Datafile entity from Synonyms table"""
        with self.store.session_scope():
            datafile = self.store.get_datafile(
                "test_file.csv", "csv", 0, "HASHED-1", self.change_id
            )
            self.store.get_datafile("test_file_2.csv", "csv", 0, "HASHED-2", self.change_id)
            self.store.add_to_synonyms(
                table=constants.DATAFILE,
                name="TEST",
                entity=datafile.datafile_id,
                change_id=self.change_id,
            )

            found_datafile = self.store.find_datafile("TEST")
            self.assertEqual(datafile.datafile_id, found_datafile.datafile_id)

    def test_new_platform_added_successfully(self):
        """Test whether a new platform is created successfully or not"""

        with self.store.session_scope():
            platforms = self.store.session.query(self.store.db_classes.Platform).all()

        # there must be no entry at the beginning
        self.assertEqual(len(platforms), 0)

        with self.store.session_scope():
            self.platform = self.store.get_platform(
                platform_name="Test Platform",
                nationality=self.nationality,
                platform_type=self.platform_type,
                privacy=self.privacy,
                change_id=self.change_id,
            )

        # there must be one entry
        with self.store.session_scope():
            platforms = self.store.session.query(self.store.db_classes.Platform).all()

            self.assertEqual(len(platforms), 1)
            self.assertEqual(platforms[0].name, "Test Platform")

    def test_present_platform_not_added(self):
        """Test whether present platform is not created"""

        with self.store.session_scope():
            platforms = self.store.session.query(self.store.db_classes.Platform).all()

        # there must be no entry at the beginning
        self.assertEqual(len(platforms), 0)

        with self.store.session_scope():
            self.platform = self.store.get_platform(
                platform_name="Test Platform",
                nationality=self.nationality,
                platform_type=self.platform_type,
                privacy=self.privacy,
                change_id=self.change_id,
            )
            self.platform = self.store.get_platform(
                platform_name="Test Platform",
                nationality=self.nationality,
                platform_type=self.platform_type,
                privacy=self.privacy,
                change_id=self.change_id,
            )

        # there must be one entry
        with self.store.session_scope():
            platforms = self.store.session.query(self.store.db_classes.Platform).all()

            self.assertEqual(len(platforms), 1)
            self.assertEqual(platforms[0].name, "Test Platform")

    def test_find_platform(self):
        """Test whether find_platform method returns the correct Platform entity"""
        with self.store.session_scope():
            nat1 = self.store.add_to_nationalities("Nat1", self.change_id).name
            nat2 = self.store.add_to_nationalities("Nat2", self.change_id).name
            # Create two platforms with same name
            platform = self.store.get_platform(
                platform_name="Test Platform",
                nationality=nat1,
                identifier="123",
                platform_type=self.platform_type,
                privacy=self.privacy,
                change_id=self.change_id,
            )
            self.store.get_platform(
                platform_name="Test Platform",
                nationality=nat2,
                identifier="123",
                platform_type=self.platform_type,
                privacy=self.privacy,
                change_id=self.change_id,
            )

            found_platform = self.store.find_platform("Test Platform", "Nat1", "123")
            assert found_platform.platform_id == platform.platform_id
            assert "Test Platform" == found_platform.name

    def test_find_platform_synonym(self):
        """Test whether find_platform method finds the correct Platform entity from Synonyms table"""
        with self.store.session_scope():
            nat1 = self.store.add_to_nationalities("Nat1", self.change_id).name
            nat2 = self.store.add_to_nationalities("Nat2", self.change_id).name

            # Create two platforms
            platform = self.store.get_platform(
                platform_name="Test Platform",
                nationality=nat1,
                identifier="123",
                platform_type=self.platform_type,
                privacy=self.privacy,
                change_id=self.change_id,
            )
            self.store.get_platform(
                platform_name="Test Platform",
                nationality=nat2,
                identifier="123",
                platform_type=self.platform_type,
                privacy=self.privacy,
                change_id=self.change_id,
            )
            self.store.add_to_synonyms(
                table=constants.PLATFORM,
                name="TEST",
                entity=platform.platform_id,
                change_id=self.change_id,
            )

            found_platform = self.store.find_platform("TEST", identifier=None, nationality=None)
            self.assertEqual(platform.platform_id, found_platform.platform_id)
            self.assertEqual(found_platform.name, "Test Platform")


@pytest.mark.postgres
class DataStoreStatusTestCase(TestCase):
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
            raise Exception("Testing Postgres server could not be started/accessed")
        try:
            self.store = DataStore(
                db_name="test",
                db_host="localhost",
                db_username="postgres",
                db_password="postgres",
                db_port=55527,
                db_type="postgres",
            )
            self.store.initialise()
            with self.store.session_scope():
                self.store.populate_reference(TEST_DATA_PATH)
                self.store.populate_metadata(TEST_DATA_PATH)
        except OperationalError:
            raise Exception("Creating database schema in testing Postgres database failed")

    def tearDown(self) -> None:
        try:
            self.postgres.stop()
        except AttributeError:
            return

    def test_get_status_of_measurement(self):
        """Test whether summary contents correct for measurement tables"""
        # Add example measurements
        processor = FileProcessor(archive=False)
        processor.load_importers_dynamically()
        processor.process(REP_DATA_PATH, self.store, False)

        with self.store.session_scope():
            table_summary_object = self.store.get_status(TableTypes.MEASUREMENT)
        report = table_summary_object.report()

        assert report != ""
        assert "| States       |                8 |" in report
        assert "| Contacts     |                7 |" in report
        assert "| Comments     |                7 |" in report

    def test_get_status_of_metadata(self):
        """Test whether summary contents correct for metadata tables"""

        with self.store.session_scope():
            table_summary_object = self.store.get_status(TableTypes.METADATA)
        report = table_summary_object.report()

        self.assertNotEqual(report, "")
        self.assertIn("Sensors", report)
        self.assertIn("Platforms", report)
        self.assertIn("Datafiles", report)

    def test_get_status_of_reference(self):
        """Test whether summary contents correct for reference tables"""

        with self.store.session_scope():
            table_summary_object = self.store.get_status(
                TableTypes.REFERENCE, exclude=[constants.HELP_TEXT]
            )
        report = table_summary_object.report()

        self.assertNotEqual(report, "")
        self.assertIn("Nationalities", report)
        self.assertIn("Privacies", report)
        self.assertIn("PlatformTypes", report)


@pytest.mark.postgres
class SensorTestCase(TestCase):
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
            raise Exception("Testing Postgres server could not be started/accessed")
        try:
            self.store = DataStore(
                db_name="test",
                db_host="localhost",
                db_username="postgres",
                db_password="postgres",
                db_port=55527,
                db_type="postgres",
            )
            self.store.initialise()
            with self.store.session_scope():
                self.change_id = self.store.add_to_changes(
                    "TEST", datetime.utcnow(), "TEST"
                ).change_id
                self.nationality = self.store.add_to_nationalities(
                    "test_nationality", self.change_id
                ).name
                self.platform_type = self.store.add_to_platform_types(
                    "test_platform_type", self.change_id
                ).name
                self.sensor_type = self.store.add_to_sensor_types(
                    "test_sensor_type", self.change_id
                ).name
                self.privacy = self.store.add_to_privacies("test_privacy", 0, self.change_id).name

                self.platform = self.store.get_platform(
                    platform_name="Test Platform",
                    nationality=self.nationality,
                    platform_type=self.platform_type,
                    privacy=self.privacy,
                    change_id=self.change_id,
                )
                self.store.session.expunge(self.platform)
        except OperationalError:
            raise Exception("Creating database schema in testing Postgres database failed")

    def tearDown(self) -> None:
        try:
            self.postgres.stop()
        except AttributeError:
            return

    def test_new_sensor_added_successfully(self):
        """Test whether a new sensor is created"""
        with self.store.session_scope():
            sensors = self.store.session.query(self.store.db_classes.Sensor).all()

            # there must be no entry at the beginning
            self.assertEqual(len(sensors), 0)

            self.platform.get_sensor(self.store, "gps", self.sensor_type, change_id=self.change_id)

            # there must be one entry
            sensors = self.store.session.query(self.store.db_classes.Sensor).all()
            self.assertEqual(len(sensors), 1)
            self.assertEqual(sensors[0].name, "gps")

    def test_present_sensor_not_added(self):
        """Test whether present sensor is not created"""
        with self.store.session_scope():
            sensors = self.store.session.query(self.store.db_classes.Sensor).all()

            # there must be no entry at the beginning
            self.assertEqual(len(sensors), 0)

            self.platform.get_sensor(self.store, "gps", self.sensor_type, change_id=self.change_id)

            # try to add the same entity
            self.platform.get_sensor(self.store, "gps", self.sensor_type, change_id=self.change_id)

            # there must be one entry
            sensors = self.store.session.query(self.store.db_classes.Sensor).all()

            self.assertEqual(len(sensors), 1)

    def test_find_sensor(self):
        """Test whether find_sensor method returns the correct Sensor entity"""
        with self.store.session_scope():
            sensors = self.store.session.query(self.store.db_classes.Sensor).all()

            # there must be no entry at the beginning
            self.assertEqual(len(sensors), 0)

            sensor = self.platform.get_sensor(
                self.store, "gps", self.sensor_type, change_id=self.change_id
            )
            self.platform.get_sensor(
                self.store, "gps_2", self.sensor_type, change_id=self.change_id
            )

            found_sensor = self.store.db_classes.Sensor().find_sensor(
                self.store, "gps", self.platform.platform_id
            )
            self.assertEqual(sensor.sensor_id, found_sensor.sensor_id)
            self.assertEqual(found_sensor.name, "gps")


@pytest.mark.postgres
class MeasurementsTestCase(TestCase):
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
            raise Exception("Testing Postgres server could not be started/accessed")
        try:
            self.store = DataStore(
                db_name="test",
                db_host="localhost",
                db_username="postgres",
                db_password="postgres",
                db_port=55527,
                db_type="postgres",
            )
            self.store.initialise()
            with self.store.session_scope():
                self.current_time = datetime.utcnow()
                self.change_id = self.store.add_to_changes(
                    "TEST", self.current_time, "TEST"
                ).change_id
                self.nationality = self.store.add_to_nationalities(
                    "test_nationality", self.change_id
                ).name
                self.platform_type = self.store.add_to_platform_types(
                    "test_platform_type", self.change_id
                ).name
                self.sensor_type = self.store.add_to_sensor_types(
                    "test_sensor_type", self.change_id
                ).name
                self.privacy = self.store.add_to_privacies("test_privacy", 0, self.change_id).name

                self.platform = self.store.get_platform(
                    platform_name="Test Platform",
                    nationality=self.nationality,
                    platform_type=self.platform_type,
                    privacy=self.privacy,
                    change_id=self.change_id,
                )
                self.sensor = self.platform.get_sensor(
                    self.store, "gps", self.sensor_type, change_id=self.change_id
                )
                self.comment_type = self.store.add_to_comment_types("test_type", self.change_id)
                self.file = self.store.get_datafile(
                    "test_file", "csv", 0, "HASHED-1", self.change_id
                )

                self.store.session.expunge(self.sensor)
                self.store.session.expunge(self.platform)
                self.store.session.expunge(self.file)
                self.store.session.expunge(self.comment_type)
        except OperationalError:
            raise Exception("Creating database schema in testing Postgres database failed")

        class TestParser(Importer):
            def __init__(
                self,
                name="Test Importer",
                validation_level=validation_constants.NONE_LEVEL,
                short_name="Test Importer",
                datafile_type="Test",
            ):
                super().__init__(name, validation_level, short_name, datafile_type)
                self.text_label = None
                self.depth = 0.0
                self.errors = list()

            def can_load_this_header(self, header) -> bool:
                return True

            def can_load_this_filename(self, filename):
                return True

            def can_load_this_type(self, suffix):
                return True

            def can_load_this_file(self, file_contents):
                return True

            def _load_this_file(self, data_store, path, file_contents, datafile):
                pass

        self.parser = TestParser()
        self.file.measurements[self.parser.short_name] = dict()

    def tearDown(self) -> None:
        try:
            self.postgres.stop()
        except AttributeError:
            return

    def test_new_state_created_successfully(self):
        """Test whether a new state is created"""
        with self.store.session_scope():
            states = self.store.session.query(self.store.db_classes.State).all()

            # there must be no entry at the beginning
            self.assertEqual(len(states), 0)

            state = self.file.create_state(
                self.store,
                self.platform,
                self.sensor,
                self.current_time,
                parser_name=self.parser.short_name,
            )

            # there must be no entry because it's kept in-memory
            states = self.store.session.query(self.store.db_classes.State).all()
            self.assertEqual(len(states), 0)

            self.assertEqual(state.time, self.current_time)

            if self.file.validate():
                self.file.commit(self.store, self.change_id)
                states = self.store.session.query(self.store.db_classes.State).all()
            self.assertEqual(len(states), 1)

    def test_new_contact_created_successfully(self):
        """Test whether a new contact is created"""

        with self.store.session_scope():
            contacts = self.store.session.query(self.store.db_classes.Contact).all()

            # there must be no entry at the beginning
            self.assertEqual(len(contacts), 0)

            contact = self.file.create_contact(
                self.store,
                self.platform,
                self.sensor,
                self.current_time,
                parser_name=self.parser.short_name,
            )

            # there must be no entry because it's kept in-memory
            contacts = self.store.session.query(self.store.db_classes.Contact).all()
            self.assertEqual(len(contacts), 0)

            # Fill null constraint field
            contact.name = "TEST"
            contact.subject_id = self.platform.platform_id
            if self.file.validate():
                self.file.commit(self.store, self.change_id)
                contacts = self.store.session.query(self.store.db_classes.Contact).all()
                self.assertEqual(len(contacts), 1)

    def test_new_comment_created_successfully(self):
        """Test whether a new comment is created"""

        with self.store.session_scope():
            comments = self.store.session.query(self.store.db_classes.Comment).all()

            # there must be no entry at the beginning
            self.assertEqual(len(comments), 0)

            comment = self.file.create_comment(
                self.store,
                self.platform,
                self.current_time,
                "Comment",
                self.comment_type,
                parser_name=self.parser.short_name,
            )

            # there must be no entry because it's kept in-memory
            comments = self.store.session.query(self.store.db_classes.Comment).all()
            self.assertEqual(len(comments), 0)

            # Fill null constraint field
            comment.platform_id = self.platform.platform_id
            if self.file.validate():
                self.file.commit(self.store, self.change_id)
                comments = self.store.session.query(self.store.db_classes.Comment).all()
                self.assertEqual(len(comments), 1)


@pytest.mark.postgres
class FirstConnectionTestCase(TestCase):
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
            raise Exception("Testing Postgres server could not be started/accessed")

    def tearDown(self) -> None:
        try:
            self.postgres.stop()
        except AttributeError:
            return

    @patch("pepys_import.utils.error_handling.custom_print_formatted_text", side_effect=side_effect)
    def test_data_store_fails_at_the_beginning(self, patched_print):
        temp_output = StringIO()
        with pytest.raises(SystemExit), redirect_stdout(temp_output):
            DataStore(
                db_name="test",
                db_host="localhost",
                db_username="TEST",
                db_password="TEST",
                db_port=55527,
                db_type="postgres",
            )
        output = temp_output.getvalue()
        assert "ERROR: SQL error when communicating with database" in output
        assert "Please check your database file and the config file's database section." in output
        assert (
            "Current database URL: 'postgresql+psycopg2://TEST:TEST@localhost:55527/test'" in output
        )


if __name__ == "__main__":
    unittest.main()
