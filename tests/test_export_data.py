import os
import unittest
from unittest import TestCase

from testing.postgresql import Postgresql

from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor

FILE_PATH = os.path.dirname(__file__)
CURRENT_DIR = os.getcwd()
DATA_PATH = os.path.join(FILE_PATH, "sample_data/track_files/rep_data/rep_test1.rep")


class DataStoreExportPostGISDBTestCase(TestCase):
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
                "100112 115800.000 SUBJECT AA 60 23 40.25 N 000 01 25.86 E 109.08 6.00 0.0" in data
            )
            assert (
                "100112 121400.000 SEARCH_PLATFORM AA 60 28 8.02 N 000 35 59.95 E 179.84 8.00 0.0"
                in data
            )
            assert ";NARRATIVE: 100112 115800.000 SENSOR Contact detected on TA" in data
            assert (
                ";NARRATIVE2: 100112 121200.000 SEARCH_PLATFORM OBSERVATION SUBJECT lost on TA"
                in data
            )
            assert (
                ";SENSOR2: 100112 115800.000 SENSOR @@ NULL 252.85 NULL 123.4 hertz 432.10 SENSOR N/A"
                in data
            )
            assert (
                ";SENSOR: 100112 120000.000 SENSOR @@ 60 15 00 N 016 45 00 E 251.33 NULL SENSOR N/A"
                in data
            )


class DataStoreExportSpatiaLiteTestCase(TestCase):
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
                "100112 115800.000 SUBJECT AA 60 23 40.25 N 000 01 25.86 E 109.08 6.00 0.0" in data
            )
            assert (
                "100112 121400.000 SEARCH_PLATFORM AA 60 28 8.02 N 000 35 59.95 E 179.84 8.00 0.0"
                in data
            )
            assert ";NARRATIVE: 100112 115800.000 SENSOR Contact detected on TA" in data
            assert (
                ";NARRATIVE2: 100112 121200.000 SEARCH_PLATFORM OBSERVATION SUBJECT lost on TA"
                in data
            )
            assert (
                ";SENSOR2: 100112 115800.000 SENSOR @@ NULL 252.85 NULL 123.4 hertz 432.10 SENSOR N/A"
                in data
            )
            assert (
                ";SENSOR: 100112 120000.000 SENSOR @@ 60 15 00 N 016 45 00 E 251.33 NULL SENSOR N/A"
                in data
            )


if __name__ == "__main__":
    unittest.main()
