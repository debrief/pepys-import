import unittest
import pytest

from pepys_import.core.store.data_store import DataStore
from pepys_import.core.formats import unit_registry


class TestProperties(unittest.TestCase):
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
