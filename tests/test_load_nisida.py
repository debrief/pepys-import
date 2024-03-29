import datetime
import os
import unittest

from importers.nisida_importer import NisidaImporter
from pepys_import.core.formats import unit_registry
from pepys_import.core.formats.location import Location
from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor
from tests.utils import check_errors_for_file_contents

FILE_PATH = os.path.dirname(__file__)
DATA_PATH = os.path.join(FILE_PATH, "sample_data/track_files/nisida/nisida_example.txt")


class TestLoadNisida(unittest.TestCase):
    def test_process_nisida_data_full_check(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

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
            # there must be 5 states after the import
            states = self.store.session.query(self.store.db_classes.State).all()
            self.assertEqual(len(states), 5)

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
            assert states[0].time == datetime.datetime(2003, 10, 31, 10, 2)

            # Check depth
            assert states[2].elevation == -100 * unit_registry.metre

            # Check lat and lon are parsed correctly for a Detection message
            assert round(states[3].location.longitude, 2) == 4.20
            assert round(states[3].location.latitude, 2) == 36.03

            # Check sensor name used for Detection message
            assert states[3].sensor_name == "GPS"

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

    def test_process_nisida_data_invalid(self):
        nisida_importer = NisidaImporter()

        check_errors_for_file_contents(
            "UNIT/OCT03/SRF", "Not enough tokens in UNIT/ line", nisida_importer
        )
        check_errors_for_file_contents(
            "UNIT//OCT03/SRF", "Missing platform name in UNIT/ line", nisida_importer
        )
        check_errors_for_file_contents(
            "UNIT/PLAT/BLH03/SRF", "Invalid month/year in UNIT/ line", nisida_importer
        )
        check_errors_for_file_contents(
            "UNIT/PLAT/MARBB/SRF", "Invalid month/year in UNIT/ line", nisida_importer
        )
        # Invalid date in UNIT header, plus another line that would depend on that
        check_errors_for_file_contents(
            "UNIT/PLAT/MARBB/SRF\n311002Z/3623.00N/00412.02E/GPS/359/03/-/",
            "Invalid month/year in UNIT/ line",
            nisida_importer,
        )

        header = "UNIT/ADRI/OCT03/SRF/\n"

        check_errors_for_file_contents(
            header + "311056Z/BLA/TEXT FOR NARRATIVE PURPOSES",
            "Line does not match any known message format",
            nisida_importer,
        )

        # Invalid lat/lon for Position message
        check_errors_for_file_contents(
            header + "311002Z/AB/CD/GPS/359/03/-/",
            "Unable to parse latitude/longitude values",
            nisida_importer,
        )
        check_errors_for_file_contents(
            header + "311002Z/99999.99/99999.99/GPS/359/03/-/",
            "Error in latitude degrees value 99.0. Must be between -90 and 90",
            nisida_importer,
        )

        # Invalid timestamps for day, hour and minute
        check_errors_for_file_contents(
            header + "451000Z/COC/TEXT FOR CO COMMENTS/", "Invalid timestamp", nisida_importer
        )
        check_errors_for_file_contents(
            header + "255500Z/COC/TEXT FOR CO COMMENTS/", "Invalid timestamp", nisida_importer
        )
        check_errors_for_file_contents(
            header + "251178Z/COC/TEXT FOR CO COMMENTS/", "Invalid timestamp", nisida_importer
        )

        # No Z at the end of timestamp
        check_errors_for_file_contents(
            header + "251125A/COC/TEXT FOR CO COMMENTS/",
            "Invalid format for timestamp - missing Z character",
            nisida_importer,
        )

        # Both time up and time down missing
        check_errors_for_file_contents(
            header + "311002Z/SEN/TAS/-/-/TIME ON EXAMPLE/",
            "You must provide at least one of time on or time off",
            nisida_importer,
        )

        # Both time up and time down missing
        check_errors_for_file_contents(
            header + "312130Z/EXP/PER//-/FULLY CHARGED AND READY",
            "You must provide at least one of time up or time down",
            nisida_importer,
        )

        # Invalid time up
        check_errors_for_file_contents(
            header + "312130Z/EXP/PER/55:92/-/FULLY CHARGED AND READY",
            "Invalid time value",
            nisida_importer,
        )
        check_errors_for_file_contents(
            header + "312130Z/EXP/PER/AA:15/-/FULLY CHARGED AND READY",
            "Unable to parse time value to float",
            nisida_importer,
        )
        check_errors_for_file_contents(
            header + "312130Z/EXP/PER/10:BB/-/FULLY CHARGED AND READY",
            "Unable to parse time value to float",
            nisida_importer,
        )
        check_errors_for_file_contents(
            header + "312130Z/EXP/PER/1015/-/FULLY CHARGED AND READY",
            "Unable to parse time value to float",
            nisida_importer,
        )

        # Invalid time down
        check_errors_for_file_contents(
            header + "312130Z/EXP/PER/-/10:BB/FULLY CHARGED AND READY",
            "Unable to parse time value to float",
            nisida_importer,
        )

        # Invalid time on/off for SENSOR
        check_errors_for_file_contents(
            header + "311300Z/SEN/TAS/13:00/CC:50/SENSOR ON AND OFF/",
            "Unable to parse time value to float",
            nisida_importer,
        )
        check_errors_for_file_contents(
            header + "311300Z/SEN/TAS/13:CC/15:50/SENSOR ON AND OFF/",
            "Unable to parse time value to float",
            nisida_importer,
        )

        # Invalid location for ATTACK message
        check_errors_for_file_contents(
            header + "311206Z/ATT/OTHER/63/12/775/99923.23N/00500.25E/GPS/TEXT FOR ATTAC",
            "Error in latitude degrees value 999.0. Must be between -90 and 90",
            nisida_importer,
        )

        # Invalid line continuation
        check_errors_for_file_contents(
            header + "311002Z/3623.00N/00412.02E/GPS/359/03/-/\n//CONTINUATION",
            "Line continuation not immediately after valid line",
            nisida_importer,
        )

        # Invalid Sensor Code
        check_errors_for_file_contents(
            header + "311200Z/DET/BLAH/23/20/777/3602.02N/00412.12E/GPS/DETECTION RECORD",
            "Invalid sensor code: BLAH",
            nisida_importer,
        )
        check_errors_for_file_contents(
            header + "311002Z/SEN/BLAH/10:02/-/TIME ON EXAMPLE/",
            "Invalid sensor code: BLAH",
            nisida_importer,
        )

        # Invalid position source for DETECTION
        check_errors_for_file_contents(
            header + "311200Z/DET/RDR/23/20/777/3602.02N/00412.12E/BLA/DETECTION RECORD",
            "Invalid position source value",
            nisida_importer,
        )

        # Invalid lat lon for Detection
        check_errors_for_file_contents(
            header + "311200Z/DET/RDR/23/20/777/3602.02Q/00412.12E/GPS/DETECTION RECORD",
            "Error in latitude hemisphere value Q. Must be N or S",
            nisida_importer,
        )
        check_errors_for_file_contents(
            header + "311200Z/DET/RDR/23/20/777/9902.02N/00412.12E/GPS/DETECTION RECORD",
            "Error in latitude degrees value 99.0. Must be between -90 and 90",
            nisida_importer,
        )
        check_errors_for_file_contents(
            header + "311200Z/DET/RDR/23/20/777/3502.02N/592412.12E/GPS/DETECTION RECORD",
            "Error in longitude degrees value 5924.0. Must be between -180 and 180",
            nisida_importer,
        )
        check_errors_for_file_contents(
            header + "311200Z/DET/RDR/23/20/777/3502.02N/005412.12N/GPS/DETECTION RECORD",
            "Error in longitude hemisphere value N. Must be E or W",
            nisida_importer,
        )

        # Not enough info for geometry calculation for ATTACK
        check_errors_for_file_contents(
            header + "311206Z/ATT/OTHER//12/775/3623.23N/00500.25E/GPS/TEXT",
            "Not enough data to calculate attack position - bearing, range or own location missing",
            nisida_importer,
        )

        # Not enough info for geometry calculation for DETECTION
        check_errors_for_file_contents(
            header + "311200Z/DET/RDR/23/-/777/3602.02N/00412.12E/GPS/DETECTION RECORD",
            "Not enough data to calculate attack position - bearing, range or own location missing",
            nisida_importer,
        )

        # Invalid position source for ATTACK
        check_errors_for_file_contents(
            header + "311206Z/ATT/OTHER/63/12/775/3623.23N/00500.25E/BLA/TEXT FOR ATTACK",
            "Invalid position source value",
            nisida_importer,
        )

        # Invalid location for DIP

        check_errors_for_file_contents(
            header + "311305Z/DIP/5/23/14:00/3502.02Q/00502.06E/ASW DIP EXAMPLE/",
            "Error in latitude hemisphere value Q. Must be N or S",
            nisida_importer,
        )

    def test_process_nisida_data_valid(self):
        nisida_importer = NisidaImporter()

        # UNIT line with POS at the end
        check_errors_for_file_contents("UNIT/PLAT/OCT03/SRF/POS", None, nisida_importer)

        # UNIT line with POS at the end and other lines after
        check_errors_for_file_contents(
            "UNIT/PLAT/OCT03/SRF/POS\n101000Z/COC/TEXT FOR CO COMMENTS/", None, nisida_importer
        )


if __name__ == "__main__":
    unittest.main()
