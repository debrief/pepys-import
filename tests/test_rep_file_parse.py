import unittest
import datetime

from pepys_import.core.formats import unit_registry
from pepys_import.core.formats.location import Location
from pepys_import.core.formats.state import State


class BasicTests(unittest.TestCase):
    def test_long_timestamp(self):
        # long date
        rep_line = State(
            1,
            "19951212 120800 SUBJECT VC 60 23 40.25 N 000 01 25.86 E 109.08  6.00  NaN Label",
        )
        self.assertTrue(rep_line.parse())
        self.assertEqual(str(rep_line.timestamp.date()), "1995-12-12")

        # long time
        rep_line = State(
            1,
            "951212 120800.555 SUBJECT VC 60 23 40.25 N 000 01 25.86 E 109.08  6.00  0.00 ",
        )
        self.assertTrue(rep_line.parse())
        self.assertEqual(str(rep_line.timestamp.time()), "12:08:00.555000")

    def test_error_reports(self):
        # too few fields
        rep_line = State(1, " 23 40.25 N 000 01 25.86 E 109.08  6.00  0.00 ")
        self.assertFalse(rep_line.parse())

        # wrong length date
        rep_line = State(
            1, "12 120800 SUBJECT VC 60 23 40.25 N 000 01 25.86 E 109.08  6.00  0.00 "
        )
        self.assertFalse(rep_line.parse())

        # wrong length time
        rep_line = State(
            1, "951212 12 SUBJECT VC 60 23 40.25 N 000 01 25.86 E 109.08  6.00  0.00 "
        )
        self.assertFalse(rep_line.parse())

        # wrong length symbology
        rep_line = State(
            1,
            "951212 120800 SUBJECT VCC 60 23 40.25 N 000 01 25.86 E 109.08  6.00  0.00 ",
        )
        self.assertFalse(rep_line.parse())

        # wrong symbology
        rep_line = State(
            1,
            "951212 120800 SUBJECT VC[VC[VC 60 23 40.25 N 000 01 25.86 E 109.08  6.00  0.00 ",
        )
        self.assertFalse(rep_line.parse())
        # bad latitude
        rep_line = State(
            1,
            "951212 120800 SUBJECT VC 6A 23 40.25 N 000 01 25.86 E 109.08  6.00  0.00 ",
        )
        self.assertFalse(rep_line.parse())

        # bad longitude
        rep_line = State(
            1,
            "951212 120800 SUBJECT VC 60 23 40.25 N 00A 01 2B.86 E 109.08  6.00  0.00 ",
        )
        self.assertFalse(rep_line.parse())

        # bad heading
        rep_line = State(
            1,
            "951212 120800 SUBJECT VC 60 23 40.25 N 000 01 25.86 E 1000.00  6.00  0.00 ",
        )
        self.assertFalse(rep_line.parse())

        # bad heading
        rep_line = State(
            1,
            "951212 120800 SUBJECT VC 60 23 40.25 N 000 01 25.86 E 10b.08  6.00  0.00 ",
        )
        self.assertFalse(rep_line.parse())

        # bad speed
        rep_line = State(
            1,
            "951212 120800 SUBJECT VC 60 23 40.25 N 000 01 25.86 E 109.08  6.b0  0.00 ",
        )
        self.assertFalse(rep_line.parse())

        # bad depth
        rep_line = State(
            1,
            "951212 120800 SUBJECT VC 60 23 40.25 N 000 01 25.86 E 109.08  6.00  0.c0 ",
        )
        self.assertFalse(rep_line.parse())

    def test_line_ok(self):
        rep_line = State(
            1,
            "100112 120800 SUBJECT VC 60 23 40.25 N 000 01 25.86 E 109.08  6.00  0.00 ",
        )
        self.assertTrue(rep_line.parse())

        self.assertEqual(1, rep_line.line_num)
        self.assertEqual(datetime.datetime(2010, 1, 12, 12, 8), rep_line.timestamp)
        self.assertEqual("SUBJECT", rep_line.get_platform())
        self.assertEqual("VC", rep_line.symbology)
        self.assertEqual(Location(60.0, 23.0, 40.25, "N"), rep_line.latitude)
        self.assertEqual(Location(0.0, 1.0, 25.86, "E"), rep_line.longitude)
        self.assertAlmostEqual(1.9038051480754146, rep_line.heading)
        self.assertAlmostEqual(6.00, rep_line.speed.to(unit_registry.knot).magnitude)
        self.assertEqual(0.0, rep_line.depth)
        self.assertEqual(None, rep_line.text_label)


if __name__ == "__main__":
    unittest.main()
