import unittest
from unittest import TestCase

from testing.postgresql import Postgresql

from pepys_import.core.store.data_store import DataStore


class DataStoreExportPostGISDBTestCase(TestCase):
    def setUp(self):
        self.store = None
        try:
            self.store = Postgresql(
                database="test", host="localhost", user="postgres", password="postgres", port=55527,
            )
        except RuntimeError:
            print("PostgreSQL database couldn't be created! Test is skipping.")

    def tearDown(self):
        try:
            self.store.stop()
        except AttributeError:
            return

    def test_postgres_cleardb(self):
        """Test whether all database tables are empty"""
        if self.store is None:
            self.skipTest("Postgres is not available. Test is skipping")

        data_store_postgres = DataStore(
            db_username="postgres",
            db_password="postgres",
            db_host="localhost",
            db_port=55527,
            db_name="test",
            db_type="postgres",
        )

        # creating database from schema
        data_store_postgres.initialise()

        with data_store_postgres.session_scope():
            # populate data
            data_store_postgres.populate_reference()
            data_store_postgres.populate_metadata()
            data_store_postgres.populate_measurement()

            datafiles = data_store_postgres.get_all_datafiles()
            datafiles_dict = {}
            for datafile in datafiles:
                datafiles_dict[datafile.reference] = datafile.datafile_id
        datafile_reference = "DATAFILE-1"
        selected_datafile_id = datafiles_dict[datafile_reference]
        with data_store_postgres.session_scope():
            data_store_postgres.export_datafile(selected_datafile_id, datafile_reference)

        # self.assertNotEqual(len(records), 0)


class DataStoreExportSpatiaLiteTestCase(TestCase):
    def test_sqlite_cleardb(self):
        """Test whether all database tables are empty"""
        data_store_sqlite = DataStore("", "", "", 0, ":memory:", db_type="sqlite")

        # creating database from schema
        data_store_sqlite.initialise()

        with data_store_sqlite.session_scope():
            # populate data
            data_store_sqlite.populate_reference()
            data_store_sqlite.populate_metadata()
            data_store_sqlite.populate_measurement()

        with data_store_sqlite.session_scope():
            datafiles = data_store_sqlite.get_all_datafiles()
            datafiles_dict = {}
            for datafile in datafiles:
                datafiles_dict[datafile.reference] = datafile.datafile_id
        datafile_reference = "DATAFILE-1"
        selected_datafile_id = datafiles_dict[datafile_reference]
        with data_store_sqlite.session_scope():
            data_store_sqlite.export_datafile(selected_datafile_id, datafile_reference)

        # self.assertNotEqual(len(records), 0)


if __name__ == "__main__":
    unittest.main()
