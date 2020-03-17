import os
import unittest
import math

from sqlalchemy import func
from geoalchemy2 import WKBElement

from unittest.mock import patch

from importers.replay_contact_importer import ReplayContactImporter
from pepys_import.file.file_processor import FileProcessor
from pepys_import.core.store.data_store import DataStore

FILE_PATH = os.path.dirname(__file__)
DATA_PATH1 = os.path.join(FILE_PATH, "sample_data/track_files/rep_data/rep_test1.rep")
DATA_PATH2 = os.path.join(
    FILE_PATH, "sample_data/track_files/rep_data/rep_test1_bad.rep"
)
DATA_PATH3 = os.path.join(
    FILE_PATH, "sample_data/track_files/rep_data/sen_frig_sensor.dsf"
)


class RepContactTests(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    @patch("shutil.move")
    @patch("os.chmod")
    def test_process_rep_contacts(self, patched_move, patched_chmod):
        processor = FileProcessor()
        processor.register_importer(ReplayContactImporter())

        # check states empty
        with self.store.session_scope():
            # there must be no states at the beginning
            contacts = self.store.session.query(self.store.db_classes.Contact).all()
            self.assertEqual(len(contacts), 0)

            # there must be no platforms at the beginning
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            self.assertEqual(len(platforms), 0)

            # there must be no datafiles at the beginning
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 0)

        # parse the folder
        processor.process(DATA_PATH1, self.store, False)

        # check data got created
        with self.store.session_scope():
            # there must be states after the import
            contacts = self.store.session.query(self.store.db_classes.Contact).all()
            self.assertEqual(len(contacts), 7)

            # check the data contents
            self.assertEqual(contacts[0].bearing, math.radians(252.85))
            self.assertEqual(contacts[1].bearing, math.radians(251.33))

            self.assertEqual(contacts[0].freq, 123.4)

            self.assertEqual(contacts[0].location, None)
            self.assertEqual(contacts[3].location, None)

            # todo, also test that the correct range is being stored

            # Check location point's type and value
            location1 = contacts[1].location
            point1 = self.store.session.query(func.ST_AsText(location1)).one()
            self.assertFalse(isinstance(location1, str))
            self.assertTrue(isinstance(location1, WKBElement))
            self.assertEqual(
                point1[0], "POINT(16.75 60.25)",
            )

            # Check location point's type and value
            location2 = contacts[4].location
            point2 = self.store.session.query(func.ST_AsText(location2)).one()
            self.assertFalse(isinstance(location2, str))
            self.assertTrue(isinstance(location2, WKBElement))
            self.assertEqual(
                point2[0], "POINT(30.75 16.25)",
            )

            # there must be platforms after the import
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            self.assertEqual(len(platforms), 2)

            # there must be one datafile afterwards
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 1)

    @patch("shutil.move")
    @patch("os.chmod")
    def test_process_dsf_contacts(self, patched_move, patched_chmod):
        processor = FileProcessor()
        processor.register_importer(ReplayContactImporter())

        # check states empty
        with self.store.session_scope():
            # there must be no states at the beginning
            contacts = self.store.session.query(self.store.db_classes.Contact).all()
            self.assertEqual(len(contacts), 0)

            # there must be no platforms at the beginning
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            self.assertEqual(len(platforms), 0)

            # there must be no datafiles at the beginning
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 0)

        # parse the folder
        processor.process(DATA_PATH3, self.store, False)

        # check data got created
        with self.store.session_scope():
            # there must be states after the import
            contacts = self.store.session.query(self.store.db_classes.Contact).all()
            self.assertEqual(len(contacts), 95)

            # check the data contents
            self.assertEqual(contacts[0].bearing, math.radians(80))
            self.assertEqual(contacts[1].bearing, math.radians(78))

            self.assertEqual(contacts[0].location, None)
            self.assertEqual(contacts[3].location, None)

            # there must be platforms after the import
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            self.assertEqual(len(platforms), 1)

            # there must be one datafile afterwards
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 1)


if __name__ == "__main__":
    unittest.main()
