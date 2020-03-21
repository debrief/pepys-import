import unittest

from pepys_import.core.store.data_store import DataStore
from testing.postgresql import Postgresql
from unittest import TestCase


class DataStoreClearPostGISDBTestCase(TestCase):
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
        )

        with data_store_postgres.session_scope():
            # creating database from schema
            data_store_postgres.initialise()

            # populate reference tables
            data_store_postgres.populate_reference()

            records = data_store_postgres.session.query(
                data_store_postgres.db_classes.Nationality
            ).all()

        self.assertNotEqual(len(records), 0)

        # Clear records from all tables
        data_store_postgres.clear_db()

        with data_store_postgres.session_scope():
            records = data_store_postgres.session.query(
                data_store_postgres.db_classes.Nationality
            ).all()

        self.assertEqual(len(records), 0)


class DataStoreClearSpatiaLiteTestCase(TestCase):
    def test_sqlite_cleardb(self):
        """Test whether all database tables are empty"""
        data_store_sqlite = DataStore("", "", "", 0, ":memory:", db_type="sqlite")

        with data_store_sqlite.session_scope():
            # creating database from schema
            data_store_sqlite.initialise()

            # populate Nationality Table
            data_store_sqlite.populate_reference()

            records = data_store_sqlite.session.query(
                data_store_sqlite.db_classes.Nationality
            ).all()

        self.assertNotEqual(len(records), 0)

        # Clear records from all tables
        data_store_sqlite.clear_db()

        with data_store_sqlite.session_scope():
            records = data_store_sqlite.session.query(
                data_store_sqlite.db_classes.Nationality
            ).all()

        self.assertEqual(len(records), 0)


if __name__ == "__main__":
    unittest.main()
