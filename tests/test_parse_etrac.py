import os
import unittest
from sqlite3 import OperationalError

from pepys_import.file.e_trac_importer import ETracImporter
from pepys_import.file.file_processor import FileProcessor
from pepys_import.core.store.data_store import DataStore
from testing.postgresql import Postgresql
from sqlalchemy import event
from pepys_import.core.store.db_base import BasePostGIS
from sqlalchemy.sql.ddl import DropSchema

FILE_PATH = os.path.dirname(__file__)
DATA_PATH = os.path.join(FILE_PATH, "sample_data/track_files/other_data")
TEST_DATA_PATH = os.path.join(FILE_PATH, "sample_data", "csv_files")


class ETracTests(unittest.TestCase):
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

    def test_process_e_trac_data(self):
        processor = FileProcessor()
        processor.register_importer(ETracImporter())

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
        processor.process(DATA_PATH, self.store, False)

        # check data got created
        with self.store.session_scope():
            # there must be states after the import
            states = self.store.session.query(self.store.db_classes.State).all()
            self.assertEqual(len(states), 85)

            # there must be platforms after the import
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            self.assertEqual(len(platforms), 18)

            # there must be one datafile afterwards
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 2)


if __name__ == "__main__":
    unittest.main()
