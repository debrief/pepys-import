import unittest

from datetime import datetime

from pepys_import.core.store.data_store import DataStore
from pepys_import.core.validators.enhanced_validator import EnhancedValidator
from pepys_import.core.validators import constants
from pepys_import.file.importer import Importer


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

        class TestParser(Importer):
            def __init__(
                self,
                name="Test Importer",
                validation_level=constants.NONE_LEVEL,
                short_name="Test Importer",
                separator=" ",
            ):
                super().__init__(name, validation_level, short_name)
                self.separator = separator
                self.text_label = None
                self.depth = 0.0
                self.errors = list()

            def can_load_this_header(self, header) -> bool:
                return True

            def can_load_this_filename(self, filename):
                return True

            def can_load_this_type(self, suffix):
                return True

            def can_load_this_file(self, file_contents):
                return True

            def load_this_file(self, data_store, path, file_contents, datafile):
                pass

        self.parser = TestParser()
        self.file.measurements[self.parser.short_name] = list()

    def tearDown(self) -> None:
        pass

    def test_bearing_between_two_locations(self):
        state = self.file.create_state(
            self.sensor, self.current_time, parser_name=self.parser.short_name
        )
        state.prev_location = "POINT(75.0 25.0)"
        state.location = "POINT(80.0 30.0)"
        state.heading = 5.0
        state.course = 5.0
        EnhancedValidator(state, self.errors, "Test Parser")
        assert len(self.errors) == 2
        assert (
            "Difference between Bearing (40.444) and Heading (286.479) is more than 90 degrees!"
            in str(self.errors[0])
        )
        assert (
            "Difference between Bearing (40.444) and Course (286.479) is more than 90 degrees!"
            in str(self.errors[1])
        )

    def test_distance_between_two_locations(self):
        state = self.file.create_state(
            self.sensor, self.current_time, parser_name=self.parser.short_name
        )
        state.prev_location = "POINT(75.0 25.0)"
        state.location = "POINT(80.0 30.0)"
        state.speed = 10.0
        EnhancedValidator(state, self.errors, "Test Parser")
        assert len(self.errors) == 1
        assert (
            "Calculated speed (206.379 m/s) is more than the measured speed * 10 (100.000 m/s)"
            in str(self.errors[0])
        )
