import unittest
from datetime import datetime

from pepys_import.core.formats import unit_registry
from pepys_import.core.formats.location import Location
from pepys_import.core.store.data_store import DataStore
from pepys_import.core.validators import constants
from pepys_import.core.validators.basic_validator import BasicValidator
from pepys_import.file.importer import Importer


class BasicValidatorTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

        with self.store.session_scope():
            # Create a platform, a sensor, a datafile and finally a state object respectively
            self.current_time = datetime.utcnow()
            change_id = self.store.add_to_changes("TEST", self.current_time, "TEST").change_id
            nationality = self.store.add_to_nationalities("test_nationality", change_id).name
            platform_type = self.store.add_to_platform_types("test_platform_type", change_id).name
            sensor_type = self.store.add_to_sensor_types("test_sensor_type", change_id).name
            privacy = self.store.add_to_privacies("test_privacy", change_id).name

            self.platform = self.store.get_platform(
                platform_name="Test Platform",
                nationality=nationality,
                platform_type=platform_type,
                privacy=privacy,
                change_id=change_id,
            )
            self.sensor = self.platform.get_sensor(
                self.store, "gps", sensor_type, change_id=change_id
            )
            self.file = self.store.get_datafile("test_file", "csv", 0, "HASHED", change_id)

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

            def _load_this_file(self, data_store, path, file_contents, datafile):
                pass

        self.parser = TestParser()
        self.file.measurements[self.parser.short_name] = dict()

    def tearDown(self) -> None:
        pass

    def test_validate_latitude(self):
        state = self.file.create_state(
            self.store,
            self.platform,
            self.sensor,
            self.current_time,
            parser_name=self.parser.short_name,
        )
        # Normally the Location class stops us setting
        # values that are out of range
        # so we hack it here, by setting the hidden attributes
        # directly
        loc = Location()
        loc._latitude = 180
        loc._longitude = 25
        state.location = loc
        bv = BasicValidator("Test Parser")
        bv.validate(state, self.errors)
        assert len(self.errors) == 1
        assert "Latitude is not between -90 and 90 degrees!" in str(self.errors[0])

    def test_validate_longitude(self):
        state = self.file.create_state(
            self.store,
            self.platform,
            self.sensor,
            self.current_time,
            parser_name=self.parser.short_name,
        )
        # Normally the Location class stops us setting
        # values that are out of range
        # so we hack it here, by setting the hidden attributes
        # directly
        loc = Location()
        loc._latitude = 25
        loc._longitude = 250
        state.location = loc
        bv = BasicValidator("Test Parser")
        bv.validate(state, self.errors)
        assert len(self.errors) == 1
        assert "Longitude is not between -180 and 180 degrees!" in str(self.errors[0])

    def test_validate_heading(self):
        state = self.file.create_state(
            self.store,
            self.platform,
            self.sensor,
            self.current_time,
            parser_name=self.parser.short_name,
        )
        state.heading = 10.0 * unit_registry.radian  # 10 radians is approximately 572 degrees
        bv = BasicValidator("Test Parser")
        bv.validate(state, self.errors)
        assert len(self.errors) == 1
        assert "Heading is not between 0 and 360 degrees!" in str(self.errors[0])

    def test_validate_course(self):
        state = self.file.create_state(
            self.store,
            self.platform,
            self.sensor,
            self.current_time,
            parser_name=self.parser.short_name,
        )
        state.course = 10.0 * unit_registry.radian  # 10 radians is approximately 572 degrees
        bv = BasicValidator("Test Parser")
        bv.validate(state, self.errors)
        assert len(self.errors) == 1
        assert "Course is not between 0 and 360 degrees!" in str(self.errors[0])


if __name__ == "__main__":
    unittest.main()
