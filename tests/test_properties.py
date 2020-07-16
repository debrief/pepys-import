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

    def test_state_speed_class_attribute(self):
        # Check this is a valid SQLAlchemy column when used as a class attribute
        assert hasattr(self.store.db_classes.State.speed, "expression")


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

        assert "Heading must be a Quantity with a dimensionality of ''" in str(exception.value)

    def test_state_heading_wrong_units_dimensionless(self):
        state = self.store.db_classes.State()

        # Check setting with a Quantity of the wrong units gives error
        with pytest.raises(ValueError) as exception:
            state.heading = unit_registry.Quantity(5)

        assert "Heading must be a Quantity with angular units (degree or radian)" in str(
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

    def test_state_heading_class_attribute(self):
        # Check this is a valid SQLAlchemy column when used as a class attribute
        assert hasattr(self.store.db_classes.State.heading, "expression")


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

        assert "Course must be a Quantity with a dimensionality of ''" in str(exception.value)

    def test_state_course_wrong_units_dimensionless(self):
        state = self.store.db_classes.State()

        # Check setting with a Quantity of the wrong units gives error
        with pytest.raises(ValueError) as exception:
            state.course = unit_registry.Quantity(5)

        assert "Course must be a Quantity with angular units (degree or radian)" in str(
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

    def test_state_course_class_attribute(self):
        # Check this is a valid SQLAlchemy column when used as a class attribute
        assert hasattr(self.store.db_classes.State.course, "expression")


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

        assert "Bearing must be a Quantity with a dimensionality of ''" in str(exception.value)

    def test_contact_bearing_wrong_units_dimensionless(self):
        contact = self.store.db_classes.Contact()

        # Check setting with a Quantity of the wrong units gives error
        with pytest.raises(ValueError) as exception:
            contact.bearing = unit_registry.Quantity(5)

        assert "Bearing must be a Quantity with angular units (degree or radian)" in str(
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

    def test_contact_bearing_class_attribute(self):
        # Check this is a valid SQLAlchemy column when used as a class attribute
        assert hasattr(self.store.db_classes.Contact.bearing, "expression")


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

    def test_contact_bearing_wrong_units_dimensionless(self):
        contact = self.store.db_classes.Contact()

        # Check setting with a Quantity of the wrong units gives error
        with pytest.raises(ValueError) as exception:
            contact.rel_bearing = unit_registry.Quantity(5)

        assert "Relative Bearing must be a Quantity with angular units (degree or radian)" in str(
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

    def test_contact_rel_bearing_class_attribute(self):
        # Check this is a valid SQLAlchemy column when used as a class attribute
        assert hasattr(self.store.db_classes.Contact.rel_bearing, "expression")


class TestContactAmbigBearingProperty(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_contact_ambig_bearing_none(self):
        contact = self.store.db_classes.Contact()

        contact.ambig_bearing = None

        assert contact.ambig_bearing is None

    def test_contact_ambig_bearing_scalar(self):
        contact = self.store.db_classes.Contact()

        # Check setting with a scalar (float) gives error
        with pytest.raises(TypeError) as exception:
            contact.ambig_bearing = 5

        assert "Ambig Bearing must be a Quantity" in str(exception.value)

    def test_contact_ambig_bearing_wrong_units(self):
        contact = self.store.db_classes.Contact()

        # Check setting with a Quantity of the wrong units gives error
        with pytest.raises(ValueError) as exception:
            contact.ambig_bearing = 5 * unit_registry.second

        assert "Ambig Bearing must be a Quantity with a dimensionality of ''" in str(
            exception.value
        )

    def test_contact_ambig_bearing_wrong_units_dimensionless(self):
        contact = self.store.db_classes.Contact()

        # Check setting with a Quantity of the wrong units gives error
        with pytest.raises(ValueError) as exception:
            contact.ambig_bearing = unit_registry.Quantity(5)

        assert "Ambig Bearing must be a Quantity with angular units (degree or radian)" in str(
            exception.value
        )

    def test_contact_ambig_bearing_right_units(self):
        contact = self.store.db_classes.Contact()

        # Check setting with a Quantity of the right SI units succeeds
        contact.ambig_bearing = 178 * unit_registry.degree

        # Check setting with a Quantity of strange but valid units succeeds
        contact.ambig_bearing = 0.324 * unit_registry.radian

    def test_contact_ambig_bearing_roundtrip(self):
        contact = self.store.db_classes.Contact()

        # Check setting and retrieving field works, and gives units as a result
        contact.ambig_bearing = 234 * unit_registry.degree

        assert contact.ambig_bearing == 234 * unit_registry.degree
        assert contact.ambig_bearing.check("")

    def test_contact_ambig_bearing_class_attribute(self):
        # Check this is a valid SQLAlchemy column when used as a class attribute
        assert hasattr(self.store.db_classes.Contact.ambig_bearing, "expression")


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

        assert "MLA must be a Quantity with a dimensionality of ''" in str(exception.value)

    def test_contact_mla_wrong_units_dimensionless(self):
        contact = self.store.db_classes.Contact()

        # Check setting with a Quantity of the wrong units gives error
        with pytest.raises(ValueError) as exception:
            contact.mla = unit_registry.Quantity(5)

        assert "MLA must be a Quantity with angular units (degree or radian)" in str(
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

    def test_contact_mla_class_attribute(self):
        # Check this is a valid SQLAlchemy column when used as a class attribute
        assert hasattr(self.store.db_classes.Contact.mla, "expression")


class TestContactSLAProperty(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_contact_soa_none(self):
        contact = self.store.db_classes.Contact()

        contact.soa = None

        assert contact.soa is None

    def test_contact_soa_scalar(self):
        contact = self.store.db_classes.Contact()

        # Check setting with a scalar (float) gives error
        with pytest.raises(TypeError) as exception:
            contact.soa = 5

        assert "SOA must be a Quantity" in str(exception.value)

    def test_contact_soa_wrong_units(self):
        contact = self.store.db_classes.Contact()

        # Check setting with a Quantity of the wrong units gives error
        with pytest.raises(ValueError) as exception:
            contact.soa = 5 * unit_registry.second

        assert "SOA must be a Quantity with a dimensionality of [length]/[time]" in str(
            exception.value
        )

    def test_contact_soa_right_units(self):
        contact = self.store.db_classes.Contact()

        # Check setting with a Quantity of the right SI units succeeds
        contact.soa = 57 * (unit_registry.metre / unit_registry.second)

        # Check setting with a Quantity of strange but valid units succeeds
        contact.soa = 0.784 * (unit_registry.angstrom / unit_registry.day)

    def test_contact_soa_roundtrip(self):
        contact = self.store.db_classes.Contact()

        # Check setting and retrieving field works, and gives units as a result
        contact.soa = 19 * unit_registry.knot

        assert contact.soa == 19 * unit_registry.knot
        assert contact.soa.check("[length]/[time]")

    def test_contact_soa_class_attribute(self):
        # Check this is a valid SQLAlchemy column when used as a class attribute
        assert hasattr(self.store.db_classes.Contact.soa, "expression")


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

        assert "Orientation must be a Quantity with a dimensionality of ''" in str(exception.value)

    def test_contact_orientation_wrong_units_dimensionless(self):
        contact = self.store.db_classes.Contact()

        # Check setting with a Quantity of the wrong units gives error
        with pytest.raises(ValueError) as exception:
            contact.orientation = unit_registry.Quantity(5)

        assert "Orientation must be a Quantity with angular units (degree or radian)" in str(
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

    def test_contact_orientation_class_attribute(self):
        # Check this is a valid SQLAlchemy column when used as a class attribute
        assert hasattr(self.store.db_classes.Contact.orientation, "expression")


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

        assert "Major must be a Quantity with a dimensionality of [length]" in str(exception.value)

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

    def test_contact_major_class_attribute(self):
        # Check this is a valid SQLAlchemy column when used as a class attribute
        assert hasattr(self.store.db_classes.Contact.major, "expression")


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

        assert "Minor must be a Quantity with a dimensionality of [length]" in str(exception.value)

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

    def test_contact_minor_class_attribute(self):
        # Check this is a valid SQLAlchemy column when used as a class attribute
        assert hasattr(self.store.db_classes.Contact.minor, "expression")


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

        assert "Range must be a Quantity with a dimensionality of [length]" in str(exception.value)

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

    def test_contact_range_class_attribute(self):
        # Check this is a valid SQLAlchemy column when used as a class attribute
        assert hasattr(self.store.db_classes.Contact.range, "expression")


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

        assert "Freq must be a Quantity with a dimensionality of [time]^-1" in str(exception.value)

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

    def test_contact_freq_class_attribute(self):
        # Check this is a valid SQLAlchemy column when used as a class attribute
        assert hasattr(self.store.db_classes.Contact.freq, "expression")


CLASSES_WITH_ELEVATION = [
    pytest.param("State", id="state"),
    pytest.param("Media", id="media"),
    pytest.param("Contact", id="contact"),
]


@pytest.mark.parametrize(
    "class_name", CLASSES_WITH_ELEVATION,
)
class TestElevationProperty:
    def setup_class(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_elevation_none(self, class_name):
        obj = eval(f"self.store.db_classes.{class_name}()")

        obj.elevation = None

        assert obj.elevation is None

    def test_elevation_scalar(self, class_name):
        obj = eval(f"self.store.db_classes.{class_name}()")

        # Check setting with a scalar (float) gives error
        with pytest.raises(TypeError) as exception:
            obj.elevation = 5

        assert "Elevation must be a Quantity" in str(exception.value)

    def test_elevation_wrong_units(self, class_name):
        obj = eval(f"self.store.db_classes.{class_name}()")

        # Check setting with a Quantity of the wrong units gives error
        with pytest.raises(ValueError) as exception:
            obj.elevation = 5 * unit_registry.second

        assert "Elevation must be a Quantity with a dimensionality of [length]" in str(
            exception.value
        )

    def test_elevation_right_units(self, class_name):
        obj = eval(f"self.store.db_classes.{class_name}()")

        # Check setting with a Quantity of the right SI units succeeds
        obj.elevation = 5 * unit_registry.metre

        # Check setting with a Quantity of strange but valid units succeeds
        obj.elevation = 5 * unit_registry.angstrom

    def test_state_elevation_roundtrip(self, class_name):
        obj = eval(f"self.store.db_classes.{class_name}()")

        # Check setting and retrieving field works, and gives units as a result
        obj.elevation = 10 * unit_registry.metre

        assert obj.elevation == 10 * unit_registry.metre
        assert obj.elevation.check("[length]")

    def test_elevation_class_attribute(self, class_name):
        obj = eval(f"self.store.db_classes.{class_name}.elevation")

        assert hasattr(obj, "expression")


CLASSES_WITH_LOCATION = [
    pytest.param("State", id="state"),
    pytest.param("Media", id="media"),
    pytest.param("Contact", id="contact"),
]


@pytest.mark.parametrize(
    "class_name", CLASSES_WITH_LOCATION,
)
class TestLocationProperty:
    def setup_class(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_location_property_none(self, class_name):
        obj = eval(f"self.store.db_classes.{class_name}()")

        obj.location = None

        assert obj.location is None

    def test_location_property_invalid_type(self, class_name):
        obj = eval(f"self.store.db_classes.{class_name}()")
        with pytest.raises(TypeError) as exception:
            obj.location = (50, -1)

        assert "location value must be an instance of the Location class" in str(exception.value)

    def test_location_invalid_location(self, class_name):
        obj = eval(f"self.store.db_classes.{class_name}()")

        # Check setting with a Quantity of the wrong units gives error
        with pytest.raises(ValueError) as exception:
            obj.location = Location()

        assert "location object does not have valid values" in str(exception.value)

    def test_location_valid_location(self, class_name):
        obj = eval(f"self.store.db_classes.{class_name}()")

        loc = Location()
        loc.set_latitude_decimal_degrees(50.23)
        loc.set_longitude_decimal_degrees(-1.34)

        obj.location = loc

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

    def test_location_class_attribute(self, class_name):
        obj = eval(f"self.store.db_classes.{class_name}.elevation")

        assert hasattr(obj, "expression")


class TestActivationMinRangeProperty(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_activation_min_range_none(self):
        activation = self.store.db_classes.Activation()

        activation.min_range = None

        assert activation.min_range is None

    def test_activation_min_range_scalar(self):
        activation = self.store.db_classes.Activation()

        # Check setting with a scalar (float) gives error
        with pytest.raises(TypeError) as exception:
            activation.min_range = 5

        assert "min_range must be a Quantity" in str(exception.value)

    def test_activation_min_range_wrong_units(self):
        activation = self.store.db_classes.Activation()

        # Check setting with a Quantity of the wrong units gives error
        with pytest.raises(ValueError) as exception:
            activation.min_range = 5 * unit_registry.second

        assert "min_range must be a Quantity with a dimensionality of [length]" in str(
            exception.value
        )

    def test_activation_min_range_right_units(self):
        activation = self.store.db_classes.Activation()

        # Check setting with a Quantity of the right SI units succeeds
        activation.min_range = 57 * unit_registry.kilometre

        # Check setting with a Quantity of strange but valid units succeeds
        activation.min_range = 1523 * unit_registry.angstrom

    def test_activation_min_range_roundtrip(self):
        activation = self.store.db_classes.Activation()

        # Check setting and retrieving field works, and gives units as a result
        activation.min_range = 99 * unit_registry.metre

        assert activation.min_range == 99 * unit_registry.metre
        assert activation.min_range.check("[length]")

    def test_activation_min_range_class_attribute(self):
        # Check this is a valid SQLAlchemy column when used as a class attribute
        assert hasattr(self.store.db_classes.Activation.min_range, "expression")


class TestActivationMaxRangeProperty(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_activation_max_range_none(self):
        activation = self.store.db_classes.Activation()

        activation.max_range = None

        assert activation.max_range is None

    def test_activation_max_range_scalar(self):
        activation = self.store.db_classes.Activation()

        # Check setting with a scalar (float) gives error
        with pytest.raises(TypeError) as exception:
            activation.max_range = 5

        assert "max_range must be a Quantity" in str(exception.value)

    def test_activation_max_range_wrong_units(self):
        activation = self.store.db_classes.Activation()

        # Check setting with a Quantity of the wrong units gives error
        with pytest.raises(ValueError) as exception:
            activation.max_range = 5 * unit_registry.second

        assert "max_range must be a Quantity with a dimensionality of [length]" in str(
            exception.value
        )

    def test_activation_max_range_right_units(self):
        activation = self.store.db_classes.Activation()

        # Check setting with a Quantity of the right SI units succeeds
        activation.max_range = 23 * unit_registry.kilometre

        # Check setting with a Quantity of strange but valid units succeeds
        activation.max_range = 978 * unit_registry.angstrom

    def test_activation_max_range_roundtrip(self):
        activation = self.store.db_classes.Activation()

        # Check setting and retrieving field works, and gives units as a result
        activation.max_range = 143 * unit_registry.metre

        assert activation.max_range == 143 * unit_registry.metre
        assert activation.max_range.check("[length]")

    def test_activation_max_range_class_attribute(self):
        # Check this is a valid SQLAlchemy column when used as a class attribute
        assert hasattr(self.store.db_classes.Activation.max_range, "expression")


class TestActivationLeftArcProperty(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_activation_left_arc_none(self):
        activation = self.store.db_classes.Activation()

        activation.left_arc = None

        assert activation.left_arc is None

    def test_activation_left_arc_scalar(self):
        activation = self.store.db_classes.Activation()

        # Check setting with a scalar (float) gives error
        with pytest.raises(TypeError) as exception:
            activation.left_arc = 5

        assert "left_arc must be a Quantity" in str(exception.value)

    def test_activation_left_arc_wrong_units(self):
        activation = self.store.db_classes.Activation()

        # Check setting with a Quantity of the wrong units gives error
        with pytest.raises(ValueError) as exception:
            activation.left_arc = 5 * unit_registry.second

        assert "left_arc must be a Quantity with a dimensionality of ''" in str(exception.value)

    def test_contact_left_arc_wrong_units_dimensionless(self):
        activation = self.store.db_classes.Activation()

        # Check setting with a Quantity of the wrong units gives error
        with pytest.raises(ValueError) as exception:
            activation.left_arc = unit_registry.Quantity(5)

        assert "left_arc must be a Quantity with angular units (degree or radian)" in str(
            exception.value
        )

    def test_activation_left_arc_right_units(self):
        activation = self.store.db_classes.Activation()

        # Check setting with a Quantity of the right SI units succeeds
        activation.left_arc = 57 * unit_registry.degree

        # Check setting with a Quantity of strange but valid units succeeds
        activation.left_arc = 0.784 * unit_registry.radian

    def test_activation_left_arc_roundtrip(self):
        activation = self.store.db_classes.Activation()

        # Check setting and retrieving field works, and gives units as a result
        activation.left_arc = 157 * unit_registry.degree

        assert activation.left_arc == 157 * unit_registry.degree
        assert activation.left_arc.check("")

    def test_activation_left_arc_class_attribute(self):
        # Check this is a valid SQLAlchemy column when used as a class attribute
        assert hasattr(self.store.db_classes.Activation.left_arc, "expression")


class TestActivationRightArcProperty(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_activation_right_arc_none(self):
        activation = self.store.db_classes.Activation()

        activation.right_arc = None

        assert activation.right_arc is None

    def test_activation_right_arc_scalar(self):
        activation = self.store.db_classes.Activation()

        # Check setting with a scalar (float) gives error
        with pytest.raises(TypeError) as exception:
            activation.right_arc = 5

        assert "right_arc must be a Quantity" in str(exception.value)

    def test_activation_right_arc_wrong_units(self):
        activation = self.store.db_classes.Activation()

        # Check setting with a Quantity of the wrong units gives error
        with pytest.raises(ValueError) as exception:
            activation.right_arc = 5 * unit_registry.second

        assert "right_arc must be a Quantity with a dimensionality of ''" in str(exception.value)

    def test_contact_right_arc_wrong_units_dimensionless(self):
        activation = self.store.db_classes.Activation()

        # Check setting with a Quantity of the wrong units gives error
        with pytest.raises(ValueError) as exception:
            activation.right_arc = unit_registry.Quantity(5)

        assert "right_arc must be a Quantity with angular units (degree or radian)" in str(
            exception.value
        )

    def test_activation_right_arc_right_units(self):
        activation = self.store.db_classes.Activation()

        # Check setting with a Quantity of the right SI units succeeds
        activation.right_arc = 98 * unit_registry.degree

        # Check setting with a Quantity of strange but valid units succeeds
        activation.right_arc = 0.523 * unit_registry.radian

    def test_activation_right_arc_roundtrip(self):
        activation = self.store.db_classes.Activation()

        # Check setting and retrieving field works, and gives units as a result
        activation.right_arc = 121 * unit_registry.degree

        assert activation.right_arc == 121 * unit_registry.degree
        assert activation.right_arc.check("")

    def test_activation_right_arc_class_attribute(self):
        # Check this is a valid SQLAlchemy column when used as a class attribute
        assert hasattr(self.store.db_classes.Activation.right_arc, "expression")


class TestGeometryGeometryProperty(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_geometry_geometry_none(self):
        geometry = self.store.db_classes.Geometry1()

        geometry.geometry = None

        assert geometry.geometry is None

    def test_geometry_geometry_loc(self):
        geometry = self.store.db_classes.Geometry1()

        loc = Location()
        loc.set_latitude_decimal_degrees(50)
        loc.set_longitude_decimal_degrees(-1)

        geometry.geometry = loc

        assert geometry.geometry == loc.to_wkt()

    def test_geometry_geometry_other(self):
        geometry = self.store.db_classes.Geometry1()

        geometry.geometry = "Test String"

        assert geometry.geometry == "Test String"

    def test_geometry_class_attribute(self):
        # Check this is a valid SQLAlchemy column when used as a class attribute
        assert hasattr(self.store.db_classes.Geometry1.geometry, "expression")


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
            self.sensor_type = self.store.add_to_sensor_types(
                "test_sensor_type", self.change_id
            ).name
            self.privacy = self.store.add_to_privacies("test_privacy", 0, self.change_id).name

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

        class TestParser(Importer):
            def __init__(
                self,
                name="Test Importer",
                validation_level=validation_constants.NONE_LEVEL,
                short_name="Test Importer",
                datafile_type="Test",
            ):
                super().__init__(name, validation_level, short_name, datafile_type)
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
