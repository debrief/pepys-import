# import datetime
import os
import unittest

from importers.link_16_importer import Link16Importer
from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor

FILE_PATH = os.path.dirname(__file__)
DATA_PATH_V1 = os.path.join(
    FILE_PATH, "sample_data/track_files/Link16/Sample.Data.GEV.Link.16.V1.csv"
)
DATA_PATH_V2 = os.path.join(
    FILE_PATH, "sample_data/track_files/Link16/Sample.Data.GEV.Link.16.V2.csv"
)


class TestLoadLink16(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

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

    #         # there must be platforms after the import
    #         platforms = self.store.session.query(self.store.db_classes.Platform).all()
    #         self.assertEqual(len(platforms), 18)

    #         # there must be one datafile afterwards
    #         datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
    #         self.assertEqual(len(datafiles), 1)

    #         # Check that there is an elevation of 147 reported (test file was manually edited
    #         # to contain an elevation of 147m)
    #         results = (
    #             self.store.session.query(self.store.db_classes.State)
    #             .filter(self.store.db_classes.State.elevation == 147)
    #             .all()
    #         )
    #         assert len(results) == 1
    #         assert results[0].time == datetime.datetime(2019, 8, 6, 4, 40, 0)


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
