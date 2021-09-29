import unittest
from unittest import TestCase

import pytest
from sqlalchemy import inspect
from testing.postgresql import Postgresql

from pepys_import.core.store.data_store import DataStore
from pepys_import.utils.data_store_utils import is_schema_created


@pytest.mark.postgres
class DataStoreInitialisePostGISTestCase(TestCase):
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

    def test_postgres_initialise(self):
        """Test whether schemas created successfully on PostgresSQL"""
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

        inspector = inspect(data_store_postgres.engine)
        table_names = inspector.get_table_names(schema="pepys")
        schema_names = inspector.get_schema_names()

        # 35 tables + alembic_version table must be created to default schema
        self.assertEqual(len(table_names), 41)
        self.assertIn("Platforms", table_names)
        self.assertIn("States", table_names)
        self.assertIn("Datafiles", table_names)
        self.assertIn("Nationalities", table_names)

        # pepys must be created
        self.assertIn("pepys", schema_names)

        # 1 table for spatial objects (spatial_ref_sys) must be created to default schema
        table_names = inspector.get_table_names()
        self.assertEqual(len(table_names), 1)
        self.assertIn("spatial_ref_sys", table_names)

    def test_is_schema_created(self):
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
        assert is_schema_created(data_store_postgres.engine, data_store_postgres.db_type) is False

        data_store_postgres.initialise()
        assert is_schema_created(data_store_postgres.engine, data_store_postgres.db_type) is True

    def test_is_empty(self):
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
        data_store_postgres.initialise()
        with data_store_postgres.session_scope():
            assert data_store_postgres.is_empty() is True
            data_store_postgres.populate_reference()
            assert data_store_postgres.is_empty() is False


class DataStoreInitialiseSpatiaLiteTestCase(TestCase):
    def test_sqlite_initialise(self):
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

        inspector = inspect(data_store_sqlite.engine)
        table_names = inspector.get_table_names()

        # SQLite can have either 78 tables (if using the new version of mod_spatialite)
        # or 76 (with the old stable release of mod_spatialite). The version of mod_spatialiate
        # that is installed can vary by platform - so both numbers should be acceptable.
        assert len(table_names) >= 77 and len(table_names) <= 79

        self.assertIn("Platforms", table_names)
        self.assertIn("States", table_names)
        self.assertIn("Datafiles", table_names)
        self.assertIn("Nationalities", table_names)

        # tables created by Spatialite
        self.assertIn("geometry_columns", table_names)
        self.assertIn("views_geometry_columns", table_names)
        self.assertIn("virts_geometry_columns", table_names)
        self.assertIn("spatialite_history", table_names)

    def test_is_schema_created(self):
        data_store_sqlite = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        assert is_schema_created(data_store_sqlite.engine, data_store_sqlite.db_type) is False

        data_store_sqlite.initialise()
        assert is_schema_created(data_store_sqlite.engine, data_store_sqlite.db_type) is True

    def test_is_empty(self):
        data_store_sqlite = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        data_store_sqlite.initialise()

        with data_store_sqlite.session_scope():
            assert data_store_sqlite.is_empty() is True
            data_store_sqlite.populate_reference()
            assert data_store_sqlite.is_empty() is False


if __name__ == "__main__":
    unittest.main()
