import unittest
import os

from unittest.mock import patch

from pepys_import.file.file_processor import FileProcessor


class EnvironmentVariablesTestCase(unittest.TestCase):
    @patch.dict(os.environ, {"PEPYS_LOCAL_PARSERS": "./test_local_imports"})
    def test_pepys_local_parsers(self):
        value = os.getenv("PEPYS_LOCAL_PARSERS")
        assert value == "./test_local_imports"

        file_processor = FileProcessor()
        assert len(file_processor.importers) == 1
        assert file_processor.importers[0].name == "Test Importer"

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
