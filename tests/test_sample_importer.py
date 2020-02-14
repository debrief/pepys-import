import os
import unittest

from pepys_import.file.replay_importer import ReplayImporter
from pepys_import.file.nmea_importer import NMEAImporter
from pepys_import.file.file_processor import FileProcessor


FILE_PATH = os.path.dirname(__file__)
BAD_DATA_PATH = os.path.join(FILE_PATH, "sample_data_bad")
DATA_PATH = os.path.join(FILE_PATH, "sample_data")


class SampleImporterTests(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def tearDown(self) -> None:
        single_level_file = os.path.join(FILE_PATH, "single_level.db")
        if os.path.exists(single_level_file):
            os.remove(single_level_file)

        descending_file = os.path.join(FILE_PATH, "descending.db")
        if os.path.exists(descending_file):
            os.remove(descending_file)

    def test_process_folders_not_descending(self):
        processor = FileProcessor("single_level.db")

        processor.register_importer(ReplayImporter())
        processor.register_importer(NMEAImporter())

        # try bad file
        exception = False
        try:
            processor.process(BAD_DATA_PATH, None, False)
        except FileNotFoundError:
            exception = True
        self.assertTrue(exception)

        # now good one
        processor.process(DATA_PATH, None, False)

    def test_process_folders_descending(self):
        processor = FileProcessor("descending.db")

        processor.register_importer(ReplayImporter())
        processor.register_importer(NMEAImporter())

        # try bad file
        exception = False
        try:
            processor.process(BAD_DATA_PATH, None, True)
        except FileNotFoundError:
            exception = True
        self.assertTrue(exception)

        # now good one
        processor.process(DATA_PATH, None, True)

    def test_process_folders_descending_in_memory(self):
        processor = FileProcessor()

        processor.register_importer(ReplayImporter())
        processor.register_importer(NMEAImporter())

        # try bad file
        exception = False
        try:
            processor.process(BAD_DATA_PATH, None, True)
        except FileNotFoundError:
            exception = True
        self.assertTrue(exception)

        # now good one
        processor.process(DATA_PATH, None, True)


if __name__ == "__main__":
    unittest.main()
