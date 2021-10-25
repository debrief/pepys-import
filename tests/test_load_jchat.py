import os
import unittest

from importers.jchat_importer import JChatImporter
from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor

FILE_PATH = os.path.dirname(__file__)
NO_EXT_PATH = os.path.join(FILE_PATH, "sample_data/jchat_files/jchat_no_ext")
DATA_PATH = os.path.join(FILE_PATH, "sample_data/jchat_files/jchat_sample.html")


class JChatTests(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    def test_no_file_suffix(self):
        processor = FileProcessor(archive=False)
        processor.register_importer(JChatImporter())
        # check states empty
        with self.store.session_scope():
            # there must be no states at the beginning
            comments = self.store.session.query(self.store.db_classes.Comment).all()
            assert len(comments) == 0

            # there must be no platforms at the beginning
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            assert len(platforms) == 0

            # there must be no datafiles at the beginning
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            assert len(datafiles) == 0

        # parse the data
        processor.process(NO_EXT_PATH, self.store, False)

        # check data got created
        with self.store.session_scope():
            # there must be states after the import
            comments = self.store.session.query(self.store.db_classes.Comment).all()
            assert len(comments) == 5

            # there must be platforms after the import
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            assert len(platforms) == 2

            # there must be one datafile afterwards
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            assert len(datafiles) == 1

            results = (
                self.store.session.query(self.store.db_classes.Comment)
                .order_by(self.store.db_classes.State.time)
                .all()
            )
            print(results)
        # assert True == False

    # Tests to include:
    # Quad exists
    # Quad doesn't exist
    # Various time wranging - e.g. month/year roll-over
    # HTML suffix
    # Messages with breaks in them
    # Missing data
    # No suffix
