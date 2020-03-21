import os
import unittest

from pepys_import.file.highlighter.highlighter import HighlightedFile

path = os.path.abspath(__file__)
dir_path = os.path.dirname(path)
TEST_FILE = os.path.join(dir_path, "sample_files/reptest1.rep")

DATA_FILE = os.path.join(dir_path, "sample_files/file.txt")
COMMA_FILE = os.path.join(dir_path, "sample_files/file_comma.txt")


class SimpleTests(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_SplitLoadFile(self):
        data_file = HighlightedFile(DATA_FILE)
        assert data_file is not None

    def test_SplitLines(self):
        data_file = HighlightedFile(DATA_FILE)

        # get the set of self-describing lines
        lines = data_file.lines()

        self.assertEqual(7, len(lines))

    def test_SplitCommaTokens(self):
        data_file = HighlightedFile(COMMA_FILE)

        # get the set of self-describing lines
        lines = data_file.lines()

        first_line = lines[0]
        assert first_line is not None

        # FixMe - this next constant should be declared in class module
        csv_delim = r'(?:,"|^")(""|[\w\W]*?)(?=",|"$)|(?:,(?!")|^(?!"))([^,]*?)(?=$|,)|(\r\n|\n)'

        tokens = first_line.tokens(csv_delim, ",")
        self.assertEqual(7, len(tokens))

        self.assertEqual("951212", tokens[0].text)

    def test_SplitTokens(self):
        data_file = HighlightedFile(DATA_FILE)

        # get the set of self-describing lines
        lines = data_file.lines()

        first_line = lines[0]
        assert first_line is not None

        tokens = first_line.tokens()
        self.assertEqual(7, len(tokens))

        first_token = tokens[0]

        assert first_token is not None

        self.assertEqual("951212", tokens[0].text)
        self.assertEqual("050000.000", tokens[1].text)
        self.assertEqual("MONDEO_44", tokens[2].text)
        self.assertEqual("@C", tokens[3].text)
        self.assertEqual("269.7", tokens[4].text)
        self.assertEqual("10.0", tokens[5].text)
        self.assertEqual("10", tokens[6].text)

        second_line = lines[1]
        assert second_line is not None

        tokens = second_line.tokens()
        self.assertEqual(5, len(tokens))

        self.assertEqual("//", tokens[0].text)
        self.assertEqual("EVENT", tokens[1].text)
        self.assertEqual("951212", tokens[2].text)
        self.assertEqual("050300.000", tokens[3].text)
        self.assertEqual("BRAVO", tokens[4].text)
