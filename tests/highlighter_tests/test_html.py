import os
import unittest

from pepys_import.file.highlighter.highlighter import HighlightedFile

path = os.path.abspath(__file__)
dir_path = os.path.dirname(path)

DATA_FILE = os.path.join(dir_path, "sample_files/file.txt")
OUTPUT_FOLDER = os.path.join(dir_path, "sample_files/")


class TestHTML(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        if os.path.exists(os.path.join(OUTPUT_FOLDER, "test_highlighted.html")):
            os.remove(os.path.join(OUTPUT_FOLDER, "test_highlighted.html"))
        pass

    def test_html_is_monospaced(self):
        dataFile = HighlightedFile(DATA_FILE)

        lines = dataFile.lines()
        lines[0].record("Test Name", "Test Field", "Test Value", "Test Units")
        lines[1].record("Test Name 2", "Test Field 2", "Test Value")

        output_file = os.path.join(OUTPUT_FOLDER, "test_highlighted.html")

        dataFile.export(output_file, True)

        with open(output_file, "r") as f:
            output_contents = f.read()

        assert "<html>" in output_contents
        assert '<body style="font-family: Courier">' in output_contents
