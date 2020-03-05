import os
import unittest
import shutil

from pepys_import.file.e_trac_importer import ETracImporter
from pepys_import.file.file_processor import FileProcessor
from pepys_import.core.store.data_store import DataStore

FILE_PATH = os.path.dirname(__file__)
DATA_PATH = os.path.join(FILE_PATH, "sample_data/track_files/other_data")
OUTPUT_PATH = os.path.join(DATA_PATH, "output")


class ETracTests(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

        # add paths of the current files to a list
        self.before_file_paths = list()
        for current_path, folders, files in os.walk(DATA_PATH):
            for file in files:
                self.before_file_paths.append(os.path.join(current_path, file))

    def tearDown(self):
        # find parsed and moved files
        output_file_paths = list()
        for current_path, folders, files in os.walk(OUTPUT_PATH):
            for file in files:
                output_file_paths.append(os.path.join(current_path, file))

        after_file_paths = list()
        for current_path, folders, files in os.walk(DATA_PATH):
            for file in files:
                after_file_paths.append(os.path.join(current_path, file))

        for path in self.before_file_paths:
            # if file is moved, it is not in after_file_paths
            if path not in after_file_paths:
                abs_path, file = os.path.split(path)
                source = os.path.join(OUTPUT_PATH, file)
                shutil.move(source, path)

        shutil.rmtree(OUTPUT_PATH)

    def test_process_e_trac_data(self):
        processor = FileProcessor()
        processor.register_importer(ETracImporter())

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
        processor.process(DATA_PATH, self.store, False)

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
            self.assertEqual(len(datafiles), 2)


if __name__ == "__main__":
    unittest.main()
