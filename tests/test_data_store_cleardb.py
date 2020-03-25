import platform
import unittest
from unittest import TestCase

from sqlalchemy import inspect
from testing.postgresql import Postgresql

from pepys_import.core.store.data_store import DataStore


class DataStoreClearContentsPostGISDBTestCase(TestCase):
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

    def test_postgres_cleardb_contents(self):
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
        data_store_postgres.clear_db_contents()

        with data_store_postgres.session_scope():
            records = data_store_postgres.session.query(
                data_store_postgres.db_classes.Nationality
            ).all()

        self.assertEqual(len(records), 0)


class DataStoreClearContentsSpatiaLiteTestCase(TestCase):
    def test_sqlite_cleardb_contents(self):
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
        data_store_sqlite.clear_db_contents()

        with data_store_sqlite.session_scope():
            records = data_store_sqlite.session.query(
                data_store_sqlite.db_classes.Nationality
            ).all()

        self.assertEqual(len(records), 0)


class DataStoreClearSchemaPostGISTestCase(TestCase):
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

    def test_clear_db_schema(self):
        if self.store is None:
            self.skipTest("Postgres is not available. Test is skipping")

        data_store_postgres = DataStore(
            db_username="postgres",
            db_password="postgres",
            db_host="localhost",
            db_port=55527,
            db_name="test",
        )

        # inspector makes it possible to load lists of schema, table, column
        # information for the sqlalchemy engine
        inspector = inspect(data_store_postgres.engine)
        table_names = inspector.get_table_names()
        schema_names = inspector.get_schema_names()

        # there must be no table and no schema for datastore at the beginning
        self.assertEqual(len(table_names), 0)
        self.assertNotIn("pepys", schema_names)

        # creating database from schema
        data_store_postgres.initialise()

        # Clearing schema
        data_store_postgres.clear_db_schema()

        inspector = inspect(data_store_postgres.engine)
        table_names = inspector.get_table_names(schema="pepys")
        schema_names = inspector.get_schema_names()

        # no tables must be left
        self.assertEqual(len(table_names), 0)


class DataStoreClearSchemaSpatiaLiteTestCase(TestCase):
    def test_clear_db_schema(self):
        """Test whether schemas created successfully on SQLite"""
        data_store_sqlite = DataStore("", "", "", 0, ":memory:", db_type="sqlite")

        # inspector makes it possible to load lists of schema, table, column
        # information for the sqlalchemy engine
        inspector = inspect(data_store_sqlite.engine)
        table_names = inspector.get_table_names()

        # there must be no table at the beginning
        self.assertEqual(len(table_names), 0)

        # creating database from schema
        data_store_sqlite.initialise()

        # clear the database schema
        data_store_sqlite.clear_db_schema()

        inspector = inspect(data_store_sqlite.engine)
        table_names = inspector.get_table_names()

        SYSTEM = platform.system()

        if SYSTEM == "Windows":
            correct_n_tables = 38
        else:
            correct_n_tables = 36

        # Only the spatial tables (36, or 38 on Windows) must be created. A few of them tested
        self.assertEqual(len(table_names), correct_n_tables)


if __name__ == "__main__":
    unittest.main()
