import unittest

from datetime import datetime
from pepys_import.core.store.data_store import DataStore


class MissingFieldsTestCase(unittest.TestCase):
    """This class includes tests where missing fields given to add methods"""

    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

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

    @unittest.expectedFailure
    def test_missing_fields_for_add_to_datafiles(self):
        with self.store.session_scope():
            self.store.add_to_datafiles(simulated=True, privacy=None, file_type=None)


if __name__ == "__main__":
    unittest.main()
