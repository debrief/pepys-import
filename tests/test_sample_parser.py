import os
import unittest

from pepys_import.file.replay_parser import replay_parser
from pepys_import.file.nmea_parser import nmea_parser
from pepys_import.file.core_parser import core_parser
from pepys_import.file.file_processor import file_processor


FILE_PATH = os.path.dirname(__file__)


class SampleParserTests(unittest.TestCase):
    def test_process_folders_not_descending(self):
        processor = file_processor()

        processor.register(replay_parser())
        processor.register(nmea_parser())

        BAD_DATA_PATH = os.path.join(FILE_PATH, "sample_data_bad")
        DATA_PATH = os.path.join(FILE_PATH, "sample_data")

        # try bad file
        exception = False
        try:
            processor.process(BAD_DATA_PATH, None, False)
        except Exception:
            exception = True
        self.assertTrue(exception)

        # now good one
        processor.process(DATA_PATH, None, False)

    def test_process_folders_descending(self):
        processor = file_processor()

        processor.register(replay_parser())
        processor.register(nmea_parser())

        BAD_DATA_PATH = os.path.join(FILE_PATH, "sample_data_bad")
        DATA_PATH = os.path.join(FILE_PATH, "sample_data")

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
