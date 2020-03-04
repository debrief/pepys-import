import os
import unittest
from datetime import datetime
from pepys_import.file.highlighter.highlighter import HighlightedFile
from pepys_import.file.highlighter.support.combine import combine_tokens

path = os.path.abspath(__file__)
dir_path = os.path.dirname(path)

DATA_FILE = os.path.join(dir_path, "sample_files/file.txt")
OUTPUT_FOLDER = os.path.join(dir_path, "sample_files/")


class UsageRecordingTests(unittest.TestCase):

    ############################
    #### setup and teardown ####
    ############################

    def setUp(self):
        pass

    def tearDown(self):
        if os.path.exists(os.path.join(OUTPUT_FOLDER, "track_lines.html")):
            os.remove(os.path.join(OUTPUT_FOLDER, "track_lines.html"))

    ####################
    #### file tests ####
    ####################

    def parse_timestamp(self, date, time):
        if len(date) == 6:
            formatStr = "%y%m%d"
        else:
            formatStr = "%Y%m%d"

        if len(time) == 6:
            formatStr += "%H%M%S"
        else:
            formatStr += "%H%M%S.%f"

        return datetime.strptime(date + time, formatStr)

    def test_CreateChars(self):
        dataFile = HighlightedFile(DATA_FILE)

        # get the set of self-describing lines
        lines = dataFile.lines()
        self.assertEqual(7, len(lines))

        chars = dataFile.chars_debug()
        assert chars is not None

        self.assertEqual(323, len(chars))

        self.assertEqual("9", chars[0].letter)
        self.assertEqual("5", chars[1].letter)

        usages = chars[0].usages
        self.assertTrue(usages is not None, "usages should be declared")
        self.assertEqual(0, len(usages), "usages should start empty")

    def test_RecordTokens(self):
        dataFile = HighlightedFile(DATA_FILE)

        # get the set of self-describing lines
        lines = dataFile.lines()

        firstLine = lines[0]
        assert firstLine is not None

        tokens = firstLine.tokens()
        self.assertEqual(7, len(tokens))

        tool = "TOOL"
        field = "FIELD"
        value = "VALUE"
        units = "UNITS"

        tokens[0].record(tool, field, value, units)

        chars = dataFile.chars_debug()
        assert chars is not None

        first_entry = chars[0]
        self.assertEqual("9", first_entry.letter)
        self.assertEqual(1, len(first_entry.usages))

        first_usage = first_entry.usages[0]
        self.assertTrue(first_usage is not None, "should have a usage")
        self.assertEqual("TOOL/FIELD", first_usage.tool_field)
        self.assertEqual("Value:VALUE Units:UNITS", first_usage.message)

        # make another recordd
        firstLine.record(field, value)
        self.assertEqual(2, len(first_entry.usages))
        second_usage = first_entry.usages[1]
        self.assertTrue(second_usage is not None, "should have a usage")
        self.assertEqual("FIELD", second_usage.tool_field)
        self.assertEqual("VALUE", second_usage.message)

    def test_multi_lines(self):
        dataFile = HighlightedFile(DATA_FILE)

        tool = "TOOL"

        # get the set of self-describing lines
        lines = dataFile.lines()

        # check the contents of hte print statement
        lineStr = str(lines[0])
        self.assertEqual(
            "Line: (0+(0, 55), 951212 050000.000 MONDEO_44   @C   269.7   10.0      10)",
            lineStr,
        )

        for line in lines:
            tokens = line.tokens()

            if tokens[0].text() == "//":
                dateToken = tokens[2]
                timeToken = tokens[3]
                messageToken = tokens[4]

                dateVal = self.parse_timestamp(dateToken.text(), timeToken.text())
                dateTimeToken = combine_tokens(dateToken, timeToken)
                dateTimeToken.record(tool, "Event DTG", dateVal, "N/A")

                messageToken.record(tool, "Message", messageToken.text(), "N/A")
            else:
                dateToken = tokens[0]
                timeToken = tokens[1]
                vehicleToken = tokens[2]
                courseToken = tokens[4]
                speedToken = tokens[5]
                tempToken = tokens[6]

                dateVal = self.parse_timestamp(dateToken.text(), timeToken.text())
                dateTimeToken = combine_tokens(dateToken, timeToken)
                dateTimeToken.record(tool, "DTG", dateVal, "N/A")
                vehicleToken.record(tool, "NAME", vehicleToken.text(), "N/A")
                courseToken.record(tool, "Course", courseToken.text(), "Degs")
                speedToken.record(tool, "Speed", speedToken.text(), "M/Sec")
                tempToken.record(tool, "Temperature", tempToken.text(), "Deg C")

                # also send the temperature somewhewre else
                tempToken.record(
                    "Third Party Temp Tracker", "Env Tmp", tempToken.text(), "Deg C"
                )

        dataFile.export(os.path.join(OUTPUT_FOLDER, "track_lines.html"), True)


if __name__ == "__main__":
    unittest.main()
