import unittest
import datetime

from pepys_import.core.formats import unit_registry
from pepys_import.core.formats.state import State


@unittest.skip("Skip until parsers are implemented")
class BasicTests(unittest.TestCase):
    def test_long_timestamp(self):
        # long date
        rep_line = State(
            1,
            "19951212 120800 SUBJECT VC 60 23 40.25 N 000 01 25.86 E 109.08  6.00  0.00 ",
        )
        rep_line.parse()

        # long time
        rep_line = State(
            1,
            "951212 120800.555 SUBJECT VC 60 23 40.25 N 000 01 25.86 E 109.08  6.00  0.00 ",
        )
        rep_line.parse()

    def test_Getters(self):
        rep_line = State(
            1,
            "951212 120800.555 SUBJECT VC 60 23 40.25 N 000 01 25.86 E 109.08  6.00  0.00 ",
        )
        rep_line.parse()

        rep_line.get_line_number
        rep_line.get_timestamp
        rep_line.get_platform
        rep_line.get_symbology
        rep_line.get_latitude
        rep_line.get_longitude
        rep_line.get_heading
        rep_line.get_speed
        rep_line.get_depth
        rep_line.get_text_label

    def test_error_reports(self):
        # too few fields
        rep_line = State(1, " 23 40.25 N 000 01 25.86 E 109.08  6.00  0.00 ")
        rep_line.parse()

        # wrong length date
        rep_line = State(
            1, "12 120800 SUBJECT VC 60 23 40.25 N 000 01 25.86 E 109.08  6.00  0.00 "
        )
        rep_line.parse()

        # wrong length time
        rep_line = State(
            1, "951212 12 SUBJECT VC 60 23 40.25 N 000 01 25.86 E 109.08  6.00  0.00 "
        )
        rep_line.parse()

        # wrong length symbology
        rep_line = State(
            1,
            "951212 120800 SUBJECT VCC 60 23 40.25 N 000 01 25.86 E 109.08  6.00  0.00 ",
        )
        rep_line.parse()

        # bad latitude
        rep_line = State(
            1,
            "951212 120800 SUBJECT VC 6A 23 40.25 N 000 01 25.86 E 109.08  6.00  0.00 ",
        )
        rep_line.parse()

        # bad longtude
        rep_line = State(
            1,
            "951212 120800 SUBJECT VC 60 23 40.25 N 00A 01 2B.86 E 109.08  6.00  0.00 ",
        )
        rep_line.parse()

        # bad course
        rep_line = State(
            1,
            "951212 120800 SUBJECT VC 60 23 40.25 N 000 01 25.86 E 10a.08  6.00  0.00 ",
        )
        rep_line.parse()

        # bad speed
        rep_line = State(
            1,
            "951212 120800 SUBJECT VC 60 23 40.25 N 000 01 25.86 E 109.08  6.b0  0.00 ",
        )
        rep_line.parse()

        # bad depth
        rep_line = State(
            1,
            "951212 120800 SUBJECT VC 60 23 40.25 N 000 01 25.86 E 109.08  6.00  0.c0 ",
        )
        rep_line.parse()

    def test_line_ok(self):
        rep_line = State(
            1,
            "100112 120800 SUBJECT VC 60 23 40.25 N 000 01 25.86 E 109.08  6.00  0.00 ",
        )
        rep_line.parse()

        self.assertEqual(1, rep_line.get_line_number())

        uReg = unit_registry

        self.assertEqual(
            datetime.datetime(2010, 1, 12, 12, 8), rep_line.get_timestamp()
        )
        self.assertEqual("SUBJECT", rep_line.get_platform())
        self.assertEqual("VC", rep_line.get_symbology())
        # FixMe   self.assertEqual(Location(60.0, 23.0, 40.25, "N"), rep_line.getLatitude())
        # FixMe   self.assertEqual("SUBJECT", rep_line.getLongitude())
        self.assertAlmostEqual(1.9038051480754146, rep_line.get_heading())
        self.assertAlmostEqual(6.00, rep_line.get_speed().to(uReg.knot).magnitude)
        self.assertEqual(0.0, rep_line.get_depth())
        self.assertEqual(None, rep_line.get_text_label())


if __name__ == "__main__":
    unittest.main()
