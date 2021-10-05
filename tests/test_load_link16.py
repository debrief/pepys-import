import os
import unittest
from datetime import datetime

from pint import UnitRegistry
from sqlalchemy import func

from importers.link_16_importer import Link16Importer
from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor
from tests.utils import check_errors_for_file_contents

FILE_PATH = os.path.dirname(__file__)
DATA_PATH_V1 = os.path.join(
    FILE_PATH, "sample_data/track_files/Link16/V1_GEV_09-05-2021T00-00-00.raw-PPLI_201.csv"
)
DATA_PATH_V2 = os.path.join(
    FILE_PATH, "sample_data/track_files/Link16/V2_GEV_16-05-2021T00-00-00.raw-SLOTS_JMSG.csv"
)

DATA_PATH_TIGHT_ROLLOVER = os.path.join(
    FILE_PATH,
    "sample_data/track_files/Link16/V1_Tight_Rollover_GEV_09-05-2021T09-58-16.raw-PPLI_201.csv",
)

DATA_PATH_INVALID_TIME = os.path.join(
    FILE_PATH, "sample_data/track_files/Link16/INVALID_10-10-2020T56-24-12.test.csv"
)

DATA_PATH_MIDDLE_DATE = os.path.join(
    FILE_PATH, "sample_data/track_files/Link16/GEV_01-02-2019T02-03-04_ii-ii.raw-PPLI_201.csv"
)

DATA_PATH_HOURS_IN_DATA = os.path.join(
    FILE_PATH,
    "sample_data/track_files/Link16/GEV_hours_in_data_16-05-2021T05-02-15.raw-PPLI_201.csv",
)

DATA_PATH_NO_TIMESTAMP = os.path.join(
    FILE_PATH,
    "sample_data/track_files/Link16/GEV_no_timestamp.raw-PPLI_201.csv",
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

    def test_extract_timestamp_middle_of_filename(self):
        filename = "GEV_01-02-2019T02-03-04_ii-ii.raw-PPLI_201.csv"
        result = Link16Importer.extract_timestamp(filename)
        assert result == "01-02-2019T02-03-04"
        assert Link16Importer.timestamp_to_datetime(result) == datetime(2019, 2, 1, 2, 3, 4)

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
            assert len(states) == 0

            # there must be no platforms at the beginning
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            assert len(platforms) == 0

            # there must be no datafiles at the beginning
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            assert len(datafiles) == 0

        # parse the data
        processor.process(DATA_PATH_V1, self.store, False)

        # check data got created
        with self.store.session_scope():
            # there must be states after the import
            states = self.store.session.query(self.store.db_classes.State).all()
            assert len(states) == 8

            # there must be platforms after the import
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            assert len(platforms) == 7

            # there must be one datafile afterwards
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            assert len(datafiles) == 1

            results = (
                self.store.session.query(self.store.db_classes.State)
                # Elevation == 4222 ft
                .filter(func.round(self.store.db_classes.State.elevation, 1) == 1286.9)
                .order_by(self.store.db_classes.State.time)
                .all()
            )
            # Correct elevations
            assert len(results) == 3
            # Timestamp checks
            assert results[0].time == datetime(2021, 5, 9, 1, 46, 38, 100000)
            assert results[1].time == datetime(2021, 5, 9, 2, 40, 47, 400000)
            assert results[2].time == datetime(2021, 5, 9, 3, 16, 35, 800000)

            ureg = UnitRegistry()
            # Location
            assert round(results[0].location.latitude, 6) == 0.534946
            assert round(results[0].location.longitude, 6) == 0.739102
            # Heading
            assert results[0].heading.to(ureg.degree).magnitude == 63
            # Speed
            assert results[0].speed.to(ureg.foot_per_second).magnitude == 262
            # Platform uses STN
            assert results[0].platform.name == "172"
            assert results[1].platform.name == "385"
            assert results[2].platform.name == "865"

    def test_process_link16_v2_data(self):
        processor = FileProcessor(archive=False)
        processor.register_importer(Link16Importer())

        # check states empty
        with self.store.session_scope():
            # there must be no states at the beginning
            states = self.store.session.query(self.store.db_classes.State).all()
            assert len(states) == 0

            # there must be no platforms at the beginning
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            assert len(platforms) == 0

            # there must be no datafiles at the beginning
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            assert len(datafiles) == 0

        # parse the data
        processor.process(DATA_PATH_V2, self.store, False)

        assert len(processor.importers[0].errors) == 0
        # check data got created
        with self.store.session_scope():
            # there must be states after the import
            states = self.store.session.query(self.store.db_classes.State).all()
            assert len(states) == 8

            # there must be platforms after the import
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            assert len(platforms) == 8

            # there must be one datafile afterwards
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            assert len(datafiles) == 1

            results = (
                self.store.session.query(self.store.db_classes.State)
                # Elevation == 77344 ft
                .filter(func.round(self.store.db_classes.State.elevation, 1) == 23574.5).all()
            )
            assert len(results) == 1
            assert results[0].time == datetime(2021, 5, 16, 2, 8, 40, 500000)

            ureg = UnitRegistry()
            # Location
            assert round(results[0].location.latitude, 6) == 0.004833
            assert round(results[0].location.longitude, 6) == 0.659078
            # Heading
            assert results[0].heading.to(ureg.degree).magnitude == 215
            # Speed
            assert results[0].speed.to(ureg.foot_per_second).magnitude == 0.020808275
            # Platform uses STN
            assert results[0].platform.name == "892"

    def test_invalid_timestamp(self):
        processor = FileProcessor(archive=False)
        processor.register_importer(Link16Importer())

        # parse the data
        processor.process(DATA_PATH_INVALID_TIME, self.store, False)
        errors = processor.importers[0].errors
        assert len(errors) == 1
        joined_errors = "\n".join(errors[0].values())
        assert "Error reading file" in joined_errors
        assert "Unable to read date from" in joined_errors

    def test_filename_without_timestamp(self):
        processor = FileProcessor(archive=False)
        processor.register_importer(Link16Importer())

        # parse the data
        processor.process(DATA_PATH_NO_TIMESTAMP, self.store, False)
        errors = processor.importers[0].errors
        assert len(errors) == 1
        joined_errors = "\n".join(errors[0].values())
        assert "Error reading file" in joined_errors
        assert "Unable to read date from" in joined_errors

    def test_file_with_datetime_in_middle_of_filename(self):
        processor = FileProcessor(archive=False)
        processor.register_importer(Link16Importer())

        # parse the data
        processor.process(DATA_PATH_MIDDLE_DATE, self.store, False)

        # check data got created
        with self.store.session_scope():
            # there must be states after the import
            states = self.store.session.query(self.store.db_classes.State).all()
            assert len(states) == 3

            # there must be platforms after the import
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            assert len(platforms) == 3

            # there must be one datafile afterwards
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            assert len(datafiles) == 1

            results = (
                self.store.session.query(self.store.db_classes.State)
                .filter(func.round(self.store.db_classes.State.elevation, 1) == 1286.9)
                .all()
            )
            assert len(results) == 1
            # Timestamp checks
            assert results[0].time == datetime(2019, 2, 1, 3, 46, 38, 100000)

            ureg = UnitRegistry()
            # Location
            assert round(results[0].location.latitude, 6) == 0.534946
            assert round(results[0].location.longitude, 6) == 0.739102
            # Heading
            assert results[0].heading.to(ureg.degree).magnitude == 63
            # Speed
            assert results[0].speed.to(ureg.foot_per_second).magnitude == 262
            # Platform uses STN
            assert results[0].platform.name == "172"

    def test_file_with_hours(self):
        processor = FileProcessor(archive=False)
        processor.register_importer(Link16Importer())

        # parse the data
        processor.process(DATA_PATH_HOURS_IN_DATA, self.store, False)

        # check data got created
        with self.store.session_scope():
            # there must be states after the import
            states = self.store.session.query(self.store.db_classes.State).all()
            assert len(states) == 3

            # there must be platforms after the import
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            assert len(platforms) == 3

            # there must be one datafile afterwards
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            assert len(datafiles) == 1

            results = (
                self.store.session.query(self.store.db_classes.State)
                .order_by(self.store.db_classes.State.time)
                .all()
            )
            # Correct elevations
            assert len(results) == 3
            # Timestamp checks
            assert results[0].time == datetime(2021, 5, 16, 1, 49, 23, 700000)
            assert results[1].time == datetime(2021, 5, 16, 2, 8, 24, 600000)
            assert results[2].time == datetime(2021, 5, 16, 2, 46, 38, 100000)
            # Only focus on the last one to make sure there isn't anything odd
            # about parsing when we have hour dates
            ureg = UnitRegistry()
            # Location
            assert round(results[2].location.latitude, 6) == 0.534946
            assert round(results[2].location.longitude, 6) == 0.739102
            # Heading
            assert results[2].heading.to(ureg.degree).magnitude == 63
            # Speed
            assert results[2].speed.to(ureg.foot_per_second).magnitude == 262
            # Platform uses STN
            assert results[2].platform.name == "172"

    def test_invalid_file_contents_v1(self):
        link16_importer = Link16Importer()
        # Not enough tokens test
        check_errors_for_file_contents(
            "PPLI,TOD\nSomeStr,49:23.7",
            "Not enough tokens",
            link16_importer,
            filename="link16_10-10-2020T01-02-03.test.csv",
        )

    def test_invalid_file_contents_v2(self):
        link16_importer = Link16Importer()
        # Not enough tokens test
        check_errors_for_file_contents(
            "Xmt/Rcv,SlotTime\nSomeStr,59:31.6",
            "Not enough tokens",
            link16_importer,
            filename="link16_10-10-2020T01-02-03.test.csv",
        )

    def test_non_zero_timestamp(self):
        processor = FileProcessor(archive=False)
        processor.register_importer(Link16Importer())

        # parse the data
        processor.process(DATA_PATH_TIGHT_ROLLOVER, self.store, False)

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

            # Heading changed to control ordering
            results = (
                self.store.session.query(self.store.db_classes.State)
                .order_by(self.store.db_classes.State.heading)
                .all()
            )
            assert len(results) == 8
            assert results[0].time == datetime(2021, 5, 9, 10, 3, 12, 230000)
            assert results[1].time == datetime(2021, 5, 9, 10, 8, 24, 600000)
            assert results[2].time == datetime(2021, 5, 9, 10, 46, 38, 100000)
            assert results[3].time == datetime(2021, 5, 9, 11, 38, 18, 0)


if __name__ == "__main__":
    unittest.main()
