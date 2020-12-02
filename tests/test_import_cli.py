import os
import sqlite3
import unittest
from contextlib import redirect_stdout
from io import StringIO
from sqlite3 import OperationalError
from unittest.mock import ANY, patch

import pg8000
import pytest
from testing.postgresql import Postgresql

from config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_TYPE, DB_USERNAME
from pepys_import.cli import process
from pepys_import.core.store.data_store import DataStore
from pepys_import.utils.sqlite_utils import load_spatialite

FILE_PATH = os.path.dirname(__file__)
DATA_PATH = os.path.join(FILE_PATH, "sample_data/track_files/other_data")
REP_WITH_ERRORS_PATH = os.path.join(
    FILE_PATH, "sample_data/track_files/rep_data/uk_track_failing_enh_validation.rep"
)
CURRENT_DIR = os.getcwd()


class TestImportWithMissingDBFieldSQLite(unittest.TestCase):
    def setUp(self):
        ds = DataStore("", "", "", 0, "cli_import_test.db", db_type="sqlite")
        ds.initialise()

    def tearDown(self):
        os.remove("cli_import_test.db")

    def test_import_with_missing_db_field(self):
        conn = sqlite3.connect("cli_import_test.db")
        load_spatialite(conn, None)

        # We want to DROP a column from the States table, but SQLite doesn't support this
        # so we drop the table and create a new table instead
        conn.execute("DROP TABLE States")

        # SQL to create a States table without a heading column
        create_sql = """CREATE TABLE States (
        state_id INTEGER NOT NULL,
        time TIMESTAMP NOT NULL,
        sensor_id INTEGER NOT NULL,
        elevation REAL,
        course REAL,
        speed REAL,
        source_id INTEGER NOT NULL,
        privacy_id INTEGER,
        created_date DATETIME, "location" POINT,
        PRIMARY KEY (state_id)
        )"""

        conn.execute(create_sql)
        conn.close()

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            process(path=DATA_PATH, archive=False, db="cli_import_test.db", resolver="default")
        output = temp_output.getvalue()

        assert "ERROR: SQL error when communicating with database" in output


@pytest.mark.postgres
class TestImportWithMissingDBFieldPostgres(unittest.TestCase):
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
        except OperationalError:
            print("Database schema and data population failed! Test is skipping.")

    def tearDown(self):
        try:
            self.postgres.stop()
        except AttributeError:
            return

    def test_import_with_missing_db_field(self):
        conn = pg8000.connect(user="postgres", password="postgres", database="test", port=55527)
        cursor = conn.cursor()
        # Alter table to drop heading column
        cursor.execute('ALTER TABLE pepys."States" DROP COLUMN heading CASCADE;')

        conn.commit()
        conn.close()

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            db_config = {
                "name": "test",
                "host": "localhost",
                "username": "postgres",
                "password": "postgres",
                "port": 55527,
                "type": "postgres",
            }

            process(path=DATA_PATH, archive=False, db=db_config, resolver="default")
        output = temp_output.getvalue()

        assert "ERROR: SQL error when communicating with database" in output


@pytest.mark.postgres
class TestImportWithWrongTypeDBFieldPostgres(unittest.TestCase):
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
        except OperationalError:
            print("Database schema and data population failed! Test is skipping.")

    def tearDown(self):
        try:
            self.postgres.stop()
        except AttributeError:
            return

    def test_import_with_wrong_type_db_field(self):
        conn = pg8000.connect(user="postgres", password="postgres", database="test", port=55527)
        cursor = conn.cursor()
        # Alter table to change heading column to be a timestamp
        cursor.execute(
            'ALTER TABLE pepys."States" ALTER COLUMN heading SET DATA TYPE character varying(150);'
        )

        conn.commit()
        conn.close()

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            db_config = {
                "name": "test",
                "host": "localhost",
                "username": "postgres",
                "password": "postgres",
                "port": 55527,
                "type": "postgres",
            }

            process(path=DATA_PATH, archive=False, db=db_config, resolver="default")
        output = temp_output.getvalue()

        assert "ERROR: SQL error when communicating with database" in output


@patch("pepys_import.cli.DefaultResolver")
def test_process_resolver_specification_default(patched_default_resolver):
    process(resolver="default")
    patched_default_resolver.assert_called_once()


@patch("pepys_import.cli.CommandLineResolver")
def test_process_resolver_specification_cli(patched_cl_resolver):
    process(resolver="command-line")
    patched_cl_resolver.assert_called_once()


@patch("pepys_import.cli.CommandLineResolver")
@patch("pepys_import.cli.DefaultResolver")
def test_process_resolver_specification_invalid(patched_default_resolver, patched_cl_resolver):
    temp_output = StringIO()
    with redirect_stdout(temp_output):
        process(resolver="invalid")
    output = temp_output.getvalue()

    assert "Invalid option" in output

    patched_cl_resolver.assert_not_called()
    patched_default_resolver.assert_not_called()


@patch("pepys_import.cli.DataStore")
@patch("pepys_import.cli.FileProcessor")
def test_process_db_none(patched_file_proc, patched_data_store):
    process()

    patched_data_store.assert_called_with(
        db_username=DB_USERNAME,
        db_password=DB_PASSWORD,
        db_host=DB_HOST,
        db_port=DB_PORT,
        db_name=DB_NAME,
        db_type=DB_TYPE,
        missing_data_resolver=ANY,  # We don't care about this argument, and it's hard to test
    )


@patch("pepys_import.cli.prompt")
def test_training_mode_message(patched_input):
    # Don't reset the database at the start or end - we test that in another test
    patched_input.side_effect = ["n", "n"]

    # Store original PEPYS_CONFIG_FILE variable so we can reset it at the end
    # (as setting training mode changes that for this process - and when
    # pytest is running tests it runs them all in one process)
    orig_pepys_config_file = os.environ.get("PEPYS_CONFIG_FILE")

    temp_output = StringIO()
    with redirect_stdout(temp_output):
        process(resolver="default", training=True)
    output = temp_output.getvalue()

    assert "Running in Training Mode" in output

    # Reset PEPYS_CONFIG_FILE to what it was at the start of the test
    if orig_pepys_config_file is None:
        del os.environ["PEPYS_CONFIG_FILE"]
    else:
        os.environ["PEPYS_CONFIG_FILE"] = orig_pepys_config_file


@patch("pepys_import.cli.DataStore")
@patch("pepys_import.cli.prompt")
def test_training_mode_setup(patched_input, patched_data_store):
    # Don't reset the database at the start or end - we test that in another test
    patched_input.side_effect = ["n", "n"]

    # Store original PEPYS_CONFIG_FILE variable so we can reset it at the end
    # (as setting training mode changes that for this process - and when
    # pytest is running tests it runs them all in one process)
    orig_pepys_config_file = os.environ.get("PEPYS_CONFIG_FILE")

    db_name = os.path.expanduser(os.path.join("~", "pepys_training_database.db"))

    process(resolver="default", training=True)

    # Check it is called with the right db path, and with training_mode=True
    patched_data_store.assert_called_with(
        db_username="",
        db_password="",
        db_host="",
        db_port=0,
        db_name=db_name,
        db_type="sqlite",
        missing_data_resolver=ANY,  # We don't care about this argument, and it's hard to test
    )

    # Reset PEPYS_CONFIG_FILE to what it was at the start of the test
    if orig_pepys_config_file is None:
        del os.environ["PEPYS_CONFIG_FILE"]
    else:
        os.environ["PEPYS_CONFIG_FILE"] = orig_pepys_config_file


@patch("pepys_import.cli.prompt")
def test_training_mode_reset_at_end(patched_input):
    # Choose to reset at the end of the import
    patched_input.side_effect = ["n", "y"]

    # Store original PEPYS_CONFIG_FILE variable so we can reset it at the end
    # (as setting training mode changes that for this process - and when
    # pytest is running tests it runs them all in one process)
    orig_pepys_config_file = os.environ.get("PEPYS_CONFIG_FILE")

    temp_output = StringIO()
    with redirect_stdout(temp_output):
        process(resolver="default", training=True)
    output = temp_output.getvalue()

    assert "Running in Training Mode" in output

    # As we've done a reset, the database file should have been deleted
    assert not os.path.exists(os.path.expanduser(os.path.join("~", "pepys_training_database.db")))

    # Reset PEPYS_CONFIG_FILE to what it was at the start of the test
    if orig_pepys_config_file is None:
        del os.environ["PEPYS_CONFIG_FILE"]
    else:
        os.environ["PEPYS_CONFIG_FILE"] = orig_pepys_config_file


@patch("pepys_import.cli.prompt")
def test_training_mode_reset_at_start(patched_input):
    # Choose to reset at the start of the import
    patched_input.side_effect = ["y", "n"]

    db_path = os.path.expanduser(os.path.join("~", "pepys_training_database.db"))

    # Create an invalid database file, this should be deleted before it is tried to be read
    # so we won't get an error (if the reset hadn't worked then we'd get a 'File is not a database' error)
    with open(db_path, "w") as f:
        f.write("Invalid DB file contents")

    # Store original PEPYS_CONFIG_FILE variable so we can reset it at the end
    # (as setting training mode changes that for this process - and when
    # pytest is running tests it runs them all in one process)
    orig_pepys_config_file = os.environ.get("PEPYS_CONFIG_FILE")

    temp_output = StringIO()
    with redirect_stdout(temp_output):
        process(resolver="default", training=True)
    output = temp_output.getvalue()

    assert "Running in Training Mode" in output

    # Reset PEPYS_CONFIG_FILE to what it was at the start of the test
    if orig_pepys_config_file is None:
        del os.environ["PEPYS_CONFIG_FILE"]
    else:
        os.environ["PEPYS_CONFIG_FILE"] = orig_pepys_config_file


@patch("pepys_import.core.store.common_db.prompt", return_value="2")
def test_skip_validation(patched_prompt):
    ds = DataStore("", "", "", 0, "cli_import_skip_validation.db", db_type="sqlite")
    ds.initialise()

    # Don't skip validation, and select "Carry on running the validator, logging errors"
    process(
        path=REP_WITH_ERRORS_PATH,
        archive=False,
        db="cli_import_skip_validation.db",
        resolver="default",
        skip_validation=False,
    )
    patched_prompt.assert_called_once()
    with ds.session_scope():
        assert len(ds.session.query(ds.db_classes.Datafile).all()) == 0
        assert len(ds.session.query(ds.db_classes.State).all()) == 0

    # Skip validation this time
    patched_prompt.reset_mock()
    process(
        path=REP_WITH_ERRORS_PATH,
        archive=False,
        db="cli_import_skip_validation.db",
        resolver="default",
        skip_validation=True,
    )
    patched_prompt.assert_not_called()
    with ds.session_scope():
        datafile = ds.session.query(ds.db_classes.Datafile).all()
        assert len(datafile) == 1
        assert datafile[0].reference == "uk_track_failing_enh_validation.rep"

        sensor = ds.session.query(ds.db_classes.Sensor).all()
        assert len(sensor) == 1
        assert sensor[0].name == "SENSOR-1"

        platform = ds.session.query(ds.db_classes.Platform).all()
        assert len(platform) == 1
        assert platform[0].name == "SPLENDID"

        states = ds.session.query(ds.db_classes.State).all()
        assert len(states) == 7

    # Remove created db
    os.remove(os.path.join(CURRENT_DIR, "cli_import_skip_validation.db"))
