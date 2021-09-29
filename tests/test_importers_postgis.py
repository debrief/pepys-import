import os
import unittest
from unittest.mock import patch

import pytest
from sqlalchemy.exc import OperationalError
from testing.postgresql import Postgresql

from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor

FILE_PATH = os.path.dirname(__file__)
CURRENT_DIR = os.getcwd()
BAD_DATA_PATH = os.path.join(FILE_PATH, "sample_data_bad")
DATA_PATH = os.path.join(FILE_PATH, "sample_data")
OUTPUT_PATH = os.path.join(DATA_PATH, "output")


@pytest.mark.postgres
class SampleImporterTestCase(unittest.TestCase):
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
        except OperationalError:
            raise Exception("Creating database schema in testing Postgres database failed")

    def tearDown(self) -> None:
        try:
            self.postgres.stop()
        except AttributeError:
            return

    def test_process_folders_not_descending(self):
        """Test whether single level processing works for the given path"""
        processor = FileProcessor("single_level.db", archive=False)

        processor.load_importers_dynamically()

        # try bad file
        exception = False
        try:
            processor.process(BAD_DATA_PATH, self.store, False)
        except FileNotFoundError:
            exception = True
        self.assertTrue(exception)

        # now good one
        processor.process(DATA_PATH, self.store, False)

    @patch("pepys_import.core.store.common_db.prompt", return_value="2")
    def test_process_folders_descending(self, patched_prompt):
        """Test whether descending processing works for the given path"""
        processor = FileProcessor("descending.db", archive=False)

        processor.load_importers_dynamically()

        # try bad file
        exception = False
        try:
            processor.process(BAD_DATA_PATH, self.store, True)
        except FileNotFoundError:
            exception = True
        self.assertTrue(exception)

        # now good one
        processor.process(DATA_PATH, self.store, True)


if __name__ == "__main__":
    unittest.main()
