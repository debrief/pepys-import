import unittest

from pepys_import.core.store.data_store import DataStore


class MissingFieldsTestCase(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    @unittest.expectedFailure
    def test_missing_fields_for_add_to_states(self):
        with self.store.session_scope() as session:
            self.store.add_to_states(
                time="2020-02-01 19:00:00", sensor=None, datafile=None
            )

    @unittest.expectedFailure
    def test_missing_fields_for_add_to_sensors(self):
        with self.store.session_scope() as session:
            self.store.add_to_sensors(name="Sensor-1", sensor_type=None, host=None)

    @unittest.expectedFailure
    def test_missing_fields_for_add_to_datafiles(self):
        with self.store.session_scope() as session:
            self.store.add_to_datafiles(simulated=True, privacy=None, file_type=None)

    @unittest.expectedFailure
    def test_missing_fields_for_add_to_platforms(self):
        with self.store.session_scope() as session:
            self.store.add_to_platforms(
                name="Platform-1", platform_type=None, privacy=None, nationality=None
            )


if __name__ == "__main__":
    unittest.main()
