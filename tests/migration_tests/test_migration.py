import os
import shutil
import unittest
from unittest.mock import patch

from testing.postgresql import Postgresql

from paths import TESTS_DIRECTORY
from pepys_admin.admin_cli import AdminShell
from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor
from pepys_import.utils.data_store_utils import is_schema_created

CURRENT_DIR = os.getcwd()
SAMPLE_DATA_PATH = os.path.join(TESTS_DIRECTORY, "sample_data", "track_files", "rep_data")
DATABASE_PATH = os.path.join(TESTS_DIRECTORY, "migration_tests", "database")
CONFIG_FILE_PATH = os.path.join(
    TESTS_DIRECTORY, "config_file_tests", "example_config", "config_for_do_migrate.ini"
)
SQLITE_PATH = os.path.join(DATABASE_PATH, "sqlite", "pepys_0.0.17_test.sqlite")
COPY_FILE_PATH = os.path.join(DATABASE_PATH, "sqlite", "COPY_pepys_0.0.17_test.sqlite")
POSTGRES_SQL_PATH = os.path.join(DATABASE_PATH, "postgres", "pepys_0.0.17_dump.sql")


class MigrateSQLiteTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.store = DataStore("", "", "", 0, "new_db.db", "sqlite")
        self.shell = AdminShell(self.store)

    def tearDown(self) -> None:
        file_path = os.path.join(CURRENT_DIR, "new_db.db")
        if os.path.exists(file_path):
            os.remove(file_path)

    @patch("pepys_admin.admin_cli.input", return_value="Y")
    def test_do_migrate_empty_database(self, patched_input):
        assert is_schema_created(self.store.engine, self.store.db_type) is False
        # Migrate
        self.shell.do_migrate()
        assert is_schema_created(self.store.engine, self.store.db_type) is True

    @patch("pepys_admin.admin_cli.input", return_value="Y")
    def test_do_migrate_not_empty_database(self, patched_input):
        self.store.initialise()
        # Parse the REP files
        processor = FileProcessor(archive=False)
        processor.load_importers_dynamically()
        processor.process(SAMPLE_DATA_PATH, self.store, True)

        # Migrate
        self.shell.do_migrate()
        # Assert that it didn't break the schema
        assert is_schema_created(self.store.engine, self.store.db_type) is True

    @patch("pepys_admin.admin_cli.input", return_value="Y")
    def test_do_migrate_from_old_version_sqlite(self, patched_input):
        shutil.copyfile(src=SQLITE_PATH, dst=COPY_FILE_PATH)

        data_store = DataStore("", "", "", 0, COPY_FILE_PATH, "sqlite")
        admin_shell = AdminShell(data_store)

        # Migrate
        admin_shell.do_migrate()
        # Assert that it didn't break the schema
        assert is_schema_created(data_store.engine, data_store.db_type) is True

        os.remove(COPY_FILE_PATH)


class MigratePostgresTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.postgres = Postgresql(
            database="test", host="localhost", user="postgres", password="postgres", port=55527,
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

    @patch("pepys_admin.admin_cli.input", return_value="Y")
    def test_do_migrate_empty_database(self, patched_input):
        assert is_schema_created(self.store.engine, self.store.db_type) is False
        # Migrate
        self.shell.do_migrate()
        assert is_schema_created(self.store.engine, self.store.db_type) is True

    @patch("pepys_admin.admin_cli.input", return_value="Y")
    def test_do_migrate_not_empty_database(self, patched_input):
        self.store.initialise()
        # Parse the REP files
        processor = FileProcessor(archive=False)
        processor.load_importers_dynamically()
        processor.process(SAMPLE_DATA_PATH, self.store, True)

        # Migrate
        self.shell.do_migrate()
        # Assert that it didn't break the schema
        assert is_schema_created(self.store.engine, self.store.db_type) is True

    @patch("pepys_admin.admin_cli.input", return_value="Y")
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
