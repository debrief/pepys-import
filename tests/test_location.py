import unittest

from pepys_import.core.formats.location import Location


class LocationTestCase(unittest.TestCase):
    def test_wrong_minutes(self):
        location = Location(1.0, "WRONG_MINUTE", 1.0, "N")
        self.assertFalse(location.parse())

    def test_wrong_seconds(self):
        location = Location(1.0, 1.0, "WRONG_SECOND", "N")
        self.assertFalse(location.parse())

    def test_wrong_hemisphere(self):
        location = Location(1.0, 1.0, 1.0, "WRONG_HEMISPHERE")
        self.assertFalse(location.parse())

    @unittest.expectedFailure
    def test_compare_wrong_instances(self):
        location = Location(1.0, 1.0, 1.0, "N")
        random_instance = "TEST"
        self.assertEqual(location, random_instance)


if __name__ == "__main__":
    unittest.main()
