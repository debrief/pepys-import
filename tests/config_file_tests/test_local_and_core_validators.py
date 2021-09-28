import os
import unittest
from unittest.mock import patch

from importers.e_trac_importer import ETracImporter
from importers.replay_importer import ReplayImporter
from pepys_import.core.store.common_db import reload_local_validators
from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor

DIRECTORY_PATH = os.path.dirname(__file__)
REP_DATA_PATH = os.path.join(
    os.path.dirname(DIRECTORY_PATH),
    "sample_data",
    "track_files",
    "rep_data",
    "rep_test1.rep",
)
OTHER_DATA_PATH = os.path.join(
    os.path.dirname(DIRECTORY_PATH),
    "sample_data",
    "track_files",
    "other_data",
    "e_trac.txt",
)
BASIC_PARSERS_PATH = os.path.join(DIRECTORY_PATH, "basic_tests")
ENHANCED_PARSERS_PATH = os.path.join(DIRECTORY_PATH, "enhanced_tests")

BASIC_PARSERS_FAILS_PATH = os.path.join(DIRECTORY_PATH, "basic_tests_fails")
ENHANCED_PARSERS_FAILS_PATH = os.path.join(DIRECTORY_PATH, "enhanced_tests_fails")


class TestLocalTests(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_local_basic_tests(self):
        with patch("config.LOCAL_BASIC_TESTS", BASIC_PARSERS_PATH):
            with patch("config.LOCAL_ENHANCED_TESTS", ENHANCED_PARSERS_PATH):
                reload_local_validators()

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

                processor = FileProcessor(archive=False)
                processor.register_importer(ETracImporter())

                # parse the folder
                processor.process(OTHER_DATA_PATH, self.store, False)

                # check data got created
                with self.store.session_scope():
                    # there must be states after the import
                    states = self.store.session.query(self.store.db_classes.State).all()
                    self.assertEqual(len(states), 44)

                    # there must be platforms after the import
                    platforms = self.store.session.query(self.store.db_classes.Platform).all()
                    self.assertEqual(len(platforms), 18)

                    # there must be one datafile afterwards
                    datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
                    self.assertEqual(len(datafiles), 1)

                    # Check that there is an elevation of 147 reported (test file was manually edited
                    # to contain an elevation of 147m)
                    results = (
                        self.store.session.query(self.store.db_classes.State)
                        .filter(self.store.db_classes.State.elevation == 147)
                        .all()
                    )
                    assert len(results) == 1

        reload_local_validators()

    def test_local_basic_and_enhanced_tests(self):
        with patch("config.LOCAL_BASIC_TESTS", BASIC_PARSERS_PATH):
            with patch("config.LOCAL_ENHANCED_TESTS", ENHANCED_PARSERS_PATH):
                reload_local_validators()

                processor = FileProcessor(archive=False)
                processor.register_importer(ReplayImporter())

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
                processor.process(REP_DATA_PATH, self.store, False)

                # check data got created
                with self.store.session_scope():
                    # there must be states after the import
                    states = self.store.session.query(self.store.db_classes.State).all()
                    self.assertEqual(len(states), 8)

                    # there must be platforms after the import
                    platforms = self.store.session.query(self.store.db_classes.Platform).all()
                    self.assertEqual(len(platforms), 2)

                    # there must be one datafile afterwards
                    datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
                    self.assertEqual(len(datafiles), 1)

        reload_local_validators()


class TestLocalTestsFails(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_local_basic_tests(self):
        with patch("config.LOCAL_BASIC_TESTS", BASIC_PARSERS_FAILS_PATH):
            with patch("config.LOCAL_ENHANCED_TESTS", ENHANCED_PARSERS_FAILS_PATH):
                reload_local_validators()

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

                processor = FileProcessor(archive=False)
                processor.register_importer(ETracImporter())

                # parse the folder
                processor.process(OTHER_DATA_PATH, self.store, False)

                # check data got created
                with self.store.session_scope():
                    # there must be no states after the import
                    states = self.store.session.query(self.store.db_classes.State).all()
                    self.assertEqual(len(states), 0)

                    # there must be platforms after the import
                    platforms = self.store.session.query(self.store.db_classes.Platform).all()
                    self.assertEqual(len(platforms), 18)

                    # there must be no datafiles afterwards - as all files gave errors
                    datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
                    self.assertEqual(len(datafiles), 0)

        reload_local_validators()

    def test_local_basic_and_enhanced_tests(self):
        with patch("config.LOCAL_BASIC_TESTS", BASIC_PARSERS_FAILS_PATH):
            with patch("config.LOCAL_ENHANCED_TESTS", ENHANCED_PARSERS_FAILS_PATH):
                reload_local_validators()

                processor = FileProcessor(archive=False)
                processor.register_importer(ReplayImporter())

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
                with patch("pepys_import.core.store.common_db.prompt", return_value="2"):
                    processor.process(REP_DATA_PATH, self.store, False)

                # check data got created
                with self.store.session_scope():
                    # there must be no states after the import
                    states = self.store.session.query(self.store.db_classes.State).all()
                    self.assertEqual(len(states), 0)

                    # there must be platforms after the import
                    platforms = self.store.session.query(self.store.db_classes.Platform).all()
                    self.assertEqual(len(platforms), 2)

                    # there must be no datafiles afterwards - as all files gave errors
                    datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
                    self.assertEqual(len(datafiles), 0)

        reload_local_validators()


if __name__ == "__main__":
    unittest.main()
