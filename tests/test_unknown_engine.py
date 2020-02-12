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


# Not working yet, metadata must be broken to raise Operational Error
class DBConnectionTestCase(TestCase):
    @unittest.expectedFailure
    def test_unknown_engine_for_spatialite(self):
        """Test whether DataStore raises exception when unknown database name entered"""
        store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        BaseSpatiaLite.metadata.create_all(store.engine)
        store.engine = None
        # it must raise exception during initialise()
        store.initialise()

    @unittest.expectedFailure
    def test_unknown_engine_for_postgis(self):
        """Test whether DataStore raises exception when unknown database name entered"""
        postgres = Postgresql(
            database="test",
            host="localhost",
            user="postgres",
            password="postgres",
            port=55527,
        )
        store = DataStore(
            db_username="postgres",
            db_password="postgres",
            db_host="localhost",
            db_port=55527,
            db_name="test",
        )
        store.engine = None
        # it must raise exception during initialise()
        store.initialise()


if __name__ == "__main__":
    unittest.main()
