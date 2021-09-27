import unittest
from unittest import TestCase

import pytest
from sqlalchemy import inspect
from testing.postgresql import Postgresql

from pepys_import.core.store.data_store import DataStore


@pytest.mark.postgres
class DataStoreClearContentsPostGISDBTestCase(TestCase):
    def setUp(self):
        self.store = None
        try:
            self.store = Postgresql(
                database="test",
                host="localhost",
                user="postgres",
                password="postgres",
                port=55527,
            )
        except RuntimeError:
            raise Exception("Creating database schema in testing Postgres database failed")

    def tearDown(self):
        try:
            self.store.stop()
        except AttributeError:
            return

    def test_postgres_clear_db_contents(self):
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
    def test_sqlite_clear_db_contents(self):
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


@pytest.mark.postgres
class DataStoreClearSchemaPostGISTestCase(TestCase):
    def setUp(self):
        self.store = None
        try:
            self.store = Postgresql(
                database="test",
                host="localhost",
                user="postgres",
                password="postgres",
                port=55527,
            )
        except RuntimeError:
            raise Exception("Creating database schema in testing Postgres database failed")

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
            db_type="postgres",
        )

        # inspector makes it possible to load lists of schema, table, column
        # information for the sqlalchemy engine
        inspector = inspect(data_store_postgres.engine)
        table_names = inspector.get_table_names()
        schema_names = inspector.get_schema_names()

        # there must be no normal Pepys tables at the beginning
        # but because we've already initialised PostGIS, there will be one table
        # which is the PostGIS spatial reference systems table
        self.assertEqual(len(table_names), 1)
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

        # Only the spatial tables should be created. The number of these varies depending on the version
        # of spatialite: either 38 for the later version or 36 for the previous version
        # On Windows we only support the pre-release version, so we get 38, but this can also happen on
        # other systems depending on configuration
        assert len(table_names) == 38 or len(table_names) == 36


if __name__ == "__main__":
    unittest.main()
