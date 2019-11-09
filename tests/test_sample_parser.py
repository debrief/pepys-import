import os
import unittest

from pepys_import.file.sample_parser import sample_parser


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
        pass


if __name__ == "__main__":
    unittest.main()
