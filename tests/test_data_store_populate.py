import os
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest import TestCase
from unittest.mock import patch

import pytest
from sqlalchemy.exc import OperationalError
from testing.postgresql import Postgresql

from pepys_import.core.store.data_store import DataStore

FILE_PATH = os.path.dirname(__file__)
TEST_DATA_PATH = os.path.join(FILE_PATH, "sample_data", "csv_files")
NOT_IMPLEMENTED_PATH = os.path.join(
    FILE_PATH, "sample_data", "csv_files", "for_not_implemented_methods"
)
MISSING_DATA_PATH = os.path.join(FILE_PATH, "sample_data", "csv_files", "missing_data")
SYNONYM_DATA_PATH = os.path.join(FILE_PATH, "sample_data", "csv_files", "for_synonym_tests")
SYNONYM_DATA_PATH_BAD = os.path.join(FILE_PATH, "sample_data", "csv_files", "for_synonym_tests_bad")
WRONG_HEADER_NAME_PATH = os.path.join(
    FILE_PATH, "sample_data", "csv_files", "for_wrong_header_names"
)
WRONG_SYNONYM_HEADER_NAME_PATH = os.path.join(
    FILE_PATH, "sample_data", "csv_files", "for_wrong_synonym_header"
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
        with self.store.session_scope():
            nationalities = self.store.session.query(self.store.db_classes.Nationality).all()
            platform_types = self.store.session.query(self.store.db_classes.PlatformType).all()

        # There must be no entities at the beginning
        self.assertEqual(len(nationalities), 0)
        self.assertEqual(len(platform_types), 0)

        # Import CSVs to the related tables
        with self.store.session_scope():
            self.store.populate_reference()

        # Check tables filled with correct data
        with self.store.session_scope():
            nationalities = self.store.session.query(self.store.db_classes.Nationality).all()
            platform_types = self.store.session.query(self.store.db_classes.PlatformType).all()
            nationality_object = self.store.search_nationality("United Kingdom")
            platform_type_object = self.store.search_platform_type("PLATFORM-TYPE-1")

            # Check whether they are not empty anymore and filled with correct data
            self.assertNotEqual(len(nationalities), 0)
            self.assertNotEqual(len(platform_types), 0)

            self.assertIn(nationality_object.name, "United Kingdom")
            self.assertIn(platform_type_object.name, "PLATFORM-TYPE-1")

            geo_types = self.store.session.query(self.store.db_classes.GeometryType).all()
            geo_sub_types = self.store.session.query(self.store.db_classes.GeometrySubType).all()
            geo_type_obj = self.store.search_geometry_type("GEOMETRY-1")
            geo_sub_type_obj = self.store.search_geometry_sub_type(
                "GEO-SUB-1", geo_type_obj.geo_type_id
            )

            self.assertNotEqual(len(geo_types), 0)
            self.assertNotEqual(len(geo_sub_types), 0)

            self.assertIn(geo_type_obj.name, "GEOMETRY-1")
            self.assertIn(geo_sub_type_obj.name, "GEO-SUB-1")

    def test_populate_metadata(self):
        # reference tables must be filled first
        with self.store.session_scope():
            self.store.populate_reference()

        # get all table values
        with self.store.session_scope():
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            sensors = self.store.session.query(self.store.db_classes.Sensor).all()

        # There must be no entities at the beginning
        self.assertEqual(len(platforms), 0)
        self.assertEqual(len(datafiles), 0)
        self.assertEqual(len(sensors), 0)

        # Import CSVs to the related tables
        with self.store.session_scope():
            self.store.populate_metadata()

        with self.store.session_scope():
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            sensors = self.store.session.query(self.store.db_classes.Sensor).all()

            platform_object = self.store.search_platform("PLATFORM-1", "United Kingdom", "123")
            datafile_object = self.store.search_datafile("DATAFILE-1")
            sensor_object = self.store.search_sensor("SENSOR-1", platform_object.platform_id)

            # Check whether they are not empty anymore and filled with correct data
            self.assertNotEqual(len(platforms), 0)
            self.assertNotEqual(len(datafiles), 0)
            self.assertNotEqual(len(sensors), 0)

            # The following assertions filter objects by foreign key ids and
            # compares values with the data from CSV

            # Platform Object: PLATFORM-1, UNITED KINGDOM, TYPE-1, Public
            nationality = (
                self.store.session.query(self.store.db_classes.Nationality)
                .filter_by(nationality_id=platform_object.nationality_id)
                .first()
            )
            self.assertEqual(nationality.name, "United Kingdom")
            platform_type = (
                self.store.session.query(self.store.db_classes.PlatformType)
                .filter_by(platform_type_id=platform_object.platform_type_id)
                .first()
            )
            self.assertEqual(platform_type.name, "PLATFORM-TYPE-1")
            privacy = (
                self.store.session.query(self.store.db_classes.Privacy)
                .filter_by(privacy_id=platform_object.privacy_id)
                .first()
            )
            self.assertEqual(privacy.name, "Public")

            # Datafile Object: DATAFILE-1, True, Public, DATAFILE-TYPE-1
            self.assertEqual(datafile_object.simulated, True)
            privacy = (
                self.store.session.query(self.store.db_classes.Privacy)
                .filter_by(privacy_id=datafile_object.privacy_id)
                .first()
            )
            self.assertEqual(privacy.name, "Public")
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


@pytest.mark.postgres
class DataStorePopulatePostGISTestCase(TestCase):
    def setUp(self) -> None:
        self.postgres = None
        self.store = None
        try:
            self.postgres = Postgresql(
                database="test", host="localhost", user="postgres", password="postgres", port=55527,
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
                db_type="postgres",
            )
            self.store.initialise()
        except OperationalError:
            print("Database schema and data population failed! Test is skipping.")

    def tearDown(self) -> None:
        try:
            self.postgres.stop()
        except AttributeError:
            return

    def test_populate_reference(self):
        """Test whether CSVs successfully imported to PostGIS"""

        # Check tables are created but empty
        with self.store.session_scope():
            nationalities = self.store.session.query(self.store.db_classes.Nationality).all()
            platform_types = self.store.session.query(self.store.db_classes.PlatformType).all()

        # There must be no entities at the beginning
        self.assertEqual(len(nationalities), 0)
        self.assertEqual(len(platform_types), 0)

        # Import CSVs to the related tables
        with self.store.session_scope():
            self.store.populate_reference()

        # Check tables filled with correct data
        with self.store.session_scope():
            nationalities = self.store.session.query(self.store.db_classes.Nationality).all()
            platform_types = self.store.session.query(self.store.db_classes.PlatformType).all()
            nationality_object = self.store.search_nationality("United Kingdom")
            platform_type_object = self.store.search_platform_type("PLATFORM-TYPE-1")

            # Check whether they are not empty anymore and filled with correct data
            self.assertNotEqual(len(nationalities), 0)
            self.assertNotEqual(len(platform_types), 0)

            self.assertIn(nationality_object.name, "United Kingdom")
            self.assertIn(platform_type_object.name, "PLATFORM-TYPE-1")

            geo_types = self.store.session.query(self.store.db_classes.GeometryType).all()
            geo_sub_types = self.store.session.query(self.store.db_classes.GeometrySubType).all()
            geo_type_obj = self.store.search_geometry_type("GEOMETRY-1")
            geo_sub_type_obj = self.store.search_geometry_sub_type(
                "GEO-SUB-1", geo_type_obj.geo_type_id
            )

            self.assertNotEqual(len(geo_types), 0)
            self.assertNotEqual(len(geo_sub_types), 0)

            self.assertIn(geo_type_obj.name, "GEOMETRY-1")
            self.assertIn(geo_sub_type_obj.name, "GEO-SUB-1")

    def test_populate_metadata(self):
        # reference tables must be filled first
        with self.store.session_scope():
            self.store.populate_reference()

        # get all table values
        with self.store.session_scope():
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            sensors = self.store.session.query(self.store.db_classes.Sensor).all()

        # There must be no entities at the beginning
        self.assertEqual(len(platforms), 0)
        self.assertEqual(len(datafiles), 0)
        self.assertEqual(len(sensors), 0)

        # Import CSVs to the related tables
        with self.store.session_scope():
            self.store.populate_metadata()

        with self.store.session_scope():
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            sensors = self.store.session.query(self.store.db_classes.Sensor).all()

            platform_object = self.store.search_platform("PLATFORM-1", "United Kingdom", "123")
            datafile_object = self.store.search_datafile("DATAFILE-1")
            sensor_object = self.store.search_sensor("SENSOR-1", platform_object.platform_id)

            # Check whether they are not empty anymore and filled with correct data
            self.assertNotEqual(len(platforms), 0)
            self.assertNotEqual(len(datafiles), 0)
            self.assertNotEqual(len(sensors), 0)

            # The following assertions filter objects by foreign key ids and
            # compares values with the data from CSV

            # Platform Object: PLATFORM-1, UNITED KINGDOM, TYPE-1, Public
            nationality = (
                self.store.session.query(self.store.db_classes.Nationality)
                .filter_by(nationality_id=platform_object.nationality_id)
                .first()
            )
            self.assertEqual(nationality.name, "United Kingdom")
            platform_type = (
                self.store.session.query(self.store.db_classes.PlatformType)
                .filter_by(platform_type_id=platform_object.platform_type_id)
                .first()
            )
            self.assertEqual(platform_type.name, "PLATFORM-TYPE-1")
            privacy = (
                self.store.session.query(self.store.db_classes.Privacy)
                .filter_by(privacy_id=platform_object.privacy_id)
                .first()
            )
            self.assertEqual(privacy.name, "Public")

            # Datafile Object: DATAFILE-1, True, Public, DATAFILE-TYPE-1
            self.assertEqual(datafile_object.simulated, True)
            privacy = (
                self.store.session.query(self.store.db_classes.Privacy)
                .filter_by(privacy_id=datafile_object.privacy_id)
                .first()
            )
            self.assertEqual(privacy.name, "Public")
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
        with self.store.session_scope():
            temp_output = StringIO()
            with redirect_stdout(temp_output):
                self.store.populate_reference(NOT_IMPLEMENTED_PATH)
            output = temp_output.getvalue()
            self.assertIn("Method(add_to_confidence_levels) not found!", output)

    def test_populate_metadata(self):
        with self.store.session_scope():
            temp_output = StringIO()
            with redirect_stdout(temp_output):
                self.store.populate_reference(NOT_IMPLEMENTED_PATH)
                self.store.populate_metadata(NOT_IMPLEMENTED_PATH)
            output = temp_output.getvalue()
            self.assertIn("Method(add_to_confidence_levels) not found!", output)
            self.assertIn("Method(add_to_tags) not found!", output)


class DataStorePopulateMissingData(TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

        with self.store.session_scope():
            self.store.populate_reference()

    def tearDown(self):
        pass

    def test_populate_missing_data(self):
        with self.store.session_scope():
            temp_output = StringIO()
            with redirect_stdout(temp_output):
                self.store.populate_metadata(MISSING_DATA_PATH)
            output = temp_output.getvalue()

            assert (
                "Error importing row ['PRIVACY-Blah', 'DATAFILE-TYPE-1', 'DATAFILE-1', 'True', '0', 'HASHED-1', ''] from Datafiles.csv"
                in output
            )
            assert "  Error was 'Privacy is invalid/missing'" in output

            assert (
                "Error importing row ['PLATFORM-2', '234', 'MissingNationality', 'PLATFORM-TYPE-2', 'Public Sensitive'] from Platforms.csv"
                in output
            )
            assert "  Error was 'Nationality is invalid/missing'" in output

            assert (
                "Error importing row ['SENSOR-2', 'SENSOR-TYPE-2', 'MissingPlatform', 'France', '234', 'Public Sensitive'] from Sensors.csv"
                in output
            )
            assert "  Error was 'Host is missing/invalid'" in output


class DataStorePopulateSynonyms(TestCase):
    def setUp(self):
        if os.path.exists("synonyms.sqlite"):
            os.remove("synonyms.sqlite")

        self.store = DataStore("", "", "", 0, "synonyms.sqlite", db_type="sqlite")
        self.store.initialise()

        with self.store.session_scope():
            self.store.populate_reference()

    def tearDown(self):
        pass

    @patch("pepys_import.resolvers.command_line_input.prompt", return_value="1")
    def test_populate_synonyms_valid(self, ptk_prompt):
        with self.store.session_scope():
            self.store.populate_reference(SYNONYM_DATA_PATH)
            self.store.populate_metadata(SYNONYM_DATA_PATH)

        with self.store.session_scope():
            synonyms = self.store.session.query(self.store.db_classes.Synonym).all()

            # We imported 4 synonyms
            assert len(synonyms) == 4

            # Check all synonym entity IDs exist in the Platforms table
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            platform_ids = [platform.platform_id for platform in platforms]

            for synonym in synonyms:
                assert synonym.entity in platform_ids

            # Check the ID for the Synonym PLATFORM-Duplicated-Synonym is the ID for
            # the Platform with name Platform-DuplicatedName and identifier F239
            platforms = (
                self.store.session.query(self.store.db_classes.Platform)
                .filter(self.store.db_classes.Platform.name == "PLATFORM-DuplicatedName")
                .filter(self.store.db_classes.Platform.identifier == "F239")
                .all()
            )

            platform_guid = platforms[0].platform_id

            synonyms = (
                self.store.session.query(self.store.db_classes.Synonym)
                .filter(self.store.db_classes.Synonym.synonym == "PLATFORM-Duplicated-Synonym")
                .all()
            )

            assert synonyms[0].entity == platform_guid

    @patch("pepys_import.resolvers.command_line_input.prompt", return_value=".")
    def test_populate_synonyms_valid_exit(self, ptk_prompt):
        with self.store.session_scope():
            self.store.populate_reference(SYNONYM_DATA_PATH)
            with pytest.raises(SystemExit):
                self.store.populate_metadata(SYNONYM_DATA_PATH)

        with self.store.session_scope():
            synonyms = self.store.session.query(self.store.db_classes.Synonym).all()

            # We imported 3 synonyms because it was cancelled on the 4th one
            assert len(synonyms) == 3

    @patch("pepys_import.resolvers.command_line_input.prompt", return_value="3")
    def test_populate_synonyms_valid_skip(self, ptk_prompt):
        with self.store.session_scope():
            self.store.populate_reference(SYNONYM_DATA_PATH)
            temp_output = StringIO()
            with redirect_stdout(temp_output):
                self.store.populate_metadata(SYNONYM_DATA_PATH)
            output = temp_output.getvalue()

        assert "Skipping row" in output

        with self.store.session_scope():
            synonyms = self.store.session.query(self.store.db_classes.Synonym).all()

            # We imported 3 synonyms because we skipped the 4th one
            assert len(synonyms) == 3

    def test_populate_synonyms_invalid(self):
        with self.store.session_scope():
            temp_output = StringIO()
            with redirect_stdout(temp_output):
                self.store.populate_reference(SYNONYM_DATA_PATH_BAD)
                self.store.populate_metadata(SYNONYM_DATA_PATH_BAD)
            output = temp_output.getvalue()

        # Check for error messages about duplicated platform name
        assert "Error on row ['Blah', 'InvalidTables', 'BlahName']" in output
        assert "  Invalid table name InvalidTables" in output

        assert "Error on row ['Blah', 'Participants', 'BlahName']" in output
        assert "  Cannot find name column for table Participants" in output

        assert "Error on row ['PLATFORM-1-Synonym2', 'Platforms', 'NonExistentPlatform']" in output
        assert "  Name 'NonExistentPlatform' is not found in table Platforms" in output

        assert "Error on row ['Datafile1-Synonym', 'Datafiles', 'Datafile-Duplicated']" in output
        assert "Name 'Datafile-Duplicated' occurs multiple times in table Datafiles. Asking user to resolve is only supported for Platforms table."


class DataStorePopulateTwice(TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_populate_twice(self):
        with self.store.session_scope():
            self.store.populate_reference(TEST_DATA_PATH)
            self.store.populate_metadata(TEST_DATA_PATH)

        with self.store.session_scope():
            # Check number of entries in a couple of tables
            platforms = self.store.session.query(self.store.db_classes.Platform).all()

            assert len(platforms) == 2

            sensor_types = self.store.session.query(self.store.db_classes.SensorType).all()

            assert len(sensor_types) == 3

        # Load again
        with self.store.session_scope():
            self.store.populate_reference(TEST_DATA_PATH)
            self.store.populate_metadata(TEST_DATA_PATH)

        # Check number of entries is the same
        with self.store.session_scope():
            platforms = self.store.session.query(self.store.db_classes.Platform).all()

            assert len(platforms) == 2

            sensor_types = self.store.session.query(self.store.db_classes.SensorType).all()

            assert len(sensor_types) == 3


class CSVHeadersTestCase(TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_wrong_header_name(self):
        temp_output = StringIO()
        with self.store.session_scope(), redirect_stdout(temp_output):
            self.store.populate_reference(WRONG_HEADER_NAME_PATH)
        output = temp_output.getvalue()
        assert "Headers and the arguments of DataStore.add_to_sensor_types() don't match!" in output
        assert "Possible arguments: name,change_id" in output
        assert "Please check your CSV file." in output

    def test_wrong_header_name_synonym(self):
        temp_output = StringIO()
        with self.store.session_scope(), redirect_stdout(temp_output):
            self.store.populate_reference()
            self.store.populate_metadata(WRONG_SYNONYM_HEADER_NAME_PATH)
        output = temp_output.getvalue()
        assert "Headers of the Synonyms.csv file are wrong or missing!" in output
        assert "Necessary arguments: synonym,table,target_name" in output
        assert "Please check your CSV file." in output


if __name__ == "__main__":
    unittest.main()
