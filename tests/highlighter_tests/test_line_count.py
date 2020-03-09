import unittest
import os
from pepys_import.file.highlighter.highlighter import HighlightedFile

path = os.path.abspath(__file__)
dir_path = os.path.dirname(path)
DATA_FILE = os.path.join(dir_path, "sample_files/file.txt")


class SimpleTest(unittest.TestCase):
    ############################
    #### setup and teardown ####
    ############################

    def setUp(self):
        pass

    def tearDown(self):
        pass

    ####################
    #### file tests ####
    ####################

    def test_number_of_lines(self):
        data_file = HighlightedFile(DATA_FILE, 2)

        # get the set of self-describing lines
        lines = data_file.lines()

        chars = data_file.chars_debug()
        self.assertEqual(88, len(chars))
        self.assertEqual(2, len(lines))

        usages = chars[0].usages
        self.assertTrue(usages is not None, "usages should be declared")

    def test_all_lines(self):
        data_file = HighlightedFile(DATA_FILE)

        # get the set of self-describing lines
        lines = data_file.lines()

        chars = data_file.chars_debug()
        self.assertEqual(323, len(chars))
        self.assertEqual(7, len(lines))

        usages = chars[0].usages
        self.assertTrue(usages is not None, "usages should be declared")

    def test_negative_number_of_lines(self):
        with self.assertRaises(SystemExit) as cm:
            data_file = HighlightedFile(DATA_FILE, -5)
            lines = data_file.lines()
            print(lines)  # to avoid unused variable warning

        self.assertEqual(cm.exception.code, 1)

    def test_more_than_lines_number(self):
        data_file = HighlightedFile(DATA_FILE, 200)

        lines = data_file.lines()
        self.assertEqual(len(lines), 7)

    def test_zero_number(self):
        with self.assertRaises(SystemExit) as cm:
            data_file = HighlightedFile(DATA_FILE, 0)
            lines = data_file.lines()
            print(lines)  # to avoid unused variable warning

        self.assertEqual(cm.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
