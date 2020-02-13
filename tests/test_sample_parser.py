import os
import unittest

from pepys_import.file.replay_parser import ReplayParser
from pepys_import.file.nmea_parser import NMEAParser
from pepys_import.file.file_processor import FileProcessor


FILE_PATH = os.path.dirname(__file__)
BAD_DATA_PATH = os.path.join(FILE_PATH, "sample_data_bad")
DATA_PATH = os.path.join(FILE_PATH, "sample_data")


class SampleParserTests(unittest.TestCase):
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

        processor.register(ReplayParser())
        processor.register(NMEAParser())

        # try bad file
        exception = False
        try:
            processor.process(BAD_DATA_PATH, None, False)
        except BaseException:
            exception = True
        self.assertTrue(exception)

        # now good one
        processor.process(DATA_PATH, None, False)

    def test_process_folders_descending(self):
        processor = FileProcessor("descending.db")

        processor.register(ReplayParser())
        processor.register(NMEAParser())

        # try bad file
        exception = False
        try:
            processor.process(BAD_DATA_PATH, True)
        except Exception:
            exception = True
        self.assertTrue(exception)

        # now good one
        processor.process(DATA_PATH, True)


if __name__ == "__main__":
    unittest.main()
