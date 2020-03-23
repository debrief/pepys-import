import unittest
import pytest

from datetime import datetime


from pepys_import.core.store.data_store import DataStore
from pepys_import.core.validators import constants as validation_constants
from pepys_import.file.importer import Importer
from pepys_import.core.formats import unit_registry

from pepys_import.core.formats.location import Location


class TestStateSpeedProperty(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_state_speed_none(self):
        state = self.store.db_classes.State()

        state.speed = None

        assert state.speed is None

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

        assert (
            "Speed must be a Quantity with a dimensionality of [length]/[time]"
            in str(exception.value)
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


class TestStateHeadingProperty(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_state_heading_none(self):
        state = self.store.db_classes.State()

        state.heading = None

        assert state.heading is None

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

        assert "Heading must be a Quantity with a dimensionality of ''" in str(
            exception.value
        )

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

    def test_state_course_none(self):
        state = self.store.db_classes.State()

        state.course = None

        assert state.course is None

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

        assert "Course must be a Quantity with a dimensionality of ''" in str(
            exception.value
        )

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


class TestContactBearingProperty(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_contact_bearing_none(self):
        contact = self.store.db_classes.Contact()

        contact.bearing = None

        assert contact.bearing is None

    def test_contact_bearing_scalar(self):
        contact = self.store.db_classes.Contact()

        # Check setting with a scalar (float) gives error
        with pytest.raises(TypeError) as exception:
            contact.bearing = 5

        assert "Bearing must be a Quantity" in str(exception.value)

    def test_contact_bearing_wrong_units(self):
        contact = self.store.db_classes.Contact()

        # Check setting with a Quantity of the wrong units gives error
        with pytest.raises(ValueError) as exception:
            contact.bearing = 5 * unit_registry.second

        assert "Bearing must be a Quantity with a dimensionality of ''" in str(
            exception.value
        )

    def test_contact_bearing_right_units(self):
        contact = self.store.db_classes.Contact()

        # Check setting with a Quantity of the right SI units succeeds
        contact.bearing = 57 * unit_registry.degree

        # Check setting with a Quantity of strange but valid units succeeds
        contact.bearing = 0.784 * unit_registry.radian

    def test_contact_bearing_roundtrip(self):
        contact = self.store.db_classes.Contact()

        # Check setting and retrieving field works, and gives units as a result
        contact.bearing = 157 * unit_registry.degree

        assert contact.bearing == 157 * unit_registry.degree
        assert contact.bearing.check("")


class TestContactRelBearingProperty(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_contact_rel_bearing_none(self):
        contact = self.store.db_classes.Contact()

        contact.rel_bearing = None

        assert contact.rel_bearing is None

    def test_contact_rel_bearing_scalar(self):
        contact = self.store.db_classes.Contact()

        # Check setting with a scalar (float) gives error
        with pytest.raises(TypeError) as exception:
            contact.rel_bearing = 5

        assert "Relative Bearing must be a Quantity" in str(exception.value)

    def test_contact_rel_bearing_wrong_units(self):
        contact = self.store.db_classes.Contact()

        # Check setting with a Quantity of the wrong units gives error
        with pytest.raises(ValueError) as exception:
            contact.rel_bearing = 5 * unit_registry.second

        assert "Relative Bearing must be a Quantity with a dimensionality of ''" in str(
            exception.value
        )

    def test_contact_rel_bearing_right_units(self):
        contact = self.store.db_classes.Contact()

        # Check setting with a Quantity of the right SI units succeeds
        contact.rel_bearing = 57 * unit_registry.degree

        # Check setting with a Quantity of strange but valid units succeeds
        contact.rel_bearing = 0.784 * unit_registry.radian

    def test_contact_rel_bearing_roundtrip(self):
        contact = self.store.db_classes.Contact()

        # Check setting and retrieving field works, and gives units as a result
        contact.rel_bearing = 157 * unit_registry.degree

        assert contact.rel_bearing == 157 * unit_registry.degree
        assert contact.rel_bearing.check("")


class TestContactMLAProperty(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_contact_mla_none(self):
        contact = self.store.db_classes.Contact()

        contact.mla = None

        assert contact.mla is None

    def test_contact_mla_scalar(self):
        contact = self.store.db_classes.Contact()

        # Check setting with a scalar (float) gives error
        with pytest.raises(TypeError) as exception:
            contact.mla = 5

        assert "MLA must be a Quantity" in str(exception.value)

    def test_contact_mla_wrong_units(self):
        contact = self.store.db_classes.Contact()

        # Check setting with a Quantity of the wrong units gives error
        with pytest.raises(ValueError) as exception:
            contact.mla = 5 * unit_registry.second

        assert "MLA must be a Quantity with a dimensionality of ''" in str(
            exception.value
        )

    def test_contact_mla_right_units(self):
        contact = self.store.db_classes.Contact()

        # Check setting with a Quantity of the right SI units succeeds
        contact.mla = 57 * unit_registry.degree

        # Check setting with a Quantity of strange but valid units succeeds
        contact.mla = 0.784 * unit_registry.radian

    def test_contact_mla_roundtrip(self):
        contact = self.store.db_classes.Contact()

        # Check setting and retrieving field works, and gives units as a result
        contact.mla = 234 * unit_registry.degree

        assert contact.mla == 234 * unit_registry.degree
        assert contact.mla.check("")


class TestContactSLAProperty(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_contact_sla_none(self):
        contact = self.store.db_classes.Contact()

        contact.sla = None

        assert contact.sla is None

    def test_contact_sla_scalar(self):
        contact = self.store.db_classes.Contact()

        # Check setting with a scalar (float) gives error
        with pytest.raises(TypeError) as exception:
            contact.sla = 5

        assert "SLA must be a Quantity" in str(exception.value)

    def test_contact_sla_wrong_units(self):
        contact = self.store.db_classes.Contact()

        # Check setting with a Quantity of the wrong units gives error
        with pytest.raises(ValueError) as exception:
            contact.sla = 5 * unit_registry.second

        assert "SLA must be a Quantity with a dimensionality of ''" in str(
            exception.value
        )

    def test_contact_sla_right_units(self):
        contact = self.store.db_classes.Contact()

        # Check setting with a Quantity of the right SI units succeeds
        contact.sla = 57 * unit_registry.degree

        # Check setting with a Quantity of strange but valid units succeeds
        contact.sla = 0.784 * unit_registry.radian

    def test_contact_sla_roundtrip(self):
        contact = self.store.db_classes.Contact()

        # Check setting and retrieving field works, and gives units as a result
        contact.sla = 198 * unit_registry.degree

        assert contact.sla == 198 * unit_registry.degree
        assert contact.sla.check("")


class TestContactOrientationProperty(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_contact_orientation_none(self):
        contact = self.store.db_classes.Contact()

        contact.orientation = None

        assert contact.orientation is None

    def test_contact_orientation_scalar(self):
        contact = self.store.db_classes.Contact()

        # Check setting with a scalar (float) gives error
        with pytest.raises(TypeError) as exception:
            contact.orientation = 5

        assert "Orientation must be a Quantity" in str(exception.value)

    def test_contact_orientation_wrong_units(self):
        contact = self.store.db_classes.Contact()

        # Check setting with a Quantity of the wrong units gives error
        with pytest.raises(ValueError) as exception:
            contact.orientation = 5 * unit_registry.second

        assert "Orientation must be a Quantity with a dimensionality of ''" in str(
            exception.value
        )

    def test_contact_orientation_right_units(self):
        contact = self.store.db_classes.Contact()

        # Check setting with a Quantity of the right SI units succeeds
        contact.orientation = 57 * unit_registry.degree

        # Check setting with a Quantity of strange but valid units succeeds
        contact.orientation = 0.784 * unit_registry.radian

    def test_contact_orientation_roundtrip(self):
        contact = self.store.db_classes.Contact()

        # Check setting and retrieving field works, and gives units as a result
        contact.orientation = 53 * unit_registry.degree

        assert contact.orientation == 53 * unit_registry.degree
        assert contact.orientation.check("")


class TestContactMajorProperty(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_contact_major_none(self):
        contact = self.store.db_classes.Contact()

        contact.major = None

        assert contact.major is None

    def test_contact_major_scalar(self):
        contact = self.store.db_classes.Contact()

        # Check setting with a scalar (float) gives error
        with pytest.raises(TypeError) as exception:
            contact.major = 5

        assert "Major must be a Quantity" in str(exception.value)

    def test_contact_major_wrong_units(self):
        contact = self.store.db_classes.Contact()

        # Check setting with a Quantity of the wrong units gives error
        with pytest.raises(ValueError) as exception:
            contact.major = 5 * unit_registry.second

        assert "Major must be a Quantity with a dimensionality of [length]" in str(
            exception.value
        )

    def test_contact_major_right_units(self):
        contact = self.store.db_classes.Contact()

        # Check setting with a Quantity of the right SI units succeeds
        contact.major = 57 * unit_registry.kilometre

        # Check setting with a Quantity of strange but valid units succeeds
        contact.major = 1523 * unit_registry.angstrom

    def test_contact_major_roundtrip(self):
        contact = self.store.db_classes.Contact()

        # Check setting and retrieving field works, and gives units as a result
        contact.major = 1234 * unit_registry.metre

        assert contact.major == 1234 * unit_registry.metre
        assert contact.major.check("[length]")


class TestContactMinorProperty(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_contact_minor_none(self):
        contact = self.store.db_classes.Contact()

        contact.minor = None

        assert contact.minor is None

    def test_contact_minor_scalar(self):
        contact = self.store.db_classes.Contact()

        # Check setting with a scalar (float) gives error
        with pytest.raises(TypeError) as exception:
            contact.minor = 5

        assert "Minor must be a Quantity" in str(exception.value)

    def test_contact_minor_wrong_units(self):
        contact = self.store.db_classes.Contact()

        # Check setting with a Quantity of the wrong units gives error
        with pytest.raises(ValueError) as exception:
            contact.minor = 5 * unit_registry.second

        assert "Minor must be a Quantity with a dimensionality of [length]" in str(
            exception.value
        )

    def test_contact_minor_right_units(self):
        contact = self.store.db_classes.Contact()

        # Check setting with a Quantity of the right SI units succeeds
        contact.minor = 32 * unit_registry.kilometre

        # Check setting with a Quantity of strange but valid units succeeds
        contact.minor = 1943 * unit_registry.angstrom

    def test_contact_minor_roundtrip(self):
        contact = self.store.db_classes.Contact()

        # Check setting and retrieving field works, and gives units as a result
        contact.minor = 1023 * unit_registry.metre

        assert contact.minor == 1023 * unit_registry.metre
        assert contact.minor.check("[length]")


class TestContactRangeProperty(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_contact_range_none(self):
        contact = self.store.db_classes.Contact()

        contact.range = None

        assert contact.range is None

    def test_contact_range_scalar(self):
        contact = self.store.db_classes.Contact()

        # Check setting with a scalar (float) gives error
        with pytest.raises(TypeError) as exception:
            contact.range = 5

        assert "Range must be a Quantity" in str(exception.value)

    def test_contact_range_wrong_units(self):
        contact = self.store.db_classes.Contact()

        # Check setting with a Quantity of the wrong units gives error
        with pytest.raises(ValueError) as exception:
            contact.range = 5 * unit_registry.second

        assert "Range must be a Quantity with a dimensionality of [length]" in str(
            exception.value
        )

    def test_contact_range_right_units(self):
        contact = self.store.db_classes.Contact()

        # Check setting with a Quantity of the right SI units succeeds
        contact.range = 19 * unit_registry.yard

        # Check setting with a Quantity of strange but valid units succeeds
        contact.range = 2341 * unit_registry.angstrom

    def test_contact_range_roundtrip(self):
        contact = self.store.db_classes.Contact()

        # Check setting and retrieving field works, and gives units as a result
        contact.range = 976 * unit_registry.metre

        assert contact.range == 976 * unit_registry.metre
        assert contact.range.check("[length]")


class TestContactFreqProperty(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_contact_freq_none(self):
        contact = self.store.db_classes.Contact()

        contact.freq = None

        assert contact.freq is None

    def test_contact_freq_scalar(self):
        contact = self.store.db_classes.Contact()

        # Check setting with a scalar (float) gives error
        with pytest.raises(TypeError) as exception:
            contact.freq = 5

        assert "Freq must be a Quantity" in str(exception.value)

    def test_contact_freq_wrong_units(self):
        contact = self.store.db_classes.Contact()

        # Check setting with a Quantity of the wrong units gives error
        with pytest.raises(ValueError) as exception:
            contact.freq = 5 * unit_registry.kilogram

        assert "Freq must be a Quantity with a dimensionality of [time]^-1" in str(
            exception.value
        )

    def test_contact_freq_right_units(self):
        contact = self.store.db_classes.Contact()

        # Check setting with a Quantity of the right SI units succeeds
        contact.freq = 32 * unit_registry.hertz

    def test_contact_freq_roundtrip(self):
        contact = self.store.db_classes.Contact()

        # Check setting and retrieving field works, and gives units as a result
        contact.freq = 567 * unit_registry.hertz

        assert contact.freq == 567 * unit_registry.hertz
        assert contact.freq.check("[time]^-1")


CLASSES_WITH_ELEVATION = [
    pytest.param("State", id="state"),
    pytest.param("Media", id="media"),
    pytest.param("Contact", id="contact"),
]


class TestElevationProperty:
    def setup_class(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    @pytest.mark.parametrize(
        "class_name", CLASSES_WITH_ELEVATION,
    )
    def test_elevation_none(self, class_name):
        obj = eval(f"self.store.db_classes.{class_name}()")

        obj.elevation = None

        assert obj.elevation is None

    @pytest.mark.parametrize(
        "class_name", CLASSES_WITH_ELEVATION,
    )
    def test_elevation_scalar(self, class_name):
        obj = eval(f"self.store.db_classes.{class_name}()")

        # Check setting with a scalar (float) gives error
        with pytest.raises(TypeError) as exception:
            obj.elevation = 5

        assert "Elevation must be a Quantity" in str(exception.value)

    @pytest.mark.parametrize(
        "class_name", CLASSES_WITH_ELEVATION,
    )
    def test_elevation_wrong_units(self, class_name):
        obj = eval(f"self.store.db_classes.{class_name}()")

        # Check setting with a Quantity of the wrong units gives error
        with pytest.raises(ValueError) as exception:
            obj.elevation = 5 * unit_registry.second

        assert "Elevation must be a Quantity with a dimensionality of [length]" in str(
            exception.value
        )

    @pytest.mark.parametrize(
        "class_name", CLASSES_WITH_ELEVATION,
    )
    def test_elevation_right_units(self, class_name):
        obj = eval(f"self.store.db_classes.{class_name}()")

        # Check setting with a Quantity of the right SI units succeeds
        obj.elevation = 5 * unit_registry.metre

        # Check setting with a Quantity of strange but valid units succeeds
        obj.elevation = 5 * unit_registry.angstrom

    @pytest.mark.parametrize(
        "class_name", CLASSES_WITH_ELEVATION,
    )
    def test_state_elevation_roundtrip(self, class_name):
        obj = eval(f"self.store.db_classes.{class_name}()")

        # Check setting and retrieving field works, and gives units as a result
        obj.elevation = 10 * unit_registry.metre

        assert obj.elevation == 10 * unit_registry.metre
        assert obj.elevation.check("[length]")


CLASSES_WITH_LOCATION = [
    pytest.param("State", id="state"),
    pytest.param("Media", id="media"),
    pytest.param("Contact", id="contact"),
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
    def test_location_property_none(self, class_name):
        obj = eval(f"self.store.db_classes.{class_name}()")

        obj.location = None

        assert obj.location is None

    @pytest.mark.parametrize(
        "class_name", CLASSES_WITH_LOCATION,
    )
    def test_location_property_invalid_type(self, class_name):
        obj = eval(f"self.store.db_classes.{class_name}()")
        with pytest.raises(TypeError) as exception:
            obj.location = (50, -1)

        assert "location value must be an instance of the Location class" in str(
            exception.value
        )

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
        with self.store.session_scope() as session:
            self.change_id = self.store.add_to_changes(
                "TEST", datetime.utcnow(), "TEST"
            ).change_id
            print(self.change_id)
            self.nationality = self.store.add_to_nationalities(
                "test_nationality", self.change_id
            ).name
            self.platform_type = self.store.add_to_platform_types(
                "test_platform_type", self.change_id
            ).name
            self.sensor_type = self.store.add_to_sensor_types(
                "test_sensor_type", self.change_id
            )
            self.privacy = self.store.add_to_privacies(
                "test_privacy", self.change_id
            ).name

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
        with self.store.session_scope() as session:
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
        with self.store.session_scope() as session:
            states = self.store.session.query(self.store.db_classes.State).all()
            self.assertEqual(len(states), 1)
            loc = states[0].location

            assert loc.latitude == 50.23
            assert loc.longitude == -1.35
