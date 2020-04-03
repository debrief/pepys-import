import datetime
import unittest
from contextlib import redirect_stdout
from io import StringIO
from math import isnan

from pepys_import.core.formats import unit_registry
from pepys_import.core.formats.location import Location
from pepys_import.core.formats.rep_line import REPLine
from pepys_import.file.highlighter.support.test_utils import create_test_line_object


class BasicTests(unittest.TestCase):
    def setUp(self) -> None:
        self.error = list()
        self.message = "Test"

    def test_long_timestamp(self):
        # long date
        rep_line = REPLine(
            1,
            create_test_line_object(
                "19951212 120800 SUBJECT VC 60 23 40.25 N 000 01 25.86 E 109.08  6.00  NaN"
            ),
            " ",
        )
        self.assertTrue(rep_line.parse(self.error, self.message))
        self.assertEqual(str(rep_line.timestamp.date()), "1995-12-12")

        # long time
        rep_line = REPLine(
            1,
            create_test_line_object(
                "951212 120800.555 SUBJECT VC 60 23 40.25 N 000 01 25.86 E 109.08  6.00  0.00 "
            ),
            " ",
        )
        self.assertTrue(rep_line.parse(self.error, self.message))
        self.assertEqual(str(rep_line.timestamp.time()), "12:08:00.555000")

    def test_error_reports(self):
        # too few fields
        rep_line = REPLine(
            1, create_test_line_object(" 23 40.25 N 000 01 25.86 E 109.08  6.00  0.00 "), " ",
        )
        self.assertFalse(rep_line.parse(self.error, self.message))

        # wrong length date
        rep_line = REPLine(
            1,
            create_test_line_object(
                "12 120800 SUBJECT VC 60 23 40.25 N 000 01 25.86 E 109.08  6.00  0.00 "
            ),
            " ",
        )
        self.assertFalse(rep_line.parse(self.error, self.message))

        # wrong length time
        rep_line = REPLine(
            1,
            create_test_line_object(
                "951212 12 SUBJECT VC 60 23 40.25 N 000 01 25.86 E 109.08  6.00  0.00 "
            ),
            " ",
        )
        self.assertFalse(rep_line.parse(self.error, self.message))

        # wrong length symbology
        rep_line = REPLine(
            1,
            create_test_line_object(
                "951212 120800 SUBJECT VCC 60 23 40.25 N 000 01 25.86 E 109.08  6.00  0.00 "
            ),
            " ",
        )
        self.assertFalse(rep_line.parse(self.error, self.message))

        # wrong symbology
        rep_line = REPLine(
            1,
            create_test_line_object(
                "951212 120800 SUBJECT VC[VC[VC 60 23 40.25 N 000 01 25.86 E 109.08  6.00  0.00 "
            ),
            " ",
        )
        self.assertFalse(rep_line.parse(self.error, self.message))
        # bad latitude
        rep_line = REPLine(
            1,
            create_test_line_object(
                "951212 120800 SUBJECT VC 6A 23 40.25 N 000 01 25.86 E 109.08  6.00  0.00 "
            ),
            " ",
        )
        self.assertFalse(rep_line.parse(self.error, self.message))

        # bad longitude
        rep_line = REPLine(
            1,
            create_test_line_object(
                "951212 120800 SUBJECT VC 60 23 40.25 N 00A 01 2B.86 E 109.08  6.00  0.00 "
            ),
            " ",
        )
        self.assertFalse(rep_line.parse(self.error, self.message))

        # bad heading
        rep_line = REPLine(
            1,
            create_test_line_object(
                "951212 120800 SUBJECT VC 60 23 40.25 N 000 01 25.86 E 10b.08  6.00  0.00 "
            ),
            " ",
        )
        self.assertFalse(rep_line.parse(self.error, self.message))

        # bad speed
        rep_line = REPLine(
            1,
            create_test_line_object(
                "951212 120800 SUBJECT VC 60 23 40.25 N 000 01 25.86 E 109.08  6.b0  0.00 "
            ),
            " ",
        )
        self.assertFalse(rep_line.parse(self.error, self.message))

        # bad depth
        rep_line = REPLine(
            1,
            create_test_line_object(
                "951212 120800 SUBJECT VC 60 23 40.25 N 000 01 25.86 E 109.08  6.00  0.c0 "
            ),
            " ",
        )
        self.assertFalse(rep_line.parse(self.error, self.message))

    def test_line_ok(self):
        rep_line = REPLine(
            line_number=1,
            line=create_test_line_object(
                "100112\t120800\tSUBJECT\tVC\t60\t23\t40.25\tS\t000\t01\t25.86\tE\t109.08\t6.00\t0.00\tLabel"
            ),
            separator="\t",
        )
        self.assertTrue(rep_line.parse(self.error, self.message))

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            rep_line.print()
        rep_line.print()
        output = temp_output.getvalue()
        self.assertIn("REP Line 1 - Timestamp: 2010-01-12 12:08:00", output)
        self.assertEqual(1, rep_line.line_num)
        self.assertEqual(datetime.datetime(2010, 1, 12, 12, 8), rep_line.timestamp)
        self.assertEqual("SUBJECT", rep_line.get_platform())
        self.assertEqual("VC", rep_line.symbology)
        correct_loc = Location()
        correct_loc.set_latitude_dms(60.0, 23.0, 40.25, "S")
        correct_loc.set_longitude_dms(0.0, 1.0, 25.86, "E")
        self.assertEqual(correct_loc, rep_line.location)
        self.assertAlmostEqual(1.9038051480754146, rep_line.heading)
        self.assertAlmostEqual(6 * unit_registry.knot, rep_line.speed)
        self.assertEqual(0.0, rep_line.depth)
        self.assertEqual("Label", rep_line.text_label)

    def test_zero_mins_secs(self):
        rep_line = REPLine(
            line_number=1,
            line=create_test_line_object(
                "100112\t120800\tSUBJECT\tVC\t53.243\t0\t0\tS\t23.495\t00\t0\tE\t109.08\t6.00\t0.00\tLabel"
            ),
            separator="\t",
        )
        assert rep_line.parse(self.error, self.message)

        correct_loc = Location()
        correct_loc.set_latitude_decimal_degrees(-53.243)
        correct_loc.set_longitude_decimal_degrees(23.495)
        assert correct_loc == rep_line.location

    def test_zero_secs(self):
        rep_line = REPLine(
            line_number=1,
            line=create_test_line_object(
                "100112\t120800\tSUBJECT\tVC\t53\t45.32\t0\tS\t23\t56.23\t0\tE\t109.08\t6.00\t0.00\tLabel"
            ),
            separator="\t",
        )
        assert rep_line.parse(self.error, self.message)

        correct_loc = Location()
        correct_loc.set_latitude_dms(53, 45.32, 0, "S")
        correct_loc.set_longitude_dms(23, 56.23, 0, "E")
        assert correct_loc == rep_line.location

    def test_nan_depth(self):
        rep_line = REPLine(
            line_number=1,
            line=create_test_line_object(
                "100112\t120800\tSUBJECT\tVC\t60\t23\t40.25\tS\t000\t01\t25.86\tE\t109.08\t6.00\tNaN\tLabel"
            ),
            separator="\t",
        )
        assert rep_line.parse(self.error, self.message)

        assert rep_line.depth is None

    def test_extended_symbology(self):
        rep_line = REPLine(
            line_number=1,
            line=create_test_line_object(
                "100112\t120800\tSUBJECT\t@C[SYMBOL=torpedo,LAYER=Support]\t60\t23\t40.25\tS\t000\t01\t25.86\tE\t109.08\t6.00\t0.0\tLabel"
            ),
            separator="\t",
        )
        assert rep_line.parse(self.error, self.message)

        correct_loc = Location()
        correct_loc.set_latitude_dms(60.0, 23.0, 40.25, "S")
        correct_loc.set_longitude_dms(0.0, 1.0, 25.86, "E")

        assert rep_line.location == correct_loc
        assert rep_line.get_platform() == "SUBJECT"


if __name__ == "__main__":
    unittest.main()
