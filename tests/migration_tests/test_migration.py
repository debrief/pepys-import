import os
import shutil
import sqlite3
import unittest
from unittest.mock import patch

from alembic import command
from testing.postgresql import Postgresql

from paths import TESTS_DIRECTORY
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
        processor.process(REP_DATA_PATH, self.store, True)

        # Migrate
        self.shell.do_migrate()
        # Assert that it didn't break the schema
        assert is_schema_created(self.store.engine, self.store.db_type) is True

    @patch("pepys_admin.admin_cli.input", return_value="Y")
    def test_do_migrate_from_old_version_sqlite(self, patched_input):
        shutil.copyfile(src=SQLITE_PATH, dst=COPY_DB_PATH)

        data_store = DataStore("", "", "", 0, COPY_DB_PATH, "sqlite")
        admin_shell = AdminShell(data_store)

        # Migrate
        admin_shell.do_migrate()
        # Assert that it didn't break the schema
        assert is_schema_created(data_store.engine, data_store.db_type) is True

        os.remove(COPY_DB_PATH)


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
        processor.process(REP_DATA_PATH, self.store, True)

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


def get_alembic_version(connection):
    version = connection.execute(f"SELECT version_num FROM alembic_version;")
    version = version.fetchone()[0]
    return version


def get_alembic_version_postgres(connection):
    version = connection.execute(f'SELECT version_num FROM pepys."alembic_version";')
    version = version.fetchone()[0]
    return version


def import_files(path_list, data_store):
    processor = FileProcessor(archive=False)
    processor.load_importers_dynamically()
    for path in path_list:
        processor.process(path, data_store, False)


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


def convert_query_result_to_dictionary(result):
    full_paths = get_full_paths_of_sample_data()
    # Put them in a proper dictionary, where key is an alembic version,
    # and value is a list that contains datafile references
    version_datafile_dict = {}
    for version, datafile in result:
        if version not in version_datafile_dict:
            version_datafile_dict[version] = []
        version_datafile_dict[version].append(full_paths.get(datafile))
    return version_datafile_dict


class StepByStepMigrationTestCase(unittest.TestCase):
    """This class has two tests that create a custom table named *version_datafile*, which has
    alembic versions with datafile references in each row. Then, it starts to upgrade the old version
    database one by one. In each upgrade, it checks whether if there is any related value in the
    custom database. If there is, it imports those datafiles and continues to upgrade.

    Currently, old databases in the repository is generated by *Pepys 0.0.17*. Therefore, there is
    only one data type (nisida) which isn't imported. In the future,
    :code:`version_datafile_table.sql` files under :code:`migration_tests/postgres` and
    :code:`migration_tests/sqlite` might be changed to include new datafile types.
    """

    def test_migrate_sqlite(self):
        shutil.copyfile(src=SQLITE_PATH, dst=COPY_DB_PATH)

        data_store = DataStore("", "", "", 0, COPY_DB_PATH, "sqlite")
        admin_shell = AdminShell(data_store)
        config = admin_shell.cfg

        # Read SQL file for creating version/datafile table and inserting values
        with open(SQLITE_SQL_PATH, "r") as f:
            sql = f.read()

        # Run SQL script, then fetch all values from the version/datafile table
        connection = sqlite3.connect(COPY_DB_PATH)
        connection.executescript(sql)
        result = connection.execute(f"SELECT version, datafile FROM version_datafile ORDER BY id;")
        result = result.fetchall()
        version_datafile_dict = convert_query_result_to_dictionary(result)

        # Migrate the database one by one, import datafiles if specified in version/datafile table
        while True:
            try:
                command.upgrade(config, "+1")
                new_version = get_alembic_version(connection)
                if new_version in version_datafile_dict:
                    import_files(version_datafile_dict[new_version], data_store)
                print(new_version)
            except Exception as e:
                print(
                    f"Exception details: {e}\n\nERROR: Alembic error when migrating the database!"
                )
                break
        # Drop the custom version/datafile table
        connection.execute("DROP TABLE version_datafile;")
        connection.close()

        # Assert that it didn't break the schema
        assert is_schema_created(data_store.engine, data_store.db_type) is True
        os.remove(COPY_DB_PATH)

    def test_migrate_postgres(self):
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
        config = admin_shell.cfg

        with open(POSTGRES_SQL_PATH, "r") as f:
            sql_code = f.read()
        with open(POSTGRES_SQL_PATH_2, "r") as f:
            sql_code_2 = f.read()

        # Import all tables and sample data
        with data_store.engine.connect().execution_options(autocommit=True) as connection:
            connection.execute(sql_code)
            connection.execute(sql_code_2)

            result = connection.execute(
                f'SELECT version, datafile FROM pepys."version_datafile" ORDER BY id;'
            )
            result = result.fetchall()
            version_datafile_dict = convert_query_result_to_dictionary(result)

            # Migrate the database one by one, import datafiles if specified in version/datafile table
            while True:
                try:
                    command.upgrade(config, "+1")
                    new_version = get_alembic_version_postgres(connection)
                    if new_version in version_datafile_dict:
                        import_files(version_datafile_dict[new_version], data_store)
                except Exception as e:
                    print(
                        f"Exception details: {e}\n\nERROR: Alembic error when migrating the database!"
                    )
                    break
            # Drop the custom version/datafile table
            connection.execute('DROP TABLE pepys."version_datafile";')

        # Assert that it didn't break the schema
        assert is_schema_created(data_store.engine, data_store.db_type) is True

        try:
            postgres.stop()
        except AttributeError:
            return


if __name__ == "__main__":
    unittest.main()
