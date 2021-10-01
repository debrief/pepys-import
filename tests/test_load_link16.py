import os
import unittest
from datetime import datetime

from sqlalchemy import func

from importers.link_16_importer import Link16Importer
from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor

FILE_PATH = os.path.dirname(__file__)
DATA_PATH_V1 = os.path.join(
    FILE_PATH, "sample_data/track_files/Link16/V1_GEV_09-05-2021T00-00-00.raw-PPLI_201.csv"
)
DATA_PATH_V2 = os.path.join(
    FILE_PATH, "sample_data/track_files/Link16/V2_GEV_16-05-2021T00-00-00.raw-SLOTS_JMSG.csv"
)


class TestLoadLink16(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_extract_timestamp_relative_v1(self):
        filename = "GEV_09-05-2021T16-10-00.raw-PPLI_201.csv"
        assert Link16Importer.extract_timestamp(filename) == "09-05-2021T16-10-00"

    def test_extract_timestamp_relative_v2(self):
        filename = "GEV_12-09-2021T09-25-00.raw-SLOTS_JMSG.csv"
        assert Link16Importer.extract_timestamp(filename) == "12-09-2021T09-25-00"

    def test_convert_timestamp_ambiguous_day_month(self):
        timestamp = "09-05-2021T16-10-00"
        assert Link16Importer.timestamp_to_datetime(timestamp) == datetime(2021, 5, 9, 16, 10, 0)

    def test_convert_timestamp_missing(self):
        timestamp = ""
        assert Link16Importer.timestamp_to_datetime(timestamp) is False

    def test_convert_timestamp_invalid(self):
        timestamp = "123456-7-8-9"
        assert Link16Importer.timestamp_to_datetime(timestamp) is False

    def test_process_link16_v1_data(self):
        processor = FileProcessor(archive=False)
        processor.register_importer(Link16Importer())

        # check states empty
        with self.store.session_scope():
            # there must be no states at the beginning
            states = self.store.session.query(self.store.db_classes.State).all()
            self.assertEqual(len(states), 0)

            # there must be no platforms at the beginning
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            self.assertEqual(len(platforms), 0)

            # there must be no datafiles at the beginning
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 0)

        # parse the data
        processor.process(DATA_PATH_V1, self.store, False)

        # check data got created
        with self.store.session_scope():
            # there must be states after the import
            states = self.store.session.query(self.store.db_classes.State).all()
            self.assertEqual(len(states), 8)

            # there must be platforms after the import
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            self.assertEqual(len(platforms), 7)

            # there must be one datafile afterwards
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 1)

            results = (
                self.store.session.query(self.store.db_classes.State)
                # Elevation == 4222 ft
                .filter(func.round(self.store.db_classes.State.elevation, 1) == 1286.9)
                .order_by(self.store.db_classes.State.time)
                .all()
            )
            assert len(results) == 3
            assert results[0].time == datetime(2021, 5, 9, 1, 46, 38, 100000)
            assert results[1].time == datetime(2021, 5, 9, 2, 40, 47, 400000)
            assert results[2].time == datetime(2021, 5, 9, 3, 16, 35, 800000)

    def test_process_link16_v2_data(self):
        processor = FileProcessor(archive=False)
        processor.register_importer(Link16Importer())

        # check states empty
        with self.store.session_scope():
            # there must be no states at the beginning
            states = self.store.session.query(self.store.db_classes.State).all()
            self.assertEqual(len(states), 0)

            # there must be no platforms at the beginning
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            self.assertEqual(len(platforms), 0)

            # there must be no datafiles at the beginning
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 0)

        # parse the data
        processor.process(DATA_PATH_V2, self.store, False)

        # check data got created
        with self.store.session_scope():
            # there must be states after the import
            states = self.store.session.query(self.store.db_classes.State).all()
            self.assertEqual(len(states), 8)

            # there must be platforms after the import
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            self.assertEqual(len(platforms), 8)

            # there must be one datafile afterwards
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 1)

            results = (
                self.store.session.query(self.store.db_classes.State)
                # Elevation == 77344 ft
                .filter(func.round(self.store.db_classes.State.elevation, 1) == 23574.5).all()
            )
            assert len(results) == 1
            assert results[0].time == datetime(2021, 5, 16, 2, 8, 40, 500000)


""" Things to test:
        Parse the date/time stamp from the name
        Roll timestamps forward correctly
        We can read v1 format
        We can read v2 format
        Check incorrect # of tokens for v1 format throws error
        Check incorrect # of tokens for v2 format throws error

"""


if __name__ == "__main__":
    unittest.main()
