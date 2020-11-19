import os
import unittest
from datetime import datetime

from pepys_import.file.highlighter.highlighter import HighlightedFile
from pepys_import.file.highlighter.support.combine import combine_tokens

PATH = os.path.abspath(__file__)
DIR_PATH = os.path.dirname(PATH)
TEST_FILE = os.path.join(DIR_PATH, "sample_files/reptest1.rep")
NMEA_FILE = os.path.join(DIR_PATH, "sample_files/NMEA_out.txt")

DATA_FILE = os.path.join(DIR_PATH, "sample_files/file.txt")
OUTPUT_FOLDER = os.path.join(DIR_PATH, "sample_files/")


class CombineTokenTests(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        files_to_delete = ["nmea.html", "nmea2.html"]

        for f in files_to_delete:
            if os.path.exists(os.path.join(OUTPUT_FOLDER, f)):
                os.remove(os.path.join(OUTPUT_FOLDER, f))

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

    def parse_location(self, lat, lat_hem, lon, long_hem):
        lat_degs = float(lat[0:2])
        lat_mins = float(lat[2:4])
        lat_secs = float(lat[4:])
        lat_degs = lat_degs + lat_mins / 60 + lat_secs / 60 / 60

        lon_degs = float(lon[0:3])
        lon_mins = float(lon[3:5])
        lon_secs = float(lon[5:])
        lon_degs = lon_degs + lon_mins / 60 + lon_secs / 60 / 60

        if lat_hem == "S":
            lat_degs = -1 * lat_degs

        if lat_hem == "W":
            lon_degs = -1 * lon_degs

        return lat_degs, lon_degs

    def test_combine_single_line(self):
        data_file = HighlightedFile(DATA_FILE, 1)

        # get the set of self-describing lines
        lines = data_file.lines()

        tokens = lines[0].tokens()

        self.assertEqual(7, len(tokens))

        date_token = tokens[0]
        time_token = tokens[1]
        date_time_token = combine_tokens(date_token, time_token)

        date_time = self.parse_timestamp(date_token.text, time_token.text)

        date_time_token.record("TOOL", "Date-Time", date_time, "N/A")

        chars = data_file.chars_debug()
        assert chars is not None

        ctr = 0
        for char in chars:
            if ctr == 22:
                break
            ctr = ctr + 1

            if 0 < ctr <= 6:
                usages = char.usages
                self.assertEqual(1, len(usages))
                self.assertEqual("Value:1995-12-12 05:00:00 Units:N/A", usages[0].message)
            elif 7 < ctr <= 17:
                usages = char.usages
                self.assertEqual(1, len(usages))
                self.assertEqual("Value:1995-12-12 05:00:00 Units:N/A", usages[0].message)

    def test_combine_tokens_on_multiple_lines(self):
        data_file = HighlightedFile(NMEA_FILE, 50)

        # get the set of self-describing lines
        lines = data_file.lines()

        nmea_delim = "([^,]+|(?<=,)(?=,)|^(?=,)|(?<=,)$)"

        lat_tok = None
        lat_hem_tok = None
        long_tok = None
        long_hem_tok = None
        date_tok = None
        time_tok = None
        hdg_tok = None
        spd_tok = None

        for line in lines:
            tokens = line.tokens(nmea_delim, ",")
            if len(tokens) > 0:

                msg_type = tokens[1].text
                if msg_type == "DZA":
                    date_tok = tokens[2]
                    time_tok = tokens[3]
                elif msg_type == "VEL":
                    spd_tok = tokens[6]
                elif msg_type == "HDG":
                    hdg_tok = tokens[2]
                elif msg_type == "POS":
                    lat_tok = tokens[3]
                    lat_hem_tok = tokens[4]
                    long_tok = tokens[5]
                    long_hem_tok = tokens[6]

                # do we have all we need?
                if date_tok and spd_tok and hdg_tok and lat_tok:

                    date_time = self.parse_timestamp(date_tok.text, time_tok.text)

                    loc = self.parse_location(
                        lat_tok.text,
                        lat_hem_tok.text,
                        long_tok.text,
                        long_hem_tok.text,
                    )
                    spd = float(spd_tok.text)
                    hdg = float(hdg_tok.text)

                    fStr = "{:8.2f}"

                    msg = (
                        "Date:"
                        + str(date_time)
                        + ", Loc:()"
                        + fStr.format(loc[0])
                        + ", "
                        + fStr.format(loc[1])
                        + "), Spd:"
                        + fStr.format(spd)
                        + ", Hdg:"
                        + fStr.format(hdg)
                    )

                    big_token = combine_tokens(
                        lat_tok,
                        lat_hem_tok,
                        long_tok,
                        long_hem_tok,
                        spd_tok,
                        hdg_tok,
                        date_tok,
                        time_tok,
                    )
                    big_token.record("NMEA Import", "Date:" + str(date_time), msg, "N/A")

                    date_tok = None
                    spd_tok = None
                    hdg_tok = None
                    lat_tok = None

        data_file.export(os.path.join(OUTPUT_FOLDER, "nmea.html"))

    def test_combine_lines_on_multiple_lines_with_multiple(self):
        data_file = HighlightedFile(NMEA_FILE)

        # get the set of self-describing lines
        lines = data_file.lines()

        nmea_delim = "([^,]+|(?<=,)(?=,)|^(?=,)|(?<=,)$)"

        lat_tok = None
        lat_hem_tok = None
        long_tok = None
        long_hem_tok = None
        date_tok = None
        time_tok = None
        hdg_tok = None
        spd_tok = None

        date_line = None
        loc_line = None
        hdg_line = None
        spd_line = None

        for line in lines:
            tokens = line.tokens(nmea_delim, ",")
            if len(tokens) > 0:

                msg_type = tokens[1].text

                if msg_type == "DZA":
                    date_tok = tokens[2]
                    time_tok = tokens[3]
                    date_line = line
                elif msg_type == "VEL":
                    spd_tok = tokens[6]
                    spd_line = line
                elif msg_type == "HDG":
                    hdg_tok = tokens[2]
                    hdg_line = line
                elif msg_type == "POS":
                    lat_tok = tokens[3]
                    lat_hem_tok = tokens[4]
                    long_tok = tokens[5]
                    long_hem_tok = tokens[6]
                    loc_line = line

                # do we have all we need?
                if date_tok and spd_tok and hdg_tok and lat_tok:

                    date_time = self.parse_timestamp(date_tok.text, time_tok.text)

                    loc = self.parse_location(
                        lat_tok.text,
                        lat_hem_tok.text,
                        long_tok.text,
                        long_hem_tok.text,
                    )
                    spd = float(spd_tok.text)
                    hdg = float(hdg_tok.text)

                    fStr = "{:8.2f}"

                    msg = (
                        "Date:"
                        + str(date_time)
                        + ", Loc:()"
                        + fStr.format(loc[0])
                        + ", "
                        + fStr.format(loc[1])
                        + "), Spd:"
                        + fStr.format(spd)
                        + ", Hdg:"
                        + fStr.format(hdg)
                    )

                    line_composite = combine_tokens(date_line, loc_line, spd_line, hdg_line)

                    line_composite.record("NMEA Import", "Date:" + str(date_time), msg, "N/A")

                    date_tok = None
                    spd_tok = None
                    hdg_tok = None
                    lat_tok = None

        data_file.export(os.path.join(OUTPUT_FOLDER, "nmea2.html"))


if __name__ == "__main__":
    unittest.main()
