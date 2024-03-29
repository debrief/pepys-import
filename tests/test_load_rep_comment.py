import datetime
import os
import unittest

from importers.replay_comment_importer import ReplayCommentImporter
from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor

FILE_PATH = os.path.dirname(__file__)
DATA_PATH1 = os.path.join(FILE_PATH, "sample_data/track_files/rep_data/rep_test1.rep")
DATA_PATH2 = os.path.join(FILE_PATH, "sample_data/track_files/rep_data/rep_test1_bad.rep")


class RepCommentTests(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_process_rep_comments(self):
        processor = FileProcessor(archive=False)
        processor.register_importer(ReplayCommentImporter())

        # check states empty
        with self.store.session_scope():
            # there must be no states at the beginning
            comments = self.store.session.query(self.store.db_classes.Comment).all()
            self.assertEqual(len(comments), 0)

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
            comments = self.store.session.query(self.store.db_classes.Comment).all()
            self.assertEqual(len(comments), 7)
            # check the first two rows have matching comment types (NULL)
            assert comments[0].comment_type_id == comments[1].comment_type_id
            # and the last row has a different comment type
            assert comments[6].comment_type_id != comments[0].comment_type_id
            # and the full comments on some other rows
            self.assertEqual(comments[0].content, "Contact detected on TA")
            self.assertEqual(comments[6].content, "SUBJECT lost on TA")
            # check the source is equal for the first two rows
            assert comments[0].platform_id == comments[1].platform_id
            # and the last row is different
            assert comments[6].platform_id != comments[0].platform_id

            # Check the timestamp for the first entry
            assert comments[0].time == datetime.datetime(2010, 1, 12, 11, 58, 0)

            # there must be platforms after the import
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            self.assertEqual(len(platforms), 2)

            # there must be one datafile afterwards
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 1)

    def test_process_rep_comment_errors(self):
        processor = FileProcessor(archive=False)
        processor.register_importer(ReplayCommentImporter())

        # check states empty
        with self.store.session_scope():
            # there must be no states at the beginning
            comments = self.store.session.query(self.store.db_classes.Comment).all()
            self.assertEqual(len(comments), 0)

            # there must be no platforms at the beginning
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            self.assertEqual(len(platforms), 0)

            # there must be no datafiles at the beginning
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 0)

        # parse the folder
        processor.process(DATA_PATH2, self.store, False)

        # check data got created
        with self.store.session_scope():
            # there must be no states after the import
            comments = self.store.session.query(self.store.db_classes.Comment).all()
            self.assertEqual(len(comments), 0)

            # there must be platforms after the import
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            self.assertEqual(len(platforms), 2)

            # there must be no datafiles afterwards - because the file was invalid
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 0)


if __name__ == "__main__":
    unittest.main()
