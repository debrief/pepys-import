import os
import unittest

import pytest
from testing.postgresql import Postgresql

from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor

FILE_PATH = os.path.dirname(__file__)
CURRENT_DIR = os.getcwd()
DATA_PATH = os.path.join(FILE_PATH, "sample_data/track_files/rep_data/rep_test1.rep")


class DataStoreExportPostGISDBTestCase(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(CURRENT_DIR, "export_test.rep")
        self.store = None
        try:
            self.store = Postgresql(
                database="test", host="localhost", user="postgres", password="postgres", port=55527,
            )
        except RuntimeError:
            print("PostgreSQL database couldn't be created! Test is skipping.")

    def tearDown(self) -> None:
        if os.path.exists(self.path):
            os.remove(self.path)
        try:
            self.store.stop()
        except AttributeError:
            return

    def test_postgres_export_datafile(self):
        if self.store is None:
            self.skipTest("Postgres is not available. Test is skipping")

        data_store = DataStore(
            db_username="postgres",
            db_password="postgres",
            db_host="localhost",
            db_port=55527,
            db_name="test",
            db_type="postgres",
        )
        data_store.initialise()

        # Parse the file
        processor = FileProcessor(archive=False)
        processor.load_importers_dynamically()
        processor.process(DATA_PATH, data_store, False)

        with data_store.session_scope():
            datafiles = data_store.get_all_datafiles()
            selected_datafile_id = datafiles[0].datafile_id
            data_store.export_datafile(selected_datafile_id, self.path)

            # Fetch data from the exported file
            with open(self.path, "r") as file:
                data = file.read().split("\n")

            assert (
                "100112 115800.000\tSUBJECT\tAA\t60 23 40.25 N\t000 01 25.86 E\t109.08\t6.00\t0.0"
                in data
            )
            assert (
                "100112 115800.000\tSEARCH_PLATFORM\tAA\t60 28 56.02 N\t000 35 59.68 E\t179.84\t8.00\t0.0"
                in data
            )
            assert ";NARRATIVE:\t100112 115800.000\tSENSOR\tContact detected on TA" in data
            assert (
                ";NARRATIVE2:\t100112 121200.000\tSEARCH_PLATFORM\tOBSERVATION\tSUBJECT lost on TA"
                in data
            )
            assert (
                ";SENSOR2:\t100112 115800.000\tSENSOR\t@@\tNULL\t252.85\tNULL\t123.4\t432.10\tSENSOR\tN/A"
                in data
            )
            assert (
                ";SENSOR:\t100112 120200.000\tSENSOR\t@@\tNULL\t251.58\tNULL\tSENSOR\tN/A" in data
            )


class DataStoreExportSpatiaLiteTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.path = os.path.join(CURRENT_DIR, "export_test.rep")
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

        # Parse the file
        processor = FileProcessor(archive=False)
        processor.load_importers_dynamically()
        processor.process(DATA_PATH, self.store, False)

    def tearDown(self) -> None:
        if os.path.exists(self.path):
            os.remove(self.path)

    def test_sqlite_export_datafile(self):
        with self.store.session_scope():
            datafiles = self.store.get_all_datafiles()
            selected_datafile_id = datafiles[0].datafile_id
            self.store.export_datafile(selected_datafile_id, self.path)

            # Fetch data from the exported file
            with open(self.path, "r") as file:
                data = file.read().split("\n")

            assert (
                "100112 115800.000\tSUBJECT\tAA\t60 23 40.25 N\t000 01 25.86 E\t109.08\t6.00\t0.0"
                in data
            )
            assert (
                "100112 115800.000\tSEARCH_PLATFORM\tAA\t60 28 56.02 N\t000 35 59.68 E\t179.84\t8.00\t0.0"
                in data
            )
            assert ";NARRATIVE:\t100112 115800.000\tSENSOR\tContact detected on TA" in data
            assert (
                ";NARRATIVE2:\t100112 121200.000\tSEARCH_PLATFORM\tOBSERVATION\tSUBJECT lost on TA"
                in data
            )
            assert (
                ";SENSOR2:\t100112 115800.000\tSENSOR\t@@\tNULL\t252.85\tNULL\t123.4\t432.10\tSENSOR\tN/A"
                in data
            )
            assert (
                ";SENSOR:\t100112 120200.000\tSENSOR\t@@\tNULL\t251.58\tNULL\tSENSOR\tN/A" in data
            )


class CachePlatformAndSensorNamesTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.path = os.path.join(CURRENT_DIR, "export_test.rep")
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

        # Parse the file
        processor = FileProcessor(archive=False)
        processor.load_importers_dynamically()
        processor.process(DATA_PATH, self.store, False)

    def test_cached_comment_type_exception(self):
        with self.store.session_scope():
            with pytest.raises(Exception) as exception:
                self.store.get_cached_comment_type_name(comment_type_id=123456789)
            assert f"No Comment Type found with Comment type id: 123456789" in str(exception.value)

    def test_cached_sensor_name_exception(self):
        with self.store.session_scope():
            with pytest.raises(Exception) as exception:
                self.store.get_cached_sensor_name(sensor_id=123456789)
            assert f"No Sensor found with sensor id: 123456789" in str(exception.value)

    def test_cached_platform_name_exceptions(self):
        with self.store.session_scope():
            with pytest.raises(Exception) as exception:
                self.store.get_cached_platform_name()
            assert (
                f"Either 'sensor_id' or 'platform_id' has to be provided to get 'platform name'"
                in str(exception.value)
            )
            with pytest.raises(Exception) as exception:
                self.store.get_cached_platform_name(sensor_id=123456789)
            assert f"No Sensor found with sensor id: 123456789" in str(exception.value)
            with pytest.raises(Exception) as exception:
                self.store.get_cached_platform_name(platform_id=123456789)
            assert f"No Platform found with platform id: 123456789" in str(exception.value)


if __name__ == "__main__":
    unittest.main()
