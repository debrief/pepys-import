import unittest

from pepys_import.core.store.data_store import DataStore
from unittest import TestCase


class TestDataStore(TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_new_datafile_added_successfully(self):
        """Test whether a new datafile is created successfully or not"""

        with self.store.session_scope() as session:
            datafiles = self.store.get_datafiles()

        # there must be no entry at the beginning
        self.assertEqual(len(datafiles), 0)

        with self.store.session_scope() as session:
            created_datafile = self.store.get_datafile("test_file.csv", "csv")

        # there must be one entry
        with self.store.session_scope() as session:
            datafiles = self.store.get_datafiles()
        self.assertEqual(len(datafiles), 1)

    def test_present_datafile_not_added(self):
        pass

    def test_new_platform_added_successfully(self):
        pass

    def test_present_platform_not_added(self):
        pass

    def test_new_sensor_added_successfully(self):
        pass

    def test_present_sensor_not_added(self):
        pass


if __name__ == "__main__":
    unittest.main()
