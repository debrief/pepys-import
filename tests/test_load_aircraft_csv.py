import datetime
import os
import unittest

from importers.aircraft_csv_format_importer import AircraftCsvFormatImporter
from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor
from tests.utils import check_errors_for_file_contents

FILE_PATH = os.path.dirname(__file__)
DATA_PATH_SHORT = os.path.join(FILE_PATH, "sample_data/track_files/csv_data/aircraft/OwnPos_UC.csv")
DATA_PATH_LONG = os.path.join(
    FILE_PATH, "sample_data/track_files/csv_data/aircraft/OwnPos_UC_Long.csv"
)
DATA_PATH_MISSING = os.path.join(
    FILE_PATH, "sample_data/track_files/csv_data/aircraft/OwnPos_UC_MissingData.csv"
)


class TestLoadAircraftCSV(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_process_aircraft_csv_data(self):
        processor = FileProcessor(archive=False)
        processor.register_importer(AircraftCsvFormatImporter())

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

        # parse the folder
        processor.process(DATA_PATH_SHORT, self.store, False)

        # check data got created
        with self.store.session_scope():
            # there must be states after the import
            states = self.store.session.query(self.store.db_classes.State).all()
            self.assertEqual(len(states), 1)

            # there must be a single platform after the import
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            self.assertEqual(len(platforms), 1)

            # there must be two datafiles afterwards - two files being processed
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 1)

            # Check that there is an elevation of 147 reported (test file was manually edited
            # to contain an elevation of 147m)
            results = (
                self.store.session.query(self.store.db_classes.State)
                .filter(self.store.db_classes.State.elevation == 1215)
                .all()
            )
            assert len(results) == 1
            print(results[0].time)
            assert results[0].time == datetime.datetime(2020, 3, 15, 10, 9, 0)

    def test_process_aircraft_csv_long(self):
        processor = FileProcessor(archive=False)
        processor.register_importer(AircraftCsvFormatImporter())

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

        # parse the folder
        processor.process(DATA_PATH_LONG, self.store, False)

        # check data got created
        with self.store.session_scope():
            # there must be states after the import
            states = self.store.session.query(self.store.db_classes.State).all()
            self.assertEqual(len(states), 20001)

            # there must be a single platform after the import
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            self.assertEqual(len(platforms), 1)

            # there must be two datafiles afterwards - two files being processed
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 1)

            # Check that there is an elevation of 0 reported (test file was manually edited
            # to contain an elevation of 0m)
            results = (
                self.store.session.query(self.store.db_classes.State)
                .filter(self.store.db_classes.State.elevation == 0)
                .all()
            )
            assert len(results) == 1
            assert results[0].time == datetime.datetime(2021, 7, 16, 8, 12, 0)

    def test_process_aircraft_csv_data_invalid(self):
        aircraft_importer = AircraftCsvFormatImporter()

        # Invalid number of tokens - too few on line
        check_errors_for_file_contents(
            "Blah, Blah",
            "Not enough tokens:",
            aircraft_importer,
            filename="OwnPos_UC.csv",
        )


if __name__ == "__main__":
    unittest.main()
