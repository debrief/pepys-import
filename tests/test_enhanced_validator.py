import unittest
from datetime import datetime, timedelta

from pepys_import.core.formats import unit_registry
from pepys_import.core.formats.location import Location
from pepys_import.core.store.data_store import DataStore
from pepys_import.core.validators import constants
from pepys_import.core.validators.enhanced_validator import EnhancedValidator
from pepys_import.file.importer import Importer
from pepys_import.utils.unit_utils import acceptable_bearing_error


class EnhancedValidatorTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()
        with self.store.session_scope():
            self.change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id
            # Create a platform, a sensor, a datafile and finally a state object respectively
            nationality = self.store.add_to_nationalities("test_nationality", self.change_id).name
            platform_type = self.store.add_to_platform_types(
                "test_platform_type", self.change_id
            ).name
            sensor_type = self.store.add_to_sensor_types("test_sensor_type", self.change_id).name
            privacy = self.store.add_to_privacies("test_privacy", self.change_id).name

            self.platform = self.store.get_platform(
                platform_name="Test Platform",
                nationality=nationality,
                platform_type=platform_type,
                privacy=privacy,
                change_id=self.change_id,
            )
            self.sensor = self.platform.get_sensor(
                self.store, "gps", sensor_type, change_id=self.change_id
            )
            self.current_time = datetime.utcnow()
            self.file = self.store.get_datafile("test_file", "csv", 0, "hashed", self.change_id)

            self.store.session.expunge(self.platform)
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

            def _load_this_file(self, data_store, path, file_contents, datafile, change_id):
                pass

        self.parser = TestParser()
        self.file.measurements[self.parser.short_name] = dict()

    def tearDown(self) -> None:
        pass

    def test_bearing_error_calc(self):
        assert acceptable_bearing_error(0, 30, 90)
        assert acceptable_bearing_error(330, 30, 90)
        assert acceptable_bearing_error(330, 0, 90)
        assert acceptable_bearing_error(30, 330, 90)

        assert acceptable_bearing_error(330, 100, 90) is False
        assert acceptable_bearing_error(270, 10, 90) is False
        assert acceptable_bearing_error(10, 260, 90) is False

    def test_bearing_between_two_locations(self):
        prev_state = self.file.create_state(
            self.store,
            self.platform,
            self.sensor,
            self.current_time,
            parser_name=self.parser.short_name,
        )
        prev_loc = Location()
        prev_loc.set_latitude_decimal_degrees(25)
        prev_loc.set_longitude_decimal_degrees(75)
        prev_state.location = prev_loc

        current_state = self.file.create_state(
            self.store,
            self.platform,
            self.sensor,
            self.current_time + timedelta(minutes=1),
            parser_name=self.parser.short_name,
        )
        loc = Location()
        loc.set_latitude_decimal_degrees(30)
        loc.set_longitude_decimal_degrees(80)
        current_state.location = loc

        current_state.heading = 5.0 * unit_registry.radian
        current_state.course = 5.0 * unit_registry.radian
        EnhancedValidator(current_state, self.errors, "Test Parser", prev_state)
        assert len(self.errors) == 2
        assert (
            "Difference between Bearing (40.444) and Heading (286.479 degree) is more than 90 degrees!"
            in str(self.errors[0])
        )
        assert (
            "Difference between Bearing (40.444) and Course (286.479 degree) is more than 90 degrees!"
            in str(self.errors[1])
        )

    def test_distance_between_two_locations(self):
        prev_state = self.file.create_state(
            self.store,
            self.platform,
            self.sensor,
            self.current_time,
            parser_name=self.parser.short_name,
        )
        prev_loc = Location()
        prev_loc.set_latitude_decimal_degrees(25)
        prev_loc.set_longitude_decimal_degrees(75)
        prev_state.location = prev_loc

        current_state = self.file.create_state(
            self.store,
            self.platform,
            self.sensor,
            self.current_time + timedelta(minutes=1),
            parser_name=self.parser.short_name,
        )
        loc = Location()
        loc.set_latitude_decimal_degrees(30)
        loc.set_longitude_decimal_degrees(80)
        current_state.location = loc

        current_state.speed = 10.0 * (unit_registry.metre / unit_registry.second)
        EnhancedValidator(current_state, self.errors, "Test Parser", prev_state)
        assert len(self.errors) == 1
        assert (
            "Calculated speed (12382.753 meter / second) is more than the measured speed * 10 "
            "(100.000 meter / second)" in str(self.errors[0])
        )


if __name__ == "__main__":
    unittest.main()
