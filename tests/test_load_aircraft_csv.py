import datetime
import os
import unittest

from importers.aircraft_csv_format_importer import AircraftCsvFormatImporter
from pepys_import.core.formats import unit_registry
from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor
from tests.utils import check_errors_for_file_contents

FILE_PATH = os.path.dirname(__file__)
DATA_PATH_SHORT = os.path.join(FILE_PATH, "sample_data/track_files/csv_data/aircraft/OwnPos_UC.csv")
DATA_PATH_LONG = os.path.join(
    FILE_PATH, "sample_data/track_files/csv_data/aircraft/OwnPos_UC_Long.csv"
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

            # there should only be one data file at the end of the test
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 1)

            # Check that there is an elevation of 1215 reported
            results = self.store.session.query(self.store.db_classes.State).all()
            assert len(results) == 1
            assert results[0].time == datetime.datetime(2020, 3, 15, 10, 9, 0)
            assert round(results[0].elevation, 2) == 370.33 * unit_registry.metre
            assert results[0].course == 311 * unit_registry.degree
            assert round(results[0].speed.magnitude, 2) == 41.82
            assert round(results[0].location.longitude, 2) == -5.10
            assert round(results[0].location.latitude, 2) == 50.62

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

    def test_process_aircraft_csv_invalid(self):
        # pylint: disable=no-self-use
        aircraft_importer = AircraftCsvFormatImporter()

        # Invalid number of tokens - too few on line
        check_errors_for_file_contents(
            "Date(Uk), \n Blah, Blah",
            "Incorrect number of tokens:",
            aircraft_importer,
            filename="OwnPos_UC.csv",
        )

        # Test Invalid Date format
        check_errors_for_file_contents(
            "Date(Uk), \n 20/03/15, 10:09:00, 50:37.12N, 005:06.24W, 50.61867, -5.104, 1215, 81.3, 311",
            "should be 10 figure date",
            aircraft_importer,
            filename="OwnPos_UC.csv",
        )

        # Test Incorrect Date format
        check_errors_for_file_contents(
            "Date(Uk), \n 99/03/2015, 10:09:00, 50:37.12N, 005:06.24W, 50.61867, -5.104, 1215, 81.3, 311",
            "Error in timestamp parsing.",
            aircraft_importer,
            filename="OwnPos_UC.csv",
        )

        # Test Invalid Time format
        check_errors_for_file_contents(
            "Date(Uk), \n 15/03/2020, 10:09, 50:37.12N, 005:06.24W, 50.61867, -5.104, 1215, 81.3, 311",
            "Should be HH:mm:ss",
            aircraft_importer,
            filename="OwnPos_UC.csv",
        )

        # Test Incorrect Time Value
        check_errors_for_file_contents(
            "Date(Uk), \n 15/03/2020, 99:99:99, 50:37.12N, 005:06.24W, 50.61867, -5.104, 1215, 81.3, 311",
            "Error in timestamp parsing.",
            aircraft_importer,
            filename="OwnPos_UC.csv",
        )

        # Test error in location parsing
        check_errors_for_file_contents(
            "Date(Uk), \n 15/03/2020, 10:09:00, 50:37.12N, 005:06.24W, #VALUE, #VALUE, 1215, 81.3, 311",
            "Couldn't convert to a number",
            aircraft_importer,
            filename="OwnPos_UC.csv",
        )

        # Test error in altitude value
        check_errors_for_file_contents(
            "Date(Uk), \n 15/03/2020, 10:09:00, 50:37.12N, 005:06.24W, 50.61867, -5.104, #VALUE, 81.3, 311",
            "Couldn't convert to a number",
            aircraft_importer,
            filename="OwnPos_UC.csv",
        )

        # Test error in speed value
        check_errors_for_file_contents(
            "Date(Uk), \n 15/03/2020, 10:09:00, 50:37.12N, 005:06.24W, 50.61867, -5.104, 1215, #VALUE, 311",
            "Couldn't convert to a number",
            aircraft_importer,
            filename="OwnPos_UC.csv",
        )

        # Test error in course value
        check_errors_for_file_contents(
            "Date(Uk), \n 15/03/2020, 10:09:00, 50:37.12N, 005:06.24W, 50.61867, -5.104, 1215, 81.3, #VALUE",
            "Couldn't convert to a number",
            aircraft_importer,
            filename="OwnPos_UC.csv",
        )


if __name__ == "__main__":
    unittest.main()
