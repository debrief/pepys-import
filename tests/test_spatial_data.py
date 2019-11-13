import unittest
import os

from geoalchemy2 import WKBElement
from sqlalchemy import func, event
from sqlalchemy.schema import DropSchema
from testing.postgresql import Postgresql

from pepys_import.core.store.data_store import DataStore
from pepys_import.core.store.db_base import base_postgres

FILE_PATH = os.path.dirname(__file__)
TEST_DATA_PATH = os.path.join(FILE_PATH, "sample_data", "csv_files")


class SpatialDataSpatialiteTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()
        self.store.populate_reference(TEST_DATA_PATH)
        self.store.populate_metadata(TEST_DATA_PATH)
        self.store.populate_measurement(TEST_DATA_PATH)

    def tearDown(self) -> None:
        pass

    def test_location(self):
        with self.store.session_scope() as session:
            # Filter state object by spatial location
            first_state = (
                self.store.session.query(self.store.db_classes.State)
                .filter(
                    self.store.db_classes.State.location.ST_Contains(
                        WKBElement("POINT(46.000 32.000)")
                    )
                )
                .first()
            )
            point = self.store.session.query(func.ST_AsText(first_state.location)).one()

            # Check location point's type and WKTE value
            self.assertFalse(isinstance(first_state.location, str))
            self.assertTrue(isinstance(first_state.location, WKBElement))
            self.assertEqual(
                point[0], "POINT(46 32)",
            )


class SpatialDataPostGISTestCase(unittest.TestCase):
    def setUp(self):
        self.store = None
        try:
            self.store = Postgresql(
                database="test",
                host="localhost",
                user="postgres",
                password="postgres",
                port=55527,
            )
        except RuntimeError:
            print("PostgreSQL database couldn't be created! Test is skipping.")

    def tearDown(self):
        try:
            event.listen(
                base_postgres.metadata, "before_create", DropSchema("datastore_schema"),
            )
            self.store.stop()
        except AttributeError:
            return

    def test_location(self):
        """Test whether schemas created successfully on PostgresSQL"""
        if self.store is None:
            self.skipTest("Postgres is not available. Test is skipping")

        data_store = DataStore(
            db_name="test",
            db_host="localhost",
            db_username="postgres",
            db_password="postgres",
            db_port=55527,
        )
        data_store.initialise()
        data_store.populate_reference(TEST_DATA_PATH)
        data_store.populate_metadata(TEST_DATA_PATH)
        data_store.populate_measurement(TEST_DATA_PATH)

        with data_store.session_scope() as session:
            # Filter state object by spatial location
            first_state = (
                data_store.session.query(data_store.db_classes.State)
                .filter(
                    func.ST_Contains(
                        data_store.db_classes.State.location, "POINT(46.000 32.000)"
                    )
                )
                .first()
            )
            point = data_store.session.query(func.ST_AsText(first_state.location)).one()

            # Check location point's type and WKBE value
            self.assertFalse(isinstance(first_state.location, str))
            self.assertTrue(isinstance(first_state.location, WKBElement))
            self.assertEqual(
                point[0], "POINT(46 32)",
            )


if __name__ == "__main__":
    unittest.main()
