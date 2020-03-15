import unittest
import pytest

from pepys_import.core.store.data_store import DataStore
from pepys_import.core.formats import unit_registry


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
