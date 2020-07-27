import datetime
import os
import unittest

from importers.eag_importer import EAGImporter
from pepys_import.core.formats import unit_registry
from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor
from tests.utils import check_errors_for_file_contents

FILE_PATH = os.path.dirname(__file__)
DATA_PATH_NO_HEADER = os.path.join(
    FILE_PATH, "sample_data/track_files/other_data/20200305_ROBIN.eag.txt"
)
DATA_PATH_WITH_HEADER = os.path.join(
    FILE_PATH, "sample_data/track_files/other_data/20200305_ROBINWithHeader.eag.txt"
)


class TestLoadEAG(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_process_eag_data_no_header(self):
        processor = FileProcessor(archive=False)
        processor.register_importer(EAGImporter())

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

        # parse the file
        processor.process(DATA_PATH_NO_HEADER, self.store, False)

        # check data got created
        with self.store.session_scope():
            # there must be 4 states after the import
            states = self.store.session.query(self.store.db_classes.State).all()
            self.assertEqual(len(states), 4)

            # there must be 1 platform after the import
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            self.assertEqual(len(platforms), 1)

            # there must be one datafile afterwards
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 1)

            # Get all the States entries
            states = self.store.session.query(self.store.db_classes.State).all()

            # Note: the lat/lon/elevation values used to calculate the ECEF values
            # in the test file were:
            # 51, -1.400000, 1500.01
            # 51.500000, -1.350000, 2000.01
            # 51.75, -1.32, 2300
            # 52, -1.30, 2700
            # Conversion to ECEF was done using http://www.sysense.com/products/ecef_lla_converter/index.html

            # Check the values match with the values in the file
            # We have to do rounding here, as the ECEF to Lat Lon conversion gives very
            # small errors
            assert round(states[0].location.longitude, 2) == -1.4
            assert round(states[0].location.latitude, 2) == 51
            assert round(states[0].elevation, 0) == 1500 * unit_registry.metre
            assert states[0].heading == 98.2 * unit_registry.degrees

            assert states[0].time == datetime.datetime(2020, 3, 5, 10, 15, 7)

            assert round(states[3].location.longitude, 2) == -1.3
            assert round(states[3].location.latitude, 2) == 52
            assert states[3].heading == 156.8 * unit_registry.degrees
            assert states[3].time == datetime.datetime(2020, 3, 5, 10, 15, 27)

    def test_process_eag_data_with_header(self):
        processor = FileProcessor(archive=False)
        processor.register_importer(EAGImporter())

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

        # parse the file
        processor.process(DATA_PATH_WITH_HEADER, self.store, False)

        # check data got created
        with self.store.session_scope():
            # there must be 4 states after the import
            states = self.store.session.query(self.store.db_classes.State).all()
            self.assertEqual(len(states), 4)

            # there must be 2 platforms after the import
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            assert len(platforms) == 2

            # there must be one datafile afterwards
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 1)

            # Get all the States entries
            states = self.store.session.query(self.store.db_classes.State).all()

            # Check that the platforms were assigned to the states correctly, based
            # on the header and the track ID column.
            # No need to check actual parsed values of other fields here, as they are the
            # same as those checked in the previous test
            assert platforms[0].name == "CALLSIGN 1"
            assert platforms[1].name == "CALLSIGN 2"

            data = [(s.heading, s.platform_name) for s in states]

            assert (98.2 * unit_registry.degree, "CALLSIGN 1") in data
            assert (104.2 * unit_registry.degree, "CALLSIGN 2") in data
            assert (156.8 * unit_registry.degree, "CALLSIGN 1") in data

    def test_process_eag_data_invalid(self):
        eag_importer = EAGImporter()

        # Invalid filename
        check_errors_for_file_contents(
            "Blah",
            "Error in filename - cannot parse date",
            eag_importer,
            filename="20200345_ROBIN.eag.txt",
        )

        # Too many tokens in line
        check_errors_for_file_contents(
            "382512000	2	123	456	3978788.87  -93765.36    ExtraToken   4969927.68	0	0	104.2	10:15:12.00",
            "Incorrect number of tokens",
            eag_importer,
            filename="20200305_ROBIN.eag.txt",
        )

        # Invalid float for time since Sunday
        check_errors_for_file_contents(
            "382517A00	2	123	456	3957216.04  -91183.85       4987436.42	0	0	126.3	10:15:17.00",
            "Cannot parse time since Sunday to float",
            eag_importer,
            filename="20200305_ROBIN.eag.txt",
        )

        # Track ID listed in row but not found in header
        contents_with_header = """A   1   152 130 23  13  CALLSIGN 1
        A   2   192 130 23  13  CALLSIGN 2
        382507000	1	123	456	4021773.74  -98290.03       4934710.34	0	0	98.2	10:15:07.00
        382512000	4	123	456	3978788.87  -93765.36       4969927.68	0	0	104.2	10:15:12.00"""
        check_errors_for_file_contents(
            contents_with_header,
            "Track ID 4 not found in header",
            eag_importer,
            filename="20200305_ROBIN.eag.txt",
        )

        # Invalid float for ECEF values
        check_errors_for_file_contents(
            "382507000	2	123	456	3957A16.04  -91183.85       4987436.42	0	0	126.3	10:15:17.00",
            "Error: cannot parse ECEF values to floats",
            eag_importer,
            filename="20200305_ROBIN.eag.txt",
        )

        # Invalid heading
        check_errors_for_file_contents(
            "382512000	2	123	456	3978788.87  -93765.36    4969927.68	0	0	10A.2	10:15:12.00",
            "Error in angle value",
            eag_importer,
            filename="20200305_ROBIN.eag.txt",
        )


if __name__ == "__main__":
    unittest.main()
