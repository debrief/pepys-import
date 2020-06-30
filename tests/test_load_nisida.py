import datetime
import os
import unittest

from geoalchemy2.shape import to_shape

from importers.nisida_importer import NisidaImporter
from pepys_import.core.formats import unit_registry
from pepys_import.core.formats.location import Location
from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor

FILE_PATH = os.path.dirname(__file__)
DATA_PATH = os.path.join(FILE_PATH, "sample_data/track_files/nisida/nisida_example.txt")


class TestLoadNisida(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_process_nisida_data(self):
        processor = FileProcessor(archive=False)
        processor.register_importer(NisidaImporter())

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
        processor.process(DATA_PATH, self.store, False)

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

            # There must be 4 geometries
            geoms = self.store.session.query(self.store.db_classes.Geometry1).all()
            assert len(geoms) == 4

            # There must be 6 comments
            comments = self.store.session.query(self.store.db_classes.Comment).all()
            assert len(comments) == 6

            # There must be 1 contact entries
            contacts = self.store.session.query(self.store.db_classes.Contact).all()
            assert len(contacts) == 1

            # There must be 5 activation entries
            activations = self.store.session.query(self.store.db_classes.Activation).all()
            assert len(activations) == 5

            # Check states

            # Check lat and lon are parsed correctly for a Position message
            assert round(states[0].location.longitude, 2) == 4.20
            assert round(states[0].location.latitude, 2) == 36.38

            # Check sensor name used for Position message
            assert states[0].sensor_name == "GPS"

            # Check a State's time
            states[0].time == datetime.datetime(2003, 10, 31, 10, 2)

            # Check lat and lon are parsed correctly for a Detection message
            assert round(states[2].location.longitude, 2) == 4.20
            assert round(states[2].location.latitude, 2) == 36.03

            # Check sensor name used for Detection message
            assert states[2].sensor_name == "GPS"

            # Check there is a comment with a long bit of text
            results = (
                self.store.session.query(self.store.db_classes.Comment)
                .filter(
                    self.store.db_classes.Comment.content
                    == "TEXT FOR NARRATIVE PURPOSES CONTINUING HERE AND HERE AND FINISHING HERE"
                )
                .all()
            )
            assert len(results) == 1
            assert results[0].comment_type_name == "Narrative"

            # Check there is a comment with specific text
            results = (
                self.store.session.query(self.store.db_classes.Comment)
                .filter(self.store.db_classes.Comment.content == "TEXT FOR CO COMMENTS")
                .all()
            )
            assert len(results) == 1
            assert results[0].comment_type_name == "CO Comments"

            # Check there is a comment with a whole ATTACK message
            results = (
                self.store.session.query(self.store.db_classes.Comment)
                .filter(
                    self.store.db_classes.Comment.content
                    == "ATT/OTHER/63/12/775/3623.23N/00500.25E/GPS/TEXT FOR ATTACK"
                )
                .all()
            )
            assert len(results) == 1
            assert results[0].comment_type_name == "Attack"

            # Check there is a comment with a whole ENV message
            results = (
                self.store.session.query(self.store.db_classes.Comment)
                .filter(
                    self.store.db_classes.Comment.content
                    == "ENV/12/12/5/5/3/12/12/22/ENVIRONMENTTEXT"
                )
                .all()
            )
            assert len(results) == 1
            assert results[0].comment_type_name == "Environment"

            # Check the geometry entries

            # Check one calculated from loc + bearing/range
            loc = Location.from_geometry(geoms[0].geometry)
            assert round(loc.latitude, 3) == 36.341
            assert round(loc.longitude, 3) == 4.363

            assert geoms[0].geo_type_name == "Tactical"
            assert geoms[0].geo_sub_type_name == "Detection"

            # Check one coming just from the data in the file
            loc = Location.from_geometry(geoms[2].geometry)
            assert round(loc.latitude, 3) == 35.034
            assert round(loc.longitude, 3) == 5.034

            assert geoms[2].geo_type_name == "Tactical"
            assert geoms[2].geo_sub_type_name == "Dip"

            # Check the Contact entries
            assert contacts[0].remarks == "DETECTION RECORD EXAMPLE TEXT"
            assert contacts[0].bearing == 23 * unit_registry.degree
            assert contacts[0].track_number == "777"

            # Check the activation entries
            assert activations[0].sensor_name == "Array Sonar"
            assert activations[0].start == datetime.datetime(2003, 10, 31, 10, 2)
            assert activations[0].end is None
            assert activations[0].remarks == "TIME ON EXAMPLE"

            assert activations[1].start == datetime.datetime(2003, 10, 31, 13, 0)
            assert activations[1].end == datetime.datetime(2003, 10, 31, 14, 50)

            assert activations[2].start is None
            assert activations[2].end == datetime.datetime(2003, 10, 31, 15, 0)

            assert activations[3].sensor_name == "PER"
            assert activations[3].remarks == "FULLY CHARGED AND READY TO KILL"


if __name__ == "__main__":
    unittest.main()
