import os
import unittest
from datetime import datetime
from pepys_import.file.highlighter.highlighter import HighlightedFile
from pepys_import.file.highlighter.support.combine import combine_tokens
from pepys_import.file.highlighter.support.export import export_report


path = os.path.abspath(__file__)
dir_path = os.path.dirname(path)
TEST_FILE = os.path.join(dir_path, "sample_files/reptest1.rep")
NMEA_FILE = os.path.join(dir_path, "sample_files/NMEA_out.txt")

DATA_FILE = os.path.join(dir_path, "sample_files/file.txt")


class CombineTokenTests(unittest.TestCase):

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

    def parse_location(self, lat, lat_hem, lon, long_hem):
        latDegs = float(lat[0:2])
        latMins = float(lat[2:4])
        latSecs = float(lat[4:])
        latDegs = latDegs + latMins / 60 + latSecs / 60 / 60

        lonDegs = float(lon[0:3])
        lonMins = float(lon[3:5])
        lonSecs = float(lon[5:])
        lonDegs = lonDegs + lonMins / 60 + lonSecs / 60 / 60

        if lat_hem == "S":
            latDegs = -1 * latDegs

        if lat_hem == "W":
            lonDegs = -1 * lonDegs

        return (latDegs, lonDegs)

    def test_CombineSingleLine(self):
        dataFile = HighlightedFile(DATA_FILE, 1)

        # get the set of self-describing lines
        lines = dataFile.lines()

        tokens = lines[0].tokens()

        self.assertEqual(7, len(tokens))

        dateToken = tokens[0]
        timeToken = tokens[1]
        dateTimeToken = combine_tokens(dateToken, timeToken)

        date_time = self.parse_timestamp(dateToken.text(), timeToken.text())

        dateTimeToken.record("TOOL", "Date-Time", date_time, "N/A")

        chars = dataFile.chars_debug()
        assert chars is not None

        ctr = 0
        for char in chars:
            if ctr == 22:
                break
            ctr = ctr + 1

            if ctr > 0 and ctr <= 6:
                usages = char.usages
                self.assertEqual(1, len(usages))
                self.assertEqual(
                    "Value:1995-12-12 05:00:00 Units:N/A", usages[0].message
                )
            elif ctr > 7 and ctr <= 17:
                usages = char.usages
                self.assertEqual(1, len(usages))
                self.assertEqual(
                    "Value:1995-12-12 05:00:00 Units:N/A", usages[0].message
                )

    def test_CombineTokensOnMultipleLines(self):
        dataFile = HighlightedFile(NMEA_FILE, 50)

        # get the set of self-describing lines
        lines = dataFile.lines()

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

                msg_type = tokens[1].text()
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

                    date_time = self.parse_timestamp(date_tok.text(), time_tok.text())

                    loc = self.parse_location(
                        lat_tok.text(),
                        lat_hem_tok.text(),
                        long_tok.text(),
                        long_hem_tok.text(),
                    )
                    spd = float(spd_tok.text())
                    hdg = float(hdg_tok.text())

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
                    big_token.record(
                        "NMEA Import", "Date:" + str(date_time), msg, "N/A"
                    )

                    date_tok = None
                    spd_tok = None
                    hdg_tok = None
                    lat_tok = None

        dataFile.export("nmea.html")

    def test_CombineLinesOnMultipleLines(self):
        dataFile = HighlightedFile(NMEA_FILE, 50)

        # get the set of self-describing lines
        lines = dataFile.lines()

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

                msg_type = tokens[1].text()

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

                    date_time = self.parse_timestamp(date_tok.text(), time_tok.text())

                    loc = self.parse_location(
                        lat_tok.text(),
                        lat_hem_tok.text(),
                        long_tok.text(),
                        long_hem_tok.text(),
                    )
                    spd = float(spd_tok.text())
                    hdg = float(hdg_tok.text())

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

                    line_composite = combine_tokens(
                        date_line, loc_line, spd_line, hdg_line
                    )

                    line_composite.record(
                        "NMEA Import", "Date:" + str(date_time), msg, "N/A"
                    )

                    date_tok = None
                    spd_tok = None
                    hdg_tok = None
                    lat_tok = None

        dataFile.export("nmea2.html")


if __name__ == "__main__":
    unittest.main()
