import unittest
from datetime import datetime

import pytest

from pepys_import.core.formats import unit_registry
from pepys_import.core.formats.location import Location
from pepys_import.core.store.data_store import DataStore
from pepys_import.core.validators import constants as validation_constants
from pepys_import.file.importer import Importer


class TestStateSpeedProperty(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_state_speed_scalar(self):
        state = self.store.db_classes.State()

        # Check setting with a scalar (float) gives error
        with pytest.raises(TypeError) as exception:
            state.speed = 5

        assert "Speed must be a Quantity" in str(exception.value)

    def test_state_speed_wrong_units(self):
        state = self.store.db_classes.State()

        # Check setting with a Quantity of the wrong units gives error
        with pytest.raises(ValueError) as exception:
            state.speed = 5 * unit_registry.metre

        assert "Speed must be a Quantity with a dimensionality of [length]/[time]" in str(
            exception.value
        )

    def test_state_speed_right_units(self):
        state = self.store.db_classes.State()

        # Check setting with a Quantity of the right SI units succeeds
        state.speed = 5 * (unit_registry.metre / unit_registry.second)

        # Check setting with a Quantity of strange but valid units succeeds
        state.speed = 5 * (unit_registry.angstrom / unit_registry.day)

    def test_state_speed_roundtrip(self):
        state = self.store.db_classes.State()

        # Check setting and retrieving field works, and gives units as a result
        state.speed = 10 * (unit_registry.metre / unit_registry.second)

        assert state.speed == 10 * (unit_registry.metre / unit_registry.second)
        assert state.speed.check("[length]/[time]")


class TestStateElevationProperty(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_state_elevation_scalar(self):
        state = self.store.db_classes.State()

        # Check setting with a scalar (float) gives error
        with pytest.raises(TypeError) as exception:
            state.elevation = 5

        assert "Elevation must be a Quantity" in str(exception.value)

    def test_state_elevation_wrong_units(self):
        state = self.store.db_classes.State()

        # Check setting with a Quantity of the wrong units gives error
        with pytest.raises(ValueError) as exception:
            state.elevation = 5 * unit_registry.second

        assert "Elevation must be a Quantity with a dimensionality of [length]" in str(
            exception.value
        )

    def test_state_elevation_right_units(self):
        state = self.store.db_classes.State()

        # Check setting with a Quantity of the right SI units succeeds
        state.elevation = 5 * unit_registry.metre

        # Check setting with a Quantity of strange but valid units succeeds
        state.elevation = 5 * unit_registry.angstrom

    def test_state_elevation_roundtrip(self):
        state = self.store.db_classes.State()

        # Check setting and retrieving field works, and gives units as a result
        state.elevation = 10 * unit_registry.metre

        assert state.elevation == 10 * unit_registry.metre
        assert state.elevation.check("[length]")


class TestStateHeadingProperty(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_state_heading_scalar(self):
        state = self.store.db_classes.State()

        # Check setting with a scalar (float) gives error
        with pytest.raises(TypeError) as exception:
            state.heading = 5

        assert "Heading must be a Quantity" in str(exception.value)

    def test_state_heading_wrong_units(self):
        state = self.store.db_classes.State()

        # Check setting with a Quantity of the wrong units gives error
        with pytest.raises(ValueError) as exception:
            state.heading = 5 * unit_registry.second

        assert "Heading must be a Quantity with a dimensionality of ''" in str(exception.value)

    def test_state_heading_right_units(self):
        state = self.store.db_classes.State()

        # Check setting with a Quantity of the right SI units succeeds
        state.heading = 57 * unit_registry.degree

        # Check setting with a Quantity of strange but valid units succeeds
        state.heading = 0.784 * unit_registry.radian

    def test_state_heading_roundtrip(self):
        state = self.store.db_classes.State()

        # Check setting and retrieving field works, and gives units as a result
        state.heading = 157 * unit_registry.degree

        assert state.heading == 157 * unit_registry.degree
        assert state.heading.check("")


class TestStateCourseProperty(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_state_course_scalar(self):
        state = self.store.db_classes.State()

        # Check setting with a scalar (float) gives error
        with pytest.raises(TypeError) as exception:
            state.course = 5

        assert "Course must be a Quantity" in str(exception.value)

    def test_state_course_wrong_units(self):
        state = self.store.db_classes.State()

        # Check setting with a Quantity of the wrong units gives error
        with pytest.raises(ValueError) as exception:
            state.course = 5 * unit_registry.second

        assert "Course must be a Quantity with a dimensionality of ''" in str(exception.value)

    def test_state_course_right_units(self):
        state = self.store.db_classes.State()

        # Check setting with a Quantity of the right SI units succeeds
        state.course = 57 * unit_registry.degree

        # Check setting with a Quantity of strange but valid units succeeds
        state.course = 0.784 * unit_registry.radian

    def test_state_course_roundtrip(self):
        state = self.store.db_classes.State()

        # Check setting and retrieving field works, and gives units as a result
        state.course = 157 * unit_registry.degree

        assert state.course == 157 * unit_registry.degree
        assert state.course.check("")


class TestMediaElevationProperty(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_media_elevation_scalar(self):
        media = self.store.db_classes.Media()

        # Check setting with a scalar (float) gives error
        with pytest.raises(TypeError) as exception:
            media.elevation = 5

        assert "Elevation must be a Quantity" in str(exception.value)

    def test_media_elevation_wrong_units(self):
        media = self.store.db_classes.Media()

        # Check setting with a Quantity of the wrong units gives error
        with pytest.raises(ValueError) as exception:
            media.elevation = 5 * unit_registry.second

        assert "Elevation must be a Quantity with a dimensionality of [length]" in str(
            exception.value
        )

    def test_media_elevation_right_units(self):
        media = self.store.db_classes.Media()

        # Check setting with a Quantity of the right SI units succeeds
        media.elevation = 5 * unit_registry.metre

        # Check setting with a Quantity of strange but valid units succeeds
        media.elevation = 5 * unit_registry.angstrom

    def test_media_elevation_roundtrip(self):
        media = self.store.db_classes.Media()

        # Check setting and retrieving field works, and gives units as a result
        media.elevation = 10 * unit_registry.metre

        assert media.elevation == 10 * unit_registry.metre
        assert media.elevation.check("[length]")


CLASSES_WITH_LOCATION = [
    pytest.param("State", id="state"),
    pytest.param("Media", id="media"),
]


class TestLocationProperty:
    def setup_class(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    @pytest.mark.parametrize(
        "class_name", CLASSES_WITH_LOCATION,
    )
    def test_location_property_invalid_type(self, class_name):
        obj = eval(f"self.store.db_classes.{class_name}()")
        print(type(obj))
        with pytest.raises(TypeError) as exception:
            obj.location = (50, -1)

        assert "location value must be an instance of the Location class" in str(exception.value)

    @pytest.mark.parametrize(
        "class_name", CLASSES_WITH_LOCATION,
    )
    def test_location_invalid_location(self, class_name):
        obj = eval(f"self.store.db_classes.{class_name}()")

        # Check setting with a Quantity of the wrong units gives error
        with pytest.raises(ValueError) as exception:
            obj.location = Location()

        assert "location object does not have valid values" in str(exception.value)

    @pytest.mark.parametrize(
        "class_name", CLASSES_WITH_LOCATION,
    )
    def test_location_valid_location(self, class_name):
        obj = eval(f"self.store.db_classes.{class_name}()")

        loc = Location()
        loc.set_latitude_decimal_degrees(50.23)
        loc.set_longitude_decimal_degrees(-1.34)

        obj.location = loc

    @pytest.mark.parametrize(
        "class_name", CLASSES_WITH_LOCATION,
    )
    def test_location_roundtrip_not_to_db(self, class_name):
        # Tests a roundtrip of a Location object, but without
        # actually committing to the DB - so the Location object
        # is converted to and from a string, but not actually stored
        # in the database as a WKBElement.

        obj = eval(f"self.store.db_classes.{class_name}()")

        loc = Location()
        loc.set_latitude_decimal_degrees(50.23)
        loc.set_longitude_decimal_degrees(-1.34)

        obj.location = loc

        assert obj.location.latitude == 50.23
        assert obj.location.longitude == -1.34


class TestLocationRoundtripToDB(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()
        with self.store.session_scope():
            self.change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id
            print(self.change_id)
            self.nationality = self.store.add_to_nationalities(
                "test_nationality", self.change_id
            ).name
            self.platform_type = self.store.add_to_platform_types(
                "test_platform_type", self.change_id
            ).name
            self.sensor_type = self.store.add_to_sensor_types("test_sensor_type", self.change_id)
            self.privacy = self.store.add_to_privacies("test_privacy", self.change_id).name

            self.platform = self.store.get_platform(
                platform_name="Test Platform",
                nationality=self.nationality,
                platform_type=self.platform_type,
                privacy=self.privacy,
                change_id=self.change_id,
            )

            self.sensor = self.platform.get_sensor(
                self.store, "gps", self.sensor_type, change_id=self.change_id
            )
            self.file = self.store.get_datafile(
                "test_file", "csv", 0, "HASHED-1", change_id=self.change_id
            )
            self.current_time = datetime.utcnow()

            self.store.session.expunge(self.sensor)
            self.store.session.expunge(self.platform)
            self.store.session.expunge(self.file)
            self.store.session.expunge(self.sensor_type)

        class TestParser(Importer):
            def __init__(
                self,
                name="Test Importer",
                validation_level=validation_constants.NONE_LEVEL,
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
        self.file.measurements[self.parser.short_name] = list()

    def tearDown(self):
        pass

    def test_location_roundtrip_to_db(self):
        with self.store.session_scope():
            states = self.store.session.query(self.store.db_classes.State).all()

            # there must be no entry at the beginning
            self.assertEqual(len(states), 0)

            state = self.file.create_state(
                self.store,
                self.platform,
                self.sensor,
                self.current_time,
                parser_name=self.parser.short_name,
            )

            loc = Location()
            loc.set_latitude_decimal_degrees(50.23)
            loc.set_longitude_decimal_degrees(-1.35)
            state.location = loc

            # there must be no entry because it's kept in-memory
            states = self.store.session.query(self.store.db_classes.State).all()
            self.assertEqual(len(states), 0)

            self.assertEqual(state.time, self.current_time)

            # Commit to the DB
            if self.file.validate():
                self.file.commit(self.store, change_id=self.change_id)

        # In a separate session, check that we get a Location class with the right
        # lat and lon
        with self.store.session_scope():
            states = self.store.session.query(self.store.db_classes.State).all()
            self.assertEqual(len(states), 1)
            loc = states[0].location

            assert loc.latitude == 50.23
            assert loc.longitude == -1.35
