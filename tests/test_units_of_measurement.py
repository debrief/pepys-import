import unittest

from pepys_import.core.formats.state import State
from pepys_import.core.formats import unit_registry, quantity


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
        self.assertEqual(
            "<Quantity(3.141592653589793, 'radian')>", repr(heading_radians)
        )

        back_to_degree = heading_radians.to(self.unit_reg.degrees)
        self.assertEqual("<Quantity(180.0, 'degree')>", repr(back_to_degree))

    def test_roundTripSpeed(self):
        speed_kilometers = quantity(20, self.unit_reg.knot)
        self.assertEqual("<Quantity(20, 'knot')>", repr(speed_kilometers))

        speed_meters = speed_kilometers.to(self.unit_reg.meter / self.unit_reg.second)
        self.assertEqual(
            "<Quantity(10.28888888888889, 'meter / second')>", repr(speed_meters)
        )

        back_to_kilometes = speed_meters.to(self.unit_reg.knot)
        self.assertEqual(
            "<Quantity(20.000000000000004, 'knot')>", repr(back_to_kilometes)
        )
        self.assertAlmostEqual(20, back_to_kilometes.magnitude)

    def test_stateConversion(self):
        state = State(
            1,
            "100112 120800 SUBJECT VC 60 23 40.25 N 000 01 25.86 E 109.08  6.00  0.00 ",
        )
        state.parse()

        # Speed and Heading from state
        # heading -> 109.08 (degrees)
        # speed   -> 6.00 (knots)

        self.assertEqual("<Quantity(109.08, 'degree')>", repr(state.get_heading()))
        self.assertEqual("<Quantity(6.0, 'knot')>", repr(state.get_speed()))


if __name__ == "__main__":
    unittest.main()
