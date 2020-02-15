import unittest

from unittest import TestCase
from testing.postgresql import Postgresql
from pepys_import.core.store.data_store import DataStore
from pepys_import.core.store.db_base import BaseSpatiaLite


class UnknownDBTestCase(TestCase):
    @unittest.expectedFailure
    def test_unknown_database_type(self):
        """Test whether DataStore raises exception when unknown database name entered"""
        DataStore("", "", "", 0, "", db_type="TestDB")


if __name__ == "__main__":
    unittest.main()
