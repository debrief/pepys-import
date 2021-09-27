import os
import unittest
from datetime import datetime

import pytest
from geoalchemy2 import WKTElement
from sqlalchemy import func
from sqlalchemy.exc import OperationalError
from testing.postgresql import Postgresql

from pepys_import.core.formats.location import Location
from pepys_import.core.store.data_store import DataStore

FILE_PATH = os.path.dirname(__file__)
TEST_DATA_PATH = os.path.join(FILE_PATH, "sample_data", "csv_files")


class SpatialDataSpatialiteTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()
        with self.store.session_scope():
            self.store.populate_reference(TEST_DATA_PATH)
            self.store.populate_metadata(TEST_DATA_PATH)

            platform = self.store.search_platform("PLATFORM-1", "United Kingdom", "123")
            sensor = self.store.search_sensor("SENSOR-1", platform.platform_id)
            datafile = self.store.search_datafile("DATAFILE-1")

            # Add an example State object
            State = self.store.db_classes.State
            timestamp = datetime(2020, 1, 1, 1, 2, 3)
            state = State(
                sensor_id=sensor.sensor_id, time=timestamp, source_id=datafile.datafile_id
            )

            loc = Location()
            loc.set_latitude_decimal_degrees(32)
            loc.set_longitude_decimal_degrees(46)

            state.location = loc
            self.store.session.add(state)

    def tearDown(self) -> None:
        pass

    def test_location(self):
        """Test location saved as Geo Point and it is possible to filter State objects on SpatiaLite"""
        with self.store.session_scope():
            # Filter state object by spatial location
            first_state = (
                self.store.session.query(self.store.db_classes.State)
                .filter(
                    func.ST_Contains(
                        self.store.db_classes.State.location,
                        WKTElement("POINT(46.000 32.000)", srid=4326),
                    )
                )
                .one()
            )
            correct_loc = Location()
            correct_loc.set_latitude_decimal_degrees(32)
            correct_loc.set_longitude_decimal_degrees(46)

            assert first_state.location == correct_loc

    def test_non_existing_location(self):
        """Test filtering State objects by non existing point returns None on SpatiaLite"""

        with self.store.session_scope():
            # Filter state object by spatial location
            first_state = (
                self.store.session.query(self.store.db_classes.State)
                .filter(
                    func.ST_Contains(
                        self.store.db_classes.State.location,
                        WKTElement("POINT(123456 123456)", srid=4326),
                    )
                )
                .one_or_none()
            )
            # There is no State object with location (123456 123456). Should return None
            self.assertIsNone(first_state)


@pytest.mark.postgres
class SpatialDataPostGISTestCase(unittest.TestCase):
    def setUp(self):
        self.postgres = None
        self.store = None
        try:
            self.postgres = Postgresql(
                database="test",
                host="localhost",
                user="postgres",
                password="postgres",
                port=55527,
            )
        except RuntimeError:
            raise Exception("Testing Postgres server could not be started/accessed")
        try:
            self.store = DataStore(
                db_name="test",
                db_host="localhost",
                db_username="postgres",
                db_password="postgres",
                db_port=55527,
                db_type="postgres",
            )
            self.store.initialise()
            with self.store.session_scope():
                self.store.populate_reference(TEST_DATA_PATH)
                self.store.populate_metadata(TEST_DATA_PATH)

                platform = self.store.search_platform("PLATFORM-1", "United Kingdom", "123")
                sensor = self.store.search_sensor("SENSOR-1", platform.platform_id)
                datafile = self.store.search_datafile("DATAFILE-1")

                # Add an example State object
                State = self.store.db_classes.State
                timestamp = datetime(2020, 1, 1, 1, 2, 3)
                state = State(
                    sensor_id=sensor.sensor_id, time=timestamp, source_id=datafile.datafile_id
                )

                loc = Location()
                loc.set_latitude_decimal_degrees(32)
                loc.set_longitude_decimal_degrees(46)

                state.location = loc
                self.store.session.add(state)
        except OperationalError:
            raise Exception("Creating database schema in testing Postgres database failed")

    def tearDown(self):
        try:
            self.postgres.stop()
        except AttributeError:
            return

    def test_location(self):
        """Test location saved as Geo Point and it is possible to filter State objects on PostGIS"""
        if self.postgres is None:
            self.skipTest("Postgres is not available. Test is skipping")

        with self.store.session_scope():
            # Filter state object by spatial location
            first_state = (
                self.store.session.query(self.store.db_classes.State)
                .filter(
                    func.ST_Contains(
                        self.store.db_classes.State.location,
                        WKTElement("POINT(46.000 32.000)", srid=4326),
                    )
                )
                .one()
            )

            correct_loc = Location()
            correct_loc.set_latitude_decimal_degrees(32)
            correct_loc.set_longitude_decimal_degrees(46)

            assert first_state.location == correct_loc

    def test_non_existing_location(self):
        """Test filtering State objects by non existing point returns None on PostGIS"""

        if self.store is None:
            self.skipTest("Postgres is not available. Test is skipping")

        with self.store.session_scope():
            # Filter state object by spatial location
            first_state = (
                self.store.session.query(self.store.db_classes.State)
                .filter(
                    func.ST_Contains(
                        self.store.db_classes.State.location,
                        WKTElement("POINT(123456 123456)", srid=4326),
                    )
                )
                .one_or_none()
            )
            # There is no State object with location (123456 123456). Should return None
            self.assertIsNone(first_state)


if __name__ == "__main__":
    unittest.main()
