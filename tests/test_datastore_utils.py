import json
import os
import re
import unittest

import pytest
from sqlalchemy.sql.expression import text
from testing.postgresql import Postgresql

from paths import MIGRATIONS_DIRECTORY
from pepys_import.core.store.data_store import DataStore
from pepys_import.utils.data_store_utils import create_alembic_version_table

with open(os.path.join(MIGRATIONS_DIRECTORY, "latest_revisions.json"), "r") as file:
    versions = json.load(file)


def test_create_alembic_version_empty_db():
    ds = DataStore("", "", "", 0, ":memory:", db_type="sqlite")

    create_alembic_version_table(ds.engine, ds.db_type)

    with ds.engine.connect() as connection:
        results = connection.execute(text("SELECT * FROM alembic_version;")).fetchall()

        assert len(results) == 1
        assert results[0][0] == versions["LATEST_SQLITE_VERSION"]


def test_create_alembic_version_table_empty():
    ds = DataStore("", "", "", 0, ":memory:", db_type="sqlite")

    # Create table and stamp version
    create_alembic_version_table(ds.engine, ds.db_type)

    # Delete all entries, so table is empty
    with ds.engine.connect() as connection:
        connection.execute(text("DELETE FROM alembic_version;"))

    # Now run function
    create_alembic_version_table(ds.engine, ds.db_type)

    # Check it has one entry and it's the right one
    with ds.engine.connect() as connection:
        results = connection.execute(text("SELECT * FROM alembic_version;")).fetchall()

        assert len(results) == 1
        assert results[0][0] == versions["LATEST_SQLITE_VERSION"]


def test_create_alembic_version_already_at_latest_version():
    ds = DataStore("", "", "", 0, ":memory:", db_type="sqlite")

    # Run once to create the table and stamp latest version, then run again
    create_alembic_version_table(ds.engine, ds.db_type)

    create_alembic_version_table(ds.engine, ds.db_type)

    with ds.engine.connect() as connection:
        results = connection.execute(text("SELECT * FROM alembic_version;")).fetchall()

        assert len(results) == 1
        assert results[0][0] == versions["LATEST_SQLITE_VERSION"]


def test_create_alembic_version_at_old_version():
    ds = DataStore("", "", "", 0, ":memory:", db_type="sqlite")

    # Run once to create the table and stamp latest version
    create_alembic_version_table(ds.engine, ds.db_type)

    with ds.engine.connect() as connection:
        connection.execute(text("UPDATE alembic_version SET version_num = 'old_version_id';"))

    with pytest.raises(
        ValueError,
        match=re.escape(
            "Database revision in alembic_version table (old_version_id) does not match latest revision"
        ),
    ):
        create_alembic_version_table(ds.engine, ds.db_type)


def test_create_alembic_version_multiple_rows():
    ds = DataStore("", "", "", 0, ":memory:", db_type="sqlite")

    # Run once to create the table and stamp latest version
    create_alembic_version_table(ds.engine, ds.db_type)

    with ds.engine.connect() as connection:
        connection.execute(text("INSERT INTO alembic_version VALUES ('new_entry');"))

    with pytest.raises(
        ValueError,
        match=re.escape(
            "Multiple rows detected in alembic_version table. Database potentially in inconsistent state.Migration functionality will not work. Please contact support."
        ),
    ):
        create_alembic_version_table(ds.engine, ds.db_type)


@pytest.mark.postgres
class TestCreateAlembicVersionTable_Postgres(unittest.TestCase):
    def setUp(self):
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
                db_type="postgres",
            )
            self.store.initialise()
        except Exception:
            print("Database schema and data population failed! Test is skipping.")

    def tearDown(self):
        try:
            self.postgres.stop()
        except AttributeError:
            return

    def test_create_alembic_version_empty_db(self):
        create_alembic_version_table(self.store.engine, self.store.db_type)

        with self.store.engine.connect() as connection:
            results = connection.execute(text("SELECT * FROM pepys.alembic_version;")).fetchall()

            assert len(results) == 1
            assert results[0][0] == versions["LATEST_POSTGRES_VERSION"]

    def test_create_alembic_version_table_empty(self):
        # Create table and stamp version
        create_alembic_version_table(self.store.engine, self.store.db_type)

        # Delete all entries, so table is empty
        with self.store.engine.connect() as connection:
            connection.execute(text("DELETE FROM pepys.alembic_version;"))

        # Now run function
        create_alembic_version_table(self.store.engine, self.store.db_type)

        # Check it has one entry and it's the right one
        with self.store.engine.connect() as connection:
            results = connection.execute(text("SELECT * FROM pepys.alembic_version;")).fetchall()

            assert len(results) == 1
            assert results[0][0] == versions["LATEST_POSTGRES_VERSION"]

    def test_create_alembic_version_already_at_latest_version(self):
        # Run once to create the table and stamp latest version, then run again
        create_alembic_version_table(self.store.engine, self.store.db_type)

        create_alembic_version_table(self.store.engine, self.store.db_type)

        with self.store.engine.connect() as connection:
            results = connection.execute(text("SELECT * FROM pepys.alembic_version;")).fetchall()

            assert len(results) == 1
            assert results[0][0] == versions["LATEST_POSTGRES_VERSION"]

    def test_create_alembic_version_at_old_version(self):
        # Run once to create the table and stamp latest version
        create_alembic_version_table(self.store.engine, self.store.db_type)

        with self.store.engine.connect() as connection:
            connection.execute(text("UPDATE alembic_version SET version_num = 'old_version_id';"))

        with pytest.raises(
            ValueError,
            match=re.escape(
                "Database revision in alembic_version table (old_version_id) does not match latest revision"
            ),
        ):
            create_alembic_version_table(self.store.engine, self.store.db_type)

    def test_create_alembic_version_multiple_rows(self):
        # Run once to create the table and stamp latest version
        create_alembic_version_table(self.store.engine, self.store.db_type)

        with self.store.engine.connect() as connection:
            connection.execute(text("INSERT INTO alembic_version VALUES ('new_entry');"))

        with pytest.raises(
            ValueError,
            match=re.escape(
                "Multiple rows detected in alembic_version table. Database potentially in inconsistent state.Migration functionality will not work. Please contact support."
            ),
        ):
            create_alembic_version_table(self.store.engine, self.store.db_type)
