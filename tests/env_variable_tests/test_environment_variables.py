import unittest
import os

from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from pepys_import.file.file_processor import FileProcessor

DIRECTORY_PATH = os.path.dirname(__file__)
TEST_IMPORTER_PATH = os.path.join(DIRECTORY_PATH, "test_local_imports")
BAD_IMPORTER_PATH = os.path.join(DIRECTORY_PATH, "bad_path")


class EnvironmentVariablesTestCase(unittest.TestCase):
    @patch.dict(os.environ, {"PEPYS_LOCAL_PARSERS": TEST_IMPORTER_PATH})
    def test_pepys_local_parsers(self):
        value = os.getenv("PEPYS_LOCAL_PARSERS")
        assert value == TEST_IMPORTER_PATH

        file_processor = FileProcessor()
        assert len(file_processor.importers) == 1
        assert file_processor.importers[0].name == "Test Importer"

    @patch.dict(os.environ, {"PEPYS_LOCAL_PARSERS": BAD_IMPORTER_PATH})
    def test_bad_pepys_local_parsers_path(self):
        value = os.getenv("PEPYS_LOCAL_PARSERS")
        assert value == BAD_IMPORTER_PATH

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            file_processor = FileProcessor()
        output = temp_output.getvalue()

        assert len(file_processor.importers) == 0
        assert (
            output
            == f"No such file or directory: {value}. Only core parsers are going to work.\n"
        )

    @patch.dict(os.environ, {"PEPYS_ARCHIVE_LOCATION": "./test_output/"})
    def test_pepys_archive_location(self):
        value = os.getenv("PEPYS_ARCHIVE_LOCATION")
        assert value == "./test_output/"

        file_processor = FileProcessor()
        assert os.path.exists(value) is True
        assert file_processor.output_path == value
        # Remove the test_output directory
        os.rmdir(value)


if __name__ == "__main__":
    unittest.main()
