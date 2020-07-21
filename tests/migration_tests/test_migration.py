import os
import shutil
from unittest.mock import patch

from testing.postgresql import Postgresql

from paths import TESTS_DIRECTORY
from pepys_admin.admin_cli import AdminShell
from pepys_import.core.store.data_store import DataStore
from pepys_import.utils.data_store_utils import is_schema_created

SAMPLE_DATA_PATH = os.path.join(TESTS_DIRECTORY, "sample_data")
DATABASE_PATH = os.path.join(TESTS_DIRECTORY, "migration_tests", "database")
CONFIG_FILE_PATH = os.path.join(
    TESTS_DIRECTORY, "config_file_tests", "example_config", "config_for_do_migrate.ini"
)
SQLITE_PATH = os.path.join(DATABASE_PATH, "pepys_0.0.17v_test.sqlite")
COPY_FILE_PATH = os.path.join(DATABASE_PATH, "COPY_pepys_0.0.17v_test.sqlite")
POSTGRES_SQL_PATH = os.path.join(DATABASE_PATH, "pepys_0.0.17_dump.sql")


@patch("pepys_admin.admin_cli.input", return_value="Y")
def test_do_migrate_from_old_version_sqlite(patched_input):
    shutil.copyfile(src=SQLITE_PATH, dst=COPY_FILE_PATH)

    data_store = DataStore("", "", "", 0, COPY_FILE_PATH, "sqlite")
    admin_shell = AdminShell(data_store)

    # Migrate
    admin_shell.do_migrate()
    # Assert that it didn't break the schema
    assert is_schema_created(data_store.engine, data_store.db_type) is True

    os.remove(COPY_FILE_PATH)


@patch("pepys_admin.admin_cli.input", return_value="Y")
def test_do_migrate_from_old_version_postgres(patched_input):
    postgres = Postgresql(
        database="test", host="localhost", user="postgres", password="postgres", port=55527,
    )
    data_store = DataStore(
        db_name="test",
        db_host="localhost",
        db_username="postgres",
        db_password="postgres",
        db_port=55527,
        db_type="postgres",
    )
    admin_shell = AdminShell(data_store)

    with open(POSTGRES_SQL_PATH, "r") as f:
        sql_code = f.read()

    # Import all tables and sample data
    with data_store.engine.connect().execution_options(autocommit=True) as connection:
        connection.execute(sql_code)

    # Migrate
    admin_shell.do_migrate()
    # Assert that it didn't break the schema
    assert is_schema_created(data_store.engine, data_store.db_type) is True

    try:
        postgres.stop()
    except AttributeError:
        return
