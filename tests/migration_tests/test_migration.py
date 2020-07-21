import os
import shutil
from importlib import reload
from unittest.mock import patch

import config
from paths import TESTS_DIRECTORY
from pepys_admin.admin_cli import AdminShell
from pepys_import.core.store.data_store import DataStore
from pepys_import.utils.data_store_utils import is_schema_created

SAMPLE_DATA_PATH = os.path.join(TESTS_DIRECTORY, "sample_data")
DATA_PATH = os.path.join(SAMPLE_DATA_PATH, "track_files/rep_data")
CONFIG_FILE_PATH = os.path.join(
    TESTS_DIRECTORY, "config_file_tests", "example_config", "config_for_do_migrate.ini"
)
SQLITE_PATH = os.path.join(
    TESTS_DIRECTORY, "migration_tests", "database", "pepys_0.0.17v_test.sqlite"
)
COPY_FILE_PATH = os.path.join(
    TESTS_DIRECTORY, "migration_tests", "database", "COPY_pepys_0.0.17v_test.sqlite"
)


@patch.dict(os.environ, {"PEPYS_CONFIG_FILE": CONFIG_FILE_PATH})
@patch("pepys_admin.admin_cli.input", return_value="Y")
def test_do_migrate_from_old_version_database(patched_input):
    reload(config)
    shutil.copyfile(src=SQLITE_PATH, dst=COPY_FILE_PATH)

    data_store = DataStore("", "", "", 0, COPY_FILE_PATH, "sqlite")
    admin_shell = AdminShell(data_store)

    # Migrate
    admin_shell.do_migrate()
    # Assert that it didn't break the schema
    assert is_schema_created(data_store.engine, data_store.db_type) is True

    os.remove(COPY_FILE_PATH)
