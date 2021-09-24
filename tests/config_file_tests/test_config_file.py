import os
import unittest
from contextlib import redirect_stdout
from importlib import reload
from io import StringIO
from unittest.mock import patch

import pytest

import config
from importers.replay_importer import ReplayImporter
from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor
from tests.utils import side_effect

DIRECTORY_PATH = os.path.dirname(__file__)
TEST_IMPORTER_PATH = os.path.join(DIRECTORY_PATH, "parsers")
BAD_IMPORTER_PATH = os.path.join(DIRECTORY_PATH, "bad_path")
OUTPUT_PATH = os.path.join(DIRECTORY_PATH, "output")
CONFIG_FILE_PATH = os.path.join(DIRECTORY_PATH, "example_config", "config.ini")
CONFIG_FILE_PATH_2 = os.path.join(DIRECTORY_PATH, "example_config", "config_without_database.ini")
CONFIG_FILE_PATH_3 = os.path.join(DIRECTORY_PATH, "example_config", "config_older_version.ini")
BASIC_PARSERS_PATH = os.path.join(DIRECTORY_PATH, "basic_tests")
ENHANCED_PARSERS_PATH = os.path.join(DIRECTORY_PATH, "enhanced_tests")
DATA_PATH = os.path.join(DIRECTORY_PATH, "..", "sample_data")


class ConfigVariablesTestCase(unittest.TestCase):
    @patch.dict(os.environ, {"PEPYS_CONFIG_FILE": CONFIG_FILE_PATH})
    def test_config_variables(self):
        reload(config)
        assert config.DB_USERNAME == "Grfg Hfre"
        assert config.DB_PASSWORD == "123456"
        assert config.DB_HOST == "localhost"
        assert config.DB_PORT == 5432
        assert config.DB_NAME == "test"
        assert config.DB_TYPE == "postgres"
        assert config.ARCHIVE_USER == "hfre"
        assert config.ARCHIVE_PASSWORD == "cnffjbeq"
        assert config.ARCHIVE_PATH == "path/to/archive"
        assert config.LOCAL_PARSERS == "path/to/parser"
        assert config.LOCAL_BASIC_TESTS == "path/to/basic/tests"
        assert config.LOCAL_ENHANCED_TESTS == "path/to/enhanced/tests"

    @patch.dict(os.environ, {"PEPYS_CONFIG_FILE": BAD_IMPORTER_PATH})
    def test_wrong_file_path(self):
        # File not found exception
        temp_output = StringIO()
        with redirect_stdout(temp_output), pytest.raises(SystemExit):
            reload(config)
        output = temp_output.getvalue()
        assert "Pepys config file not found at location: " in output

    @patch.dict(os.environ, {"PEPYS_CONFIG_FILE": TEST_IMPORTER_PATH})
    def test_wrong_file_path_2(self):
        # Your environment variable doesn't point to a file exception
        temp_output = StringIO()
        with redirect_stdout(temp_output), pytest.raises(SystemExit):
            reload(config)
        output = temp_output.getvalue()
        assert "Your environment variable doesn't point to a file:" in output

    @patch.dict(os.environ, {"PEPYS_CONFIG_FILE": CONFIG_FILE_PATH_2})
    def test_without_database_section(self):
        # Your environment variable doesn't point to a file exception
        temp_output = StringIO()
        with redirect_stdout(temp_output), pytest.raises(SystemExit):
            reload(config)
        output = temp_output.getvalue()
        assert "Couldn't find 'database' section in" in output

    @patch.dict(os.environ, {"PEPYS_CONFIG_FILE": CONFIG_FILE_PATH_3})
    def test_with_older_config_file(self):
        # pylint: disable=no-self-use
        temp_output = StringIO()
        with redirect_stdout(temp_output), pytest.raises(SystemExit):
            reload(config)
        output = temp_output.getvalue()
        assert (
            "Config file contains variable names used in legacy versions of Pepys that provided insufficient support for database migration. \n Please contact your system administrator to discuss renaming db_xxx to database_xxx."
            in output
        )

    @patch.dict(os.environ, {"PEPYS_CONFIG_FILE_USER": CONFIG_FILE_PATH})
    def test_config_file_user_variable(self):
        reload(config)
        assert config.DB_USERNAME == "Grfg Hfre"
        assert config.DB_PASSWORD == "123456"
        assert config.DB_HOST == "localhost"

    @patch.dict(
        os.environ,
        {"PEPYS_CONFIG_FILE_USER": CONFIG_FILE_PATH, "PEPYS_CONFIG_FILE": CONFIG_FILE_PATH_2},
    )
    def test_config_file_user_has_priority(self):
        reload(config)
        assert config.DB_USERNAME == "Grfg Hfre"
        assert config.DB_PASSWORD == "123456"
        assert config.DB_HOST == "localhost"


class FileProcessorVariablesTestCase(unittest.TestCase):
    def test_pepys_local_parsers(self):
        file_processor = FileProcessor(local_parsers=TEST_IMPORTER_PATH)

        assert len(file_processor.importers) == 1
        assert file_processor.importers[0].name == "Test Importer"

    @patch("pepys_import.file.file_processor.custom_print_formatted_text", side_effect=side_effect)
    def test_bad_pepys_local_parsers_path(self, patched_print):
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            file_processor = FileProcessor(local_parsers=BAD_IMPORTER_PATH)
        output = temp_output.getvalue()

        assert len(file_processor.importers) == 0
        assert (
            output
            == f"No such file or directory: {BAD_IMPORTER_PATH}. Only core parsers are going to work.\n"
        )

    def test_pepys_archive_location(self):
        file_processor = FileProcessor(archive_path=OUTPUT_PATH, archive=True)
        assert os.path.exists(OUTPUT_PATH) is True
        assert file_processor.output_path == OUTPUT_PATH
        # Remove the test_output directory
        os.rmdir(OUTPUT_PATH)

    def test_pepys_invalid_archive_location_not_archiving(self):
        # Tests that an invalid archive location doesn't give
        # an error if we've got archiving turned off
        _ = FileProcessor(archive_path=r"///blahblah/blah", archive=False)

    def test_pepys_invalid_archive_location_with_archiving(self):
        # Tests that an invalid archive location gives an error
        # if we're running with archiving turned on
        with pytest.raises(ValueError, match="Could not create archive folder"):
            _ = FileProcessor(archive_path=r"///blahblah/blah", archive=True)

    def test_no_archive_path_given(self):
        store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        store.initialise()
        with store.session_scope():
            store.populate_reference()

        file_processor = FileProcessor()

        file_processor.register_importer(ReplayImporter())
        processing_path = os.path.join(DATA_PATH, "track_files", "rep_data", "rep_test1.rep")
        file_processor.process(
            processing_path,
            store,
            False,
        )

        assert os.path.exists(os.path.join(DATA_PATH, "track_files", "rep_data", "output"))

        if os.path.exists(os.path.join(processing_path, "output")):
            os.rmdir(os.path.join(processing_path, "output"))


if __name__ == "__main__":
    unittest.main()
