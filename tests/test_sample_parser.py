import os
import unittest

from pepys_import.file.replay_parser import ReplayParser
from pepys_import.file.nmea_parser import NMEAParser
from pepys_import.file.core_parser import CoreParser
from pepys_import.file.file_processor import FileProcessor


FILE_PATH = os.path.dirname(__file__)
BAD_DATA_PATH = os.path.join(FILE_PATH, "sample_data_bad")
DATA_PATH = os.path.join(FILE_PATH, "sample_data")


@unittest.skip("Skip until parsers are implemented")
class SampleParserTests(unittest.TestCase):
    @unittest.skip
    def test_process_folders_not_descending(self):
        processor = FileProcessor("single_level.db")

        processor.register(ReplayParser())
        processor.register(NMEAParser())

        # try bad file
        exception = False
        try:
            processor.process(BAD_DATA_PATH, None, False)
        except Exception:
            exception = True
        self.assertTrue(exception)

        # now good one
        processor.process(DATA_PATH, None, False)

    @unittest.skip
    def test_process_folders_descending(self):
        processor = FileProcessor("descending.db")

        processor.register(ReplayParser())
        processor.register(NMEAParser())

        # try bad file
        exception = False
        try:
            processor.process(BAD_DATA_PATH, None, True)
        except Exception:
            exception = True
        self.assertTrue(exception)

        # now good one
        processor.process(DATA_PATH, None, True)


if __name__ == "__main__":
    unittest.main()
