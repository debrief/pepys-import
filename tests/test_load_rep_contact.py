import os
import unittest

from importers.replay_contact_importer import ReplayContactImporter
from pepys_import.core.formats import unit_registry
from pepys_import.core.formats.location import Location
from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor

FILE_PATH = os.path.dirname(__file__)
DATA_PATH1 = os.path.join(FILE_PATH, "sample_data/track_files/rep_data/rep_test1.rep")
DATA_PATH2 = os.path.join(FILE_PATH, "sample_data/track_files/rep_data/rep_test1_bad.rep")
DATA_PATH3 = os.path.join(FILE_PATH, "sample_data/track_files/rep_data/sen_frig_sensor.dsf")


class RepContactTests(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_process_rep_contacts(self):
        processor = FileProcessor(archive=False)
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
            self.assertEqual(contacts[0].bearing, 252.85 * unit_registry.degree)

            # Has to be almost equal as we get a number very slightly different to 251.33
            # due to floating point precision issues
            self.assertAlmostEqual(contacts[1].bearing, 251.33 * unit_registry.degree)

            self.assertEqual(contacts[0].freq, 123.4 * unit_registry.hertz)

            self.assertEqual(contacts[0].location, None)
            self.assertEqual(contacts[3].location, None)

            self.assertAlmostEqual(contacts[0].range, 395.11224 * unit_registry.metre)

            # Check location point's type and value
            location1 = contacts[1].location
            correct_loc = Location()
            correct_loc.set_longitude_decimal_degrees(16.75)
            correct_loc.set_latitude_decimal_degrees(60.25)
            assert location1 == correct_loc

            # Check location point's type and value
            location2 = contacts[4].location
            correct_loc = Location()
            correct_loc.set_longitude_decimal_degrees(30.75)
            correct_loc.set_latitude_decimal_degrees(16.25)
            assert location2 == correct_loc

            # there must be platforms after the import
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            self.assertEqual(len(platforms), 2)

            # there must be one datafile afterwards
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 1)

    def test_process_dsf_contacts(self):
        processor = FileProcessor(archive=False)
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
            self.assertEqual(contacts[0].bearing, 80 * unit_registry.degree)
            self.assertEqual(contacts[1].bearing, 78 * unit_registry.degree)

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
