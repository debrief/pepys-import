import datetime
import os
import unittest

import pytest
from testing.postgresql import Postgresql

from importers.gpx_importer import GPXImporter
from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor

FILE_PATH = os.path.dirname(__file__)
DATA_PATH = os.path.join(FILE_PATH, "sample_data/track_files/gpx/gpx_1_1.gpx")


def test_gpx_timezone_sqlite():
    store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    store.initialise()

    processor = FileProcessor(archive=False)
    processor.register_importer(GPXImporter())

    # parse the folder
    processor.process(DATA_PATH, store, False)

    # check data got created
    with store.session_scope():
        # there must be states after the import
        states = store.session.query(store.db_classes.State).all()

        assert states[0].time == datetime.datetime(2012, 4, 27, 15, 29, 38)


@pytest.mark.postgres
class TestGPXTimezonePostgres(unittest.TestCase):
    def setUp(self):
        self.postgres = None

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

        self.postgres_store = DataStore(
            db_name="test",
            db_host="localhost",
            db_username="postgres",
            db_password="postgres",
            db_port=55527,
            db_type="postgres",
        )

        self.postgres_store.initialise()

    def tearDown(self):
        try:
            self.postgres.stop()
        except AttributeError:
            return

    def test_gpx_timezone_postgres(self):
        processor = FileProcessor(archive=False)
        processor.register_importer(GPXImporter())

        processor.process(DATA_PATH, self.postgres_store, False)

        with self.postgres_store.session_scope():
            postgres_results = (
                self.postgres_store.session.query(self.postgres_store.db_classes.State)
                .order_by(self.postgres_store.db_classes.State.time)
                .all()
            )

            assert postgres_results[0].time == datetime.datetime(2012, 4, 27, 15, 29, 38)


@pytest.mark.postgres
class TestTimesEqualDifferentDBs(unittest.TestCase):
    def setUp(self):
        self.postgres = None

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

        self.postgres_store = DataStore(
            db_name="test",
            db_host="localhost",
            db_username="postgres",
            db_password="postgres",
            db_port=55527,
            db_type="postgres",
        )
        self.sqlite_store = DataStore("", "", "", 0, db_name="slave.sqlite", db_type="sqlite")

        self.postgres_store.initialise()
        self.sqlite_store.initialise()

    def tearDown(self):
        try:
            self.postgres.stop()
        except AttributeError:
            return

    def test_gpx_timezones_values_equal_postgres_sqlite(self):
        processor = FileProcessor(archive=False)
        processor.register_importer(GPXImporter())

        processor.process(DATA_PATH, self.sqlite_store, False)
        processor.process(DATA_PATH, self.postgres_store, False)

        with self.postgres_store.session_scope():
            with self.sqlite_store.session_scope():
                sqlite_results = (
                    self.sqlite_store.session.query(self.sqlite_store.db_classes.State)
                    .order_by(self.sqlite_store.db_classes.State.time)
                    .all()
                )
                postgres_results = (
                    self.postgres_store.session.query(self.postgres_store.db_classes.State)
                    .order_by(self.postgres_store.db_classes.State.time)
                    .all()
                )

                sqlite_times = [result.time for result in sqlite_results]
                postgres_times = [result.time for result in postgres_results]

                assert sqlite_times == postgres_times
