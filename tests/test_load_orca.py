import unittest

from pepys_import.core.store.data_store import DataStore


class TestLoadOrca(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass
