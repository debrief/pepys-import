import json
import os
import shutil
import sqlite3
import unittest
from unittest.mock import patch

import pytest
from alembic import command
from testing.postgresql import Postgresql

from paths import MIGRATIONS_DIRECTORY, TESTS_DIRECTORY
from pepys_admin.admin_cli import AdminShell
from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor
from pepys_import.utils.data_store_utils import is_schema_created

CURRENT_DIR = os.getcwd()
SAMPLE_DATA_PATH = os.path.join(TESTS_DIRECTORY, "sample_data")
REP_DATA_PATH = os.path.join(SAMPLE_DATA_PATH, "track_files", "rep_data")
DATABASE_PATH = os.path.join(TESTS_DIRECTORY, "migration_tests", "database")
SQLITE_PATH = os.path.join(DATABASE_PATH, "sqlite", "pepys_0.0.17_test.sqlite")
COPY_DB_PATH = os.path.join(DATABASE_PATH, "sqlite", "COPY_pepys_0.0.17_test.sqlite")
SQLITE_SQL_PATH = os.path.join(DATABASE_PATH, "sqlite", "version_datafile_table.sql")
POSTGRES_SQL_PATH = os.path.join(DATABASE_PATH, "postgres", "pepys_0.0.17_dump.sql")
POSTGRES_SQL_PATH_2 = os.path.join(DATABASE_PATH, "postgres", "version_datafile_table.sql")
LATEST_VERSIONS_PATH = os.path.join(MIGRATIONS_DIRECTORY, "latest_revisions.json")


class MigrateSQLiteTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.store = DataStore("", "", "", 0, "new_db.db", "sqlite")
        self.shell = AdminShell(self.store)

    def tearDown(self) -> None:
        file_path = os.path.join(CURRENT_DIR, "new_db.db")
        if os.path.exists(file_path):
            os.remove(file_path)

    @patch("pepys_admin.admin_cli.prompt", return_value="Y")
    def test_do_migrate_empty_database(self, patched_input):
        assert is_schema_created(self.store.engine, self.store.db_type) is False
        # Migrate
        self.shell.do_migrate()
        assert is_schema_created(self.store.engine, self.store.db_type) is True

    @patch("pepys_admin.admin_cli.prompt", return_value="Y")
    @patch("pepys_import.core.store.common_db.prompt", return_value="2")
    def test_do_migrate_not_empty_database(self, patched_prompt, patched_input):
        self.store.initialise()
        # Parse the REP files
        processor = FileProcessor(archive=False)
        processor.load_importers_dynamically()
        processor.process(REP_DATA_PATH, self.store, True)

        # Migrate
        self.shell.do_migrate()
        # Assert that it didn't break the schema
        assert is_schema_created(self.store.engine, self.store.db_type) is True

    @patch("pepys_admin.admin_cli.prompt", return_value="Y")
    def test_do_migrate_from_old_version_sqlite(self, patched_input):
        shutil.copyfile(src=SQLITE_PATH, dst=COPY_DB_PATH)

        data_store = DataStore("", "", "", 0, COPY_DB_PATH, "sqlite")
        admin_shell = AdminShell(data_store)

        # Migrate
        admin_shell.do_migrate()
        # Assert that it didn't break the schema
        assert is_schema_created(data_store.engine, data_store.db_type) is True

        os.remove(COPY_DB_PATH)


@pytest.mark.postgres
class MigratePostgresTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.postgres = Postgresql(
            database="test",
            host="localhost",
            user="postgres",
            password="postgres",
            port=55527,
        )
        self.store = DataStore(
            db_name="test",
            db_host="localhost",
            db_username="postgres",
            db_password="postgres",
            db_port=55527,
            db_type="postgres",
        )
        self.shell = AdminShell(self.store)

    def tearDown(self) -> None:
        try:
            self.postgres.stop()
        except AttributeError:
            return

    @patch("pepys_admin.admin_cli.prompt", return_value="Y")
    def test_do_migrate_empty_database(self, patched_input):
        assert is_schema_created(self.store.engine, self.store.db_type) is False
        # Migrate
        self.shell.do_migrate()
        assert is_schema_created(self.store.engine, self.store.db_type) is True

    @patch("pepys_admin.admin_cli.prompt", return_value="Y")
    @patch("pepys_import.core.store.common_db.prompt", return_value="2")
    def test_do_migrate_not_empty_database(self, patched_prompt, patched_input):
        self.store.initialise()
        # Parse the REP files
        processor = FileProcessor(archive=False)
        processor.load_importers_dynamically()
        processor.process(REP_DATA_PATH, self.store, True)

        # Migrate
        self.shell.do_migrate()
        # Assert that it didn't break the schema
        assert is_schema_created(self.store.engine, self.store.db_type) is True

    @patch("pepys_admin.admin_cli.prompt", return_value="Y")
    def test_do_migrate_from_old_version_postgres(self, patched_input):
        with open(POSTGRES_SQL_PATH, "r") as f:
            sql_code = f.read()

        # Import all tables and sample data
        with self.store.engine.connect().execution_options(autocommit=True) as connection:
            connection.execute(sql_code)

        # Migrate
        self.shell.do_migrate()
        # Assert that it didn't break the schema
        assert is_schema_created(self.store.engine, self.store.db_type) is True


def get_alembic_version(connection, db_type="sqlite"):
    if db_type == "sqlite":
        version = connection.execute("SELECT version_num FROM alembic_version;")
    elif db_type == "postgres":
        version = connection.execute('SELECT version_num FROM pepys."alembic_version";')
    else:
        print("Given DB type is wrong!")
        return

    version = version.fetchone()[0]
    return version


def get_latest_alembic_version(db_type="sqlite"):
    with open(LATEST_VERSIONS_PATH, "r") as f:
        versions = json.load(f)
    if db_type == "sqlite":
        return versions.get("LATEST_SQLITE_VERSION")
    elif db_type == "postgres":
        return versions.get("LATEST_POSTGRES_VERSION")
    else:
        print("Given DB type is wrong!")


def import_files(datafile_list, data_store):
    full_paths = get_full_paths_of_sample_data()
    processor = FileProcessor(archive=False)
    processor.load_importers_dynamically()
    for datafile in datafile_list:
        full_path = full_paths.get(datafile)
        processor.process(full_path, data_store, False)


def get_full_paths_of_sample_data(directory=SAMPLE_DATA_PATH):
    """Fetches full path for each datafile in the directory.
    By default, it fetches paths from *tests/sample_data* folder."""
    full_paths = {}
    for current_path, folders, files in os.walk(directory):
        # Skip CSV files
        if "csv_files" in current_path:
            continue

        for file in files:
            full_paths[file] = os.path.join(current_path, file)
    return full_paths


class StepByStepMigrationTestCase(unittest.TestCase):
    """This class has two tests that starts to upgrade the old version database one by one.
    In each upgrade, it checks whether if there is any related value in the dictionary.
    If there is, it imports those datafiles and continues to upgrade.

    Currently, old databases in the repository is generated by *Pepys 0.0.17*. Therefore, there is
    only one data type (nisida) which isn't imported. In the future,
    the dictionaries in the :code:`setUp` method might be changed to include new datafiles.
    """

    def setUp(self) -> None:
        # The following dictionaries are going to be used to import datafiles. When the version of
        # the database is sufficient (if the version is the same with a key in dictionary)
        self.sqlite_version_datafile_dict = {
            "5a909b3cec9d": [
                "nisida_example.txt",
                "nisida_invalid_header_line.txt",
                "nisida_split_narrative.txt",
            ]
        }
        self.postgres_version_datafile_dict = {
            "d154cad9087f": [
                "nisida_example.txt",
                "nisida_invalid_header_line.txt",
                "nisida_split_narrative.txt",
            ]
        }

    def test_migrate_sqlite(self):
        shutil.copyfile(src=SQLITE_PATH, dst=COPY_DB_PATH)

        data_store = DataStore("", "", "", 0, COPY_DB_PATH, "sqlite")
        admin_shell = AdminShell(data_store)
        config = admin_shell.cfg
        latest_sqlite_version = get_latest_alembic_version()

        connection = sqlite3.connect(COPY_DB_PATH)
        # Migrate the database one by one, import datafiles if specified in version/datafile table
        while True:
            command.upgrade(config, "+1")
            new_version = get_alembic_version(connection)
            if new_version in self.sqlite_version_datafile_dict:
                import_files(self.sqlite_version_datafile_dict[new_version], data_store)
            if new_version == latest_sqlite_version:
                print("Upgrade to head is successful!")
                break
        connection.close()

        # Assert that it didn't break the schema
        assert is_schema_created(data_store.engine, data_store.db_type) is True
        os.remove(COPY_DB_PATH)

    @pytest.mark.postgres
    def test_migrate_postgres(self):
        postgres = Postgresql(
            database="test",
            host="localhost",
            user="postgres",
            password="postgres",
            port=55527,
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
        config = admin_shell.cfg
        latest_postgres_version = get_latest_alembic_version("postgres")

        with open(POSTGRES_SQL_PATH, "r") as f:
            sql_code = f.read()

        # Import all tables and sample data
        with data_store.engine.connect().execution_options(autocommit=True) as connection:
            connection.execute(sql_code)

            # Migrate the database one by one, import datafiles if specified in version/datafile table
            while True:
                command.upgrade(config, "+1")
                new_version = get_alembic_version(connection, "postgres")
                if new_version in self.postgres_version_datafile_dict:
                    import_files(self.postgres_version_datafile_dict[new_version], data_store)
                if new_version == latest_postgres_version:
                    print("Upgrade to head is successful!")
                    break

        # Assert that it didn't break the schema
        assert is_schema_created(data_store.engine, data_store.db_type) is True

        try:
            postgres.stop()
        except AttributeError:
            return


if __name__ == "__main__":
    unittest.main()
