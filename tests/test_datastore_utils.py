import json
import os
import re
import unittest
from contextlib import redirect_stdout
from io import StringIO

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
    with ds.engine.begin() as connection:
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

    with ds.engine.begin() as connection:
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

    with ds.engine.begin() as connection:
        connection.execute(text("INSERT INTO alembic_version VALUES ('new_entry');"))

    with pytest.raises(
        ValueError,
        match=re.escape(
            "Multiple rows detected in alembic_version table. Database potentially in inconsistent state.Migration functionality will not work. Please contact support."
        ),
    ):
        create_alembic_version_table(ds.engine, ds.db_type)


def test_check_migration_version_new():
    # Create a new alembic version database - function should pass
    DataStore("", "", "", 0, ":memory:", db_type="sqlite")


def test_check_migration_version_is_found():
    # Create a new alembic version database - function should pass
    ds = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    revision = ["version_id", "test_version_id"]

    # Run once to create the table and stamp latest version
    create_alembic_version_table(ds.engine, ds.db_type)

    with ds.engine.begin() as connection:
        connection.execute(text("UPDATE alembic_version SET version_num = 'version_id';"))

    ds.check_migration_version(revision)


def test_check_migration_version_no_revisions():
    # Call the function with no revisions in the list - function should call sys.exit(1)
    ds = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    revisions = []

    with pytest.raises(SystemExit) as exit_exception_e:
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            ds.check_migration_version(revisions)
    output = temp_output.getvalue()
    assert "ERROR: Expected list of known revisions is empty." in output
    assert exit_exception_e.value.code == 1


def test_check_migration_version_not_in_revisions():
    # Call the function with revisions that won't exist - function should call sys.exit(1)
    ds = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    # These revisions will count as known revisions but will not be found by the database
    revisions = ["abc", "def", "ghi"]

    # Run once to create the table and stamp latest version
    create_alembic_version_table(ds.engine, ds.db_type)

    with ds.engine.begin() as connection:
        connection.execute(text("UPDATE alembic_version SET version_num = 'version_id';"))

    # Revision list won't have the migration version within it -
    with pytest.raises(SystemExit) as exit_exception_e:
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            ds.check_migration_version(revisions)
    output = temp_output.getvalue()
    assert (
        "ERROR: The current database version version_id is not recognised by this version of Pepys."
        in output
    )
    assert exit_exception_e.value.code == 1


def test_check_migration_version_incorrect_length():
    # Create a new alembic version database - function should pass
    ds = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    revisions = ["version_id", "test_version_id"]

    # Run once to create the table and stamp latest version
    create_alembic_version_table(ds.engine, ds.db_type)

    with ds.engine.begin() as connection:
        connection.execute(text("INSERT INTO alembic_version VALUES ('TEST');"))
        connection.execute(text("INSERT INTO alembic_version VALUES ('TEST1');"))

    with pytest.raises(SystemExit) as exit_exception_e:
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            ds.check_migration_version(revisions)
    output = temp_output.getvalue()
    assert "ERROR: Retrieved version contents from database is incorrect length." in output
    assert exit_exception_e.value.code == 1


def test_check_migration_version_incorrect_length_null_value():
    # Create a new alembic version database - function should pass
    ds = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    revisions = ["version_id", "test_version_id"]

    # Run once to create the table and stamp latest version
    create_alembic_version_table(ds.engine, ds.db_type)

    with ds.engine.begin() as connection:
        connection.execute(text("INSERT INTO alembic_version VALUES ('');"))

    with pytest.raises(SystemExit) as exit_exception_e:
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            ds.check_migration_version(revisions)
    output = temp_output.getvalue()
    assert "ERROR: Retrieved version contents from database is incorrect length." in output
    assert exit_exception_e.value.code == 1


def test_check_migration_version_incorrect_n_cols():
    ds = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    revisions = ["version_id", "test_version_id"]

    with ds.engine.begin() as connection:
        connection.execute(text("CREATE TABLE alembic_version (col1, col2, col3);"))
        connection.execute(text("INSERT INTO alembic_version VALUES ('', '', '');"))

    with pytest.raises(SystemExit) as exit_exception_e:
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            ds.check_migration_version(revisions)
    output = temp_output.getvalue()
    assert "ERROR: Retrieved version contents from database is incorrect length." in output
    assert exit_exception_e.value.code == 1


def test_check_migration_version_no_table_contents():
    # Create a new alembic version database - function should pass
    ds = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    revisions = ["version_id", "test_version_id"]

    # Run once to create the table and stamp latest version
    create_alembic_version_table(ds.engine, ds.db_type)

    with ds.engine.begin() as connection:
        connection.execute(text("DELETE FROM alembic_version;"))

    temp_output = StringIO()
    with redirect_stdout(temp_output):
        ds.check_migration_version(revisions)
    output = temp_output.getvalue()
    assert "No previous database contents - continuing to create schema." in output


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
        with self.store.engine.begin() as connection:
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

        with self.store.engine.begin() as connection:
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

        with self.store.engine.begin() as connection:
            connection.execute(text("INSERT INTO alembic_version VALUES ('new_entry');"))

        with pytest.raises(
            ValueError,
            match=re.escape(
                "Multiple rows detected in alembic_version table. Database potentially in inconsistent state.Migration functionality will not work. Please contact support."
            ),
        ):
            create_alembic_version_table(self.store.engine, self.store.db_type)


@pytest.mark.postgres
class TestCheckMigrationVersion_Postgres(unittest.TestCase):
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

    def test_check_migration_version_is_found(self):
        # Create a new alembic version database - function should pass
        revision = ["version_id", "test_version_id"]

        # Run once to create the table and stamp latest version
        create_alembic_version_table(self.store.engine, self.store.db_type)

        with self.store.engine.begin() as connection:
            connection.execute(text("UPDATE pepys.alembic_version SET version_num = 'version_id';"))

        self.store.check_migration_version(revision)

    def test_check_migration_version_no_revisions(self):
        # Call the function with no revisions in the list - function should call sys.exit(1)
        revisions = []

        with pytest.raises(SystemExit) as exit_exception_e:
            temp_output = StringIO()
            with redirect_stdout(temp_output):
                self.store.check_migration_version(revisions)
        output = temp_output.getvalue()
        assert "ERROR: Expected list of known revisions is empty." in output
        assert exit_exception_e.value.code == 1

    def test_check_migration_version_not_in_revisions(self):
        # These revisions will count as known revisions but will not be found by the database
        revisions = ["abc", "def", "ghi"]

        # Run once to create the table and stamp latest version
        create_alembic_version_table(self.store.engine, self.store.db_type)

        with self.store.engine.begin() as connection:
            connection.execute(text("UPDATE pepys.alembic_version SET version_num = 'version_id';"))

        # Revision list won't have the migration version within it -
        with pytest.raises(SystemExit) as exit_exception_e:
            temp_output = StringIO()
            with redirect_stdout(temp_output):
                self.store.check_migration_version(revisions)
        output = temp_output.getvalue()
        assert (
            "ERROR: The current database version version_id is not recognised by this version of Pepys."
            in output
        )
        assert exit_exception_e.value.code == 1

    def test_check_migration_version_incorrect_length(self):
        revisions = ["version_id", "test_version_id"]

        # Run once to create the table and stamp latest version
        create_alembic_version_table(self.store.engine, self.store.db_type)

        with self.store.engine.begin() as connection:
            connection.execute(text("INSERT INTO pepys.alembic_version VALUES ('TEST');"))
            connection.execute(text("INSERT INTO pepys.alembic_version VALUES ('TEST1');"))

        with pytest.raises(SystemExit) as exit_exception_e:
            temp_output = StringIO()
            with redirect_stdout(temp_output):
                self.store.check_migration_version(revisions)
        output = temp_output.getvalue()
        assert "ERROR: Retrieved version contents from database is incorrect length." in output
        assert exit_exception_e.value.code == 1

    def test_check_migration_version_incorrect_length_null_value(self):
        revisions = ["version_id", "test_version_id"]

        # Run once to create the table and stamp latest version
        create_alembic_version_table(self.store.engine, self.store.db_type)

        with self.store.engine.begin() as connection:
            connection.execute(text("INSERT INTO pepys.alembic_version VALUES ('');"))

        with pytest.raises(SystemExit) as exit_exception_e:
            temp_output = StringIO()
            with redirect_stdout(temp_output):
                self.store.check_migration_version(revisions)
        output = temp_output.getvalue()
        assert "ERROR: Retrieved version contents from database is incorrect length." in output
        assert exit_exception_e.value.code == 1

    def test_check_migration_version_no_table_contents(self):
        revisions = ["version_id", "test_version_id"]

        # Run once to create the table and stamp latest version
        create_alembic_version_table(self.store.engine, self.store.db_type)

        with self.store.engine.begin() as connection:
            connection.execute(text("DELETE FROM pepys.alembic_version;"))

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.store.check_migration_version(revisions)
        output = temp_output.getvalue()
        assert "No previous database contents - continuing to create schema." in output
