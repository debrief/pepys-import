import os
import unittest

from pepys_import.core.formats.repl_file import REPFile

FILE_PATH = os.path.dirname(__file__)
TEST_DATA_PATH = os.path.join(FILE_PATH, "sample_data", "track_files", "rep_data")
TEST_FILE = os.path.join(TEST_DATA_PATH, "rep_test1.rep")
BROKEN_FILE = os.path.join(TEST_DATA_PATH, "rep_test2.rep")


class BasicTests(unittest.TestCase):
    def test_file_not_found(self):
        exception = False
        try:
            REPFile("non_existing.rep")
        except IOError:
            exception = True

        self.assertTrue(exception)

    def test_get_file_type(self):
        rep_file = REPFile(TEST_FILE)
        self.assertEqual("REP", rep_file.datafile_type)

    def test_get_file_name(self):
        rep_file = REPFile(TEST_FILE)
        self.assertEqual(TEST_FILE, rep_file.filepath)

    def test_get_all_lines(self):
        rep_file = REPFile(TEST_FILE)
        self.assertEqual(8, len(rep_file.lines))

    def test_file_types(self):
        rep_file = REPFile(TEST_FILE)
        self.assertEqual("REP", rep_file.datafile_type)
        self.assertEqual(TEST_FILE, rep_file.filepath)

    def test_file_parse_error(self):
        exception = False
        try:
            REPFile(BROKEN_FILE)
        except Exception:
            exception = True

        self.assertTrue(exception)


if __name__ == "__main__":
    unittest.main()
