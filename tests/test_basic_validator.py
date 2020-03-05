import unittest

from datetime import datetime

from pepys_import.core.store.data_store import DataStore
from pepys_import.core.validators.basic_validator import BasicValidator


class BasicValidatorTestCase(unittest.TestCase):
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

    def test_validate_longitude(self):
        state = self.file.create_state(self.sensor, self.current_time)
        state.location = "POINT(180.0 25.0)"
        BasicValidator(state, self.errors, "Test Parser")
        assert len(self.errors) == 1
        assert "Longitude is not between -90 and 90 degrees!" in str(self.errors[0])

    def test_validate_latitude(self):
        state = self.file.create_state(self.sensor, self.current_time)
        state.location = "POINT(25.0 300.0)"
        BasicValidator(state, self.errors, "Test Parser")
        assert len(self.errors) == 1
        assert "Latitude is not between -180 and 180 degrees!" in str(self.errors[0])

    def test_validate_heading(self):
        state = self.file.create_state(self.sensor, self.current_time)
        state.heading = 10.0  # 10 radians is approximately 572 degrees
        BasicValidator(state, self.errors, "Test Parser")
        assert len(self.errors) == 1
        assert "Heading is not between 0 and 360 degrees!" in str(self.errors[0])

    def test_validate_course(self):
        state = self.file.create_state(self.sensor, self.current_time)
        state.course = 10.0  # 10 radians is approximately 572 degrees
        BasicValidator(state, self.errors, "Test Parser")
        assert len(self.errors) == 1
        assert "Course is not between 0 and 360 degrees!" in str(self.errors[0])


if __name__ == "__main__":
    unittest.main()
