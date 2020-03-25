import os
import unittest
from datetime import datetime

from pepys_import.file.highlighter.highlighter import HighlightedFile
from pepys_import.file.highlighter.support.combine import combine_tokens

PATH = os.path.abspath(__file__)
DIR_PATH = os.path.dirname(PATH)

DATA_FILE = os.path.join(DIR_PATH, "sample_files/file.txt")
OUTPUT_FOLDER = os.path.join(DIR_PATH, "sample_files/")


class UsageRecordingTests(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        if os.path.exists(os.path.join(OUTPUT_FOLDER, "track_lines.html")):
            os.remove(os.path.join(OUTPUT_FOLDER, "track_lines.html"))

    def parse_timestamp(self, date, time):
        if len(date) == 6:
            format_str = "%y%m%d"
        else:
            format_str = "%Y%m%d"

        if len(time) == 6:
            format_str += "%H%M%S"
        else:
            format_str += "%H%M%S.%f"

        return datetime.strptime(date + time, format_str)

    def test_create_chars(self):
        data_file = HighlightedFile(DATA_FILE)

        # get the set of self-describing lines
        lines = data_file.lines()
        self.assertEqual(7, len(lines))

        chars = data_file.chars_debug()
        assert chars is not None

        self.assertEqual(323, len(chars))

        self.assertEqual("9", chars[0].letter)
        self.assertEqual("5", chars[1].letter)

        usages = chars[0].usages
        self.assertTrue(usages is not None, "usages should be declared")
        self.assertEqual(0, len(usages), "usages should start empty")

    def test_record_tokens(self):
        data_file = HighlightedFile(DATA_FILE)

        # get the set of self-describing lines
        lines = data_file.lines()

        first_line = lines[0]
        assert first_line is not None

        tokens = first_line.tokens()
        self.assertEqual(7, len(tokens))

        tool = "TOOL"
        field = "FIELD"
        value = "VALUE"
        units = "UNITS"

        tokens[0].record(tool, field, value, units)

        chars = data_file.chars_debug()
        assert chars is not None

        first_entry = chars[0]
        self.assertEqual("9", first_entry.letter)
        self.assertEqual(1, len(first_entry.usages))

        first_usage = first_entry.usages[0]
        self.assertTrue(first_usage is not None, "should have a usage")
        self.assertEqual("TOOL/FIELD", first_usage.tool_field)
        self.assertEqual("Value:VALUE Units:UNITS", first_usage.message)

        # make another recordd
        first_line.record(tool, field, value, units)
        self.assertEqual(2, len(first_entry.usages))
        second_usage = first_entry.usages[1]
        self.assertTrue(second_usage is not None, "should have a usage")
        self.assertEqual("TOOL/FIELD", second_usage.tool_field)
        self.assertEqual("Value:VALUE Units:UNITS", second_usage.message)

    def test_multi_lines(self):
        data_file = HighlightedFile(DATA_FILE)

        tool = "TOOL"

        # get the set of self-describing lines
        lines = data_file.lines()

        # check the contents of hte print statement
        line_str = str(lines[0])
        self.assertEqual(
            "Line: (0+(0, 55), 951212 050000.000 MONDEO_44   @C   269.7   10.0      10)", line_str,
        )

        for line in lines:
            tokens = line.tokens()

            if tokens[0].text == "//":
                date_token = tokens[2]
                time_token = tokens[3]
                message_token = tokens[4]

                date_val = self.parse_timestamp(date_token.text, time_token.text)
                date_time_token = combine_tokens(date_token, time_token)
                date_time_token.record(tool, "Event DTG", date_val, "N/A")

                message_token.record(tool, "Message", message_token.text, "N/A")
            else:
                date_token = tokens[0]
                time_token = tokens[1]
                vehicle_token = tokens[2]
                course_token = tokens[4]
                speed_token = tokens[5]
                temp_token = tokens[6]

                date_val = self.parse_timestamp(date_token.text, time_token.text)
                date_time_token = combine_tokens(date_token, time_token)
                date_time_token.record(tool, "DTG", date_val, "N/A")
                vehicle_token.record(tool, "NAME", vehicle_token.text, "N/A")
                course_token.record(tool, "Course", course_token.text, "Degs")
                speed_token.record(tool, "Speed", speed_token.text, "M/Sec")
                temp_token.record(tool, "Temperature", temp_token.text, "Deg C")

                # also send the temperature somewhewre else
                temp_token.record("Third Party Temp Tracker", "Env Tmp", temp_token.text, "Deg C")

        data_file.export(os.path.join(OUTPUT_FOLDER, "track_lines.html"), True)


if __name__ == "__main__":
    unittest.main()
