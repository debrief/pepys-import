import unittest

from datetime import datetime

from pepys_import.core.store.data_store import DataStore
from pepys_import.core.validators.enhanced_validator import EnhancedValidator


class EnhancedValidatorTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

        with self.store.session_scope():
            # Create a platform, a sensor, a datafile and finally a state object respectively
            nationality = self.store.add_to_nationalities("test_nationality").name
            platform_type = self.store.add_to_platform_types("test_platform_type").name
            sensor_type = self.store.add_to_sensor_types("test_sensor_type")
            privacy = self.store.add_to_privacies("test_privacy").name

            platform = self.store.get_platform(
                platform_name="Test Platform",
                nationality=nationality,
                platform_type=platform_type,
                privacy=privacy,
            )
            self.sensor = platform.get_sensor(self.store, "gps", sensor_type)
            self.current_time = datetime.utcnow()
            self.file = self.store.get_datafile("test_file", "csv")

            self.store.session.expunge(self.sensor)
            self.store.session.expunge(self.file)

        self.errors = list()

    def tearDown(self) -> None:
        pass

    def test_bearing_between_two_locations(self):
        state = self.file.create_state(self.sensor, self.current_time)
        state.prev_location = "POINT(75.0 25.0)"
        state.location = "POINT(80.0 30.0)"
        state.heading = 5.0
        state.course = 5.0
        EnhancedValidator(state, self.errors, "Test Parser")
        assert len(self.errors) == 2
        assert (
            "Difference between Bearing (137.243) and Heading (286.479) is more than 90 degrees!"
            in str(self.errors[0])
        )
        assert (
            "Difference between Bearing (137.243) and Course (286.479) is more than 90 degrees!"
            in str(self.errors[1])
        )

    def test_distance_between_two_locations(self):
        state = self.file.create_state(self.sensor, self.current_time)
        state.prev_location = "POINT(75.0 25.0)"
        state.location = "POINT(80.0 30.0)"
        state.speed = 10.0
        EnhancedValidator(state, self.errors, "Test Parser")
        assert len(self.errors) == 1
        assert (
            "Calculated speed (206.379 m/s) is more than the measured speed * 10 (100.000 m/s)"
            in str(self.errors[0])
        )
