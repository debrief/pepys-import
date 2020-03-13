import unittest
import os

from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from pepys_import.file.file_processor import FileProcessor

DIRECTORY_PATH = os.path.dirname(__file__)
TEST_IMPORTER_PATH = os.path.join(DIRECTORY_PATH, "samples")
BAD_IMPORTER_PATH = os.path.join(DIRECTORY_PATH, "bad_path")
OUTPUT_PATH = os.path.join(DIRECTORY_PATH, "output")


class EnvironmentVariablesTestCase(unittest.TestCase):
    @patch("pepys_import.file.file_processor.LOCAL_PARSERS", TEST_IMPORTER_PATH)
    def test_pepys_local_parsers(self):
        file_processor = FileProcessor()

        assert len(file_processor.importers) == 1
        assert file_processor.importers[0].name == "Test Importer"

    @patch("pepys_import.file.file_processor.LOCAL_PARSERS", BAD_IMPORTER_PATH)
    def test_bad_pepys_local_parsers_path(self):
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            file_processor = FileProcessor()
        output = temp_output.getvalue()

        assert len(file_processor.importers) == 0
        assert (
            output
            == f"No such file or directory: {BAD_IMPORTER_PATH}. Only core parsers are going to work.\n"
        )

    @patch("pepys_import.file.file_processor.ARCHIVE_PATH", OUTPUT_PATH)
    def test_pepys_archive_location(self):
        file_processor = FileProcessor()
        assert os.path.exists(OUTPUT_PATH) is True
        assert file_processor.output_path == OUTPUT_PATH
        # Remove the test_output directory
        os.rmdir(OUTPUT_PATH)


if __name__ == "__main__":
    unittest.main()
