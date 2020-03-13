import unittest
import datetime

from pepys_import.core.formats.location import Location
from pepys_import.core.formats.rep_line import REPLine
from pepys_import.file.highlighter.support.test_utils import create_test_line_object
from contextlib import redirect_stdout
from io import StringIO


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
            1,
            create_test_line_object(" 23 40.25 N 000 01 25.86 E 109.08  6.00  0.00 "),
            " ",
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
        self.assertEqual(Location(60.0, 23.0, 40.25, "S"), rep_line.latitude)
        self.assertEqual(Location(0.0, 1.0, 25.86, "E"), rep_line.longitude)
        self.assertAlmostEqual(1.9038051480754146, rep_line.heading)
        self.assertAlmostEqual(3.086666666666667, rep_line.speed)
        self.assertEqual(0.0, rep_line.depth)
        self.assertEqual("Label", rep_line.text_label)


if __name__ == "__main__":
    unittest.main()
