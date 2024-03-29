import unittest

from pepys_import.core.formats import quantity, unit_registry
from pepys_import.core.formats.rep_line import REPLine
from pepys_import.file.highlighter.support.test_utils import create_test_line_object


class UnitsTests(unittest.TestCase):
    def setUp(self):
        self.unit_reg = unit_registry

    def learn_about_params(self, msg, length: quantity):
        # check the parameter is of the correct type
        assert length.check("[length]")

    def test_understanding_of_params(self):
        val_metres = quantity(33, self.unit_reg.metre)
        assert val_metres.check("[length]")
        self.learn_about_params("quantity", val_metres)

        val_yards = quantity(33, self.unit_reg.yard)
        assert val_yards.check("[length]")
        self.learn_about_params("quantity", val_yards)

    @unittest.expectedFailure
    def test_sending_wrong_dimension(self):
        bad_units = quantity(54, self.unit_reg.radian)

        # this should fail, since it's expecting a length
        self.learn_about_params("quantity", bad_units)

    @unittest.expectedFailure
    def test_try_to_send_non_quantity_to_quantity_method(self):
        self.learn_about_params("float", 46.0)

    def test_round_trip_degs(self):
        heading_degrees = quantity(180.0, self.unit_reg.degrees)
        self.assertEqual("<Quantity(180.0, 'degree')>", repr(heading_degrees))

        heading_radians = heading_degrees.to(self.unit_reg.radians)
        self.assertEqual("<Quantity(3.14, 'radian')>", repr(round(heading_radians, 2)))

        back_to_degree = heading_radians.to(self.unit_reg.degrees)
        self.assertEqual("<Quantity(180.0, 'degree')>", repr(back_to_degree))

    def test_round_trip_speed(self):
        speed_kilometers = quantity(20, self.unit_reg.knot)
        self.assertEqual("<Quantity(20, 'knot')>", repr(speed_kilometers))

        speed_meters = speed_kilometers.to(self.unit_reg.meter / self.unit_reg.second)
        self.assertEqual("<Quantity(10.29, 'meter / second')>", repr(round(speed_meters, 2)))

        back_to_kilometes = speed_meters.to(self.unit_reg.knot)
        self.assertEqual("<Quantity(20.0, 'knot')>", repr(round(back_to_kilometes, 2)))
        self.assertAlmostEqual(20, back_to_kilometes.magnitude)

    def test_state_conversion(self):
        state = REPLine(
            1,
            create_test_line_object(
                "100112 120800 SUBJECT VC 60 23 40.25 N 000 01 25.86 E 109.08  6.00  0.00 "
            ),
        )
        self.assertTrue(state.parse(list(), "test"))

        # Speed and Heading from state
        # heading -> 109.08 (degrees)
        # speed   -> 6 knots (still stored as knots in REPLine, but has units)

        self.assertEqual("<Quantity(109.08, 'degree')>", repr(state.heading))
        self.assertAlmostEqual(6, state.speed.magnitude)
        assert state.speed.check("[length]/[time]")


if __name__ == "__main__":
    unittest.main()
