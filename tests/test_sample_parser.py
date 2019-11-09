import os
import unittest

from pepys_import.file.sample_parser import sample_parser
from pepys_import.file.core_parser import core_parser
from pepys_import.file.file_processor import file_processor


FILE_PATH = os.path.dirname(__file__)


class test_parser_1(core_parser):
    def __init__(self):
        super().__init__("test_1")

    def can_accept_suffix(self, suffix):
        return suffix == ".rep"

    def can_accept_filename(self, filename):
        return "good_file" in filename

    def can_accept_first_line(self, first_line):
        return "good" in first_line

    def can_process_file(self, file_contents):
        return "good" in file_contents

    def process(self, data_store, file_contents):
        pass


class test_parser_2(core_parser):
    def __init__(self):
        super().__init__("test_2")

    def can_accept_suffix(self, suffix):
        return suffix == ".csv"

    def can_accept_filename(self, filename):
        return "good_file" in filename

    def can_accept_first_line(self, first_line):
        return "good" in first_line

    def can_process_file(self, file_contents):
        return "good" in file_contents

    def process(self, data_store, file_contents):
        pass


class SampleParserTests(unittest.TestCase):
    def test_run_class(self):
        parser = sample_parser()

        # suffix
        self.assertFalse(parser.can_accept_suffix("bad"))
        self.assertTrue(parser.can_accept_suffix("rep"))

        # filename
        self.assertFalse(parser.can_accept_filename("bad_file.rep"))
        self.assertTrue(parser.can_accept_filename("good_file.rep"))

        # first line
        self.assertFalse(parser.can_accept_first_line("\\ bad line"))
        self.assertTrue(parser.can_accept_first_line("\\ good line"))

        # file contents
        self.assertFalse(parser.can_process_file("\\ bad\nasd as\n line"))
        self.assertTrue(parser.can_process_file("\\ \n sdfg \n sdfs good \n line"))

        self.assertTrue(parser)

    def test_process_folders(self):
        processor = file_processor()

        processor.register(test_parser_1())
        processor.register(test_parser_2())

        BAD_DATA_PATH = os.path.join(FILE_PATH, "sample_data_bad")
        DATA_PATH = os.path.join(FILE_PATH, "sample_data")

        # try bad file
        exception = False
        try:
            processor.process(BAD_DATA_PATH, None)
        except Exception:
            exception = True
        self.assertTrue(exception)

        # now good one
        processor.process(DATA_PATH, None)

        pass


if __name__ == "__main__":
    unittest.main()
