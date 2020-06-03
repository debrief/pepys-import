import unittest
from datetime import datetime

import pytest

from pepys_import.core.store.data_store import DataStore
from pepys_import.utils.data_store_utils import MissingDataException


class MissingFieldsTestCase(unittest.TestCase):
    """This class includes tests where missing fields given to add methods"""

    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

        with self.store.session_scope():
            self.store.populate_reference()
            self.change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id

    def tearDown(self):
        pass

    @unittest.expectedFailure
    def test_missing_fields_for_add_to_states(self):
        with self.store.session_scope():
            self.store.add_to_states(time=datetime.utcnow(), sensor=None, datafile=None)

    @unittest.expectedFailure
    def test_missing_fields_for_add_to_sensors(self):
        with self.store.session_scope():
            self.store.add_to_sensors(name="Sensor-1", sensor_type=None, host=None)

    def test_missing_fields_for_add_to_datafiles(self):
        with self.store.session_scope():
            with pytest.raises(MissingDataException):
                self.store.add_to_datafiles(
                    "PRIVACY-DoesNotExist",
                    "DATAFILE-TYPE-1",
                    "DATAFILE-1",
                    True,
                    0,
                    "HASHED-1",
                    change_id=self.change_id,
                )

            with pytest.raises(MissingDataException):
                self.store.add_to_datafiles(
                    "PRIVACY-1",
                    "DATAFILE-TYPE-1-DoesNotExist",
                    "DATAFILE-1",
                    True,
                    0,
                    "HASHED-1",
                    change_id=self.change_id,
                )

            # Shouldn't raise an exception, as all valid
            self.store.add_to_datafiles(
                "PRIVACY-1",
                "DATAFILE-TYPE-1",
                "DATAFILE-1",
                True,
                0,
                "HASHED-1",
                change_id=self.change_id,
            )


if __name__ == "__main__":
    unittest.main()
