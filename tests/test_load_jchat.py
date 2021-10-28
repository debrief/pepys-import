import os
import unicodedata
import unittest

from importers.jchat_importer import JChatImporter
from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor

FILE_PATH = os.path.dirname(__file__)
NO_EXT_PATH = os.path.join(FILE_PATH, "sample_data/jchat_files/jchat_no_ext")
BREAKS_PATH = os.path.join(FILE_PATH, "sample_data/jchat_files/jchat_breaks_in_message.html")
DATA_PATH = os.path.join(FILE_PATH, "sample_data/jchat_files/jchat_sample.html")
UNUSUAL_CHARS_PATH = os.path.join(FILE_PATH, "sample_data/jchat_files/jchat_unusual_chars.html")
MARKER_MESSAGES_PATH = os.path.join(FILE_PATH, "sample_data/jchat_files/marker_messages.html")
ROOM_MESSAGES_PATH = os.path.join(FILE_PATH, "sample_data/jchat_files/connect_disconnect.html")
NO_HTML_EXT_DOT_IN_NAME_PATH = os.path.join(FILE_PATH, "sample_data/jchat_files/ABC_123.01_XYZ")


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
                .order_by(self.store.db_classes.Comment.time)
                .all()
            )
            assert results[0].content == "COMMS TEST"

    def test_breaks_in_message(self):
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
        processor.process(BREAKS_PATH, self.store, False)

        # check data got created
        with self.store.session_scope():
            # there must be states after the import
            comments = self.store.session.query(self.store.db_classes.Comment).all()
            assert len(comments) == 3

            # there must be platforms after the import
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            assert len(platforms) == 2

            # there must be one datafile afterwards
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            assert len(datafiles) == 1

            results = (
                self.store.session.query(self.store.db_classes.Comment)
                .order_by(self.store.db_classes.Comment.time)
                .all()
            )
            assert results[0].content == "COMMS TEST"
            assert results[1].content == "Replay bravo"
            assert results[2].content == "Replay multiple bravos in same tag"

    def test_existing_quad_with_new_quads(self):
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
        processor.process(DATA_PATH, self.store, False)

        # check data got created
        with self.store.session_scope():
            # there must be states after the import
            comments = self.store.session.query(self.store.db_classes.Comment).all()
            assert len(comments) == 5

            # there must be platforms after the import
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            assert len(platforms) == 3

            # there must be one datafile afterwards
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            assert len(datafiles) == 1

            results = (
                self.store.session.query(self.store.db_classes.Comment)
                .order_by(self.store.db_classes.Comment.time)
                .all()
            )
            assert results[0].content == "COMMS TEST"
            assert results[1].content == "Replay bravo"
            assert results[2].content == "Replay bravo"
            assert results[3].content == "Replay bravo - next day"
            assert results[4].content == "Replay bravo - next month"

    def test_html_character_representation(self):
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
        processor.process(UNUSUAL_CHARS_PATH, self.store, False)

        # check data got created
        with self.store.session_scope():
            # there must be states after the import
            comments = self.store.session.query(self.store.db_classes.Comment).all()
            assert len(comments) == 3

            # there must be platforms after the import
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            assert len(platforms) == 3

            # there must be one datafile afterwards
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            assert len(datafiles) == 1

            results = (
                self.store.session.query(self.store.db_classes.Comment)
                .order_by(self.store.db_classes.Comment.time)
                .all()
            )
            assert unicodedata.normalize("NFKC", results[0].content) == "COMMS  ’TEST"
            assert unicodedata.normalize("NFKC", results[1].content) == "Replay&‘ ...bravo"
            assert unicodedata.normalize("NFKC", results[2].content) == "Replay–bravo"

    def test_room_connections_disconnections_ignored(self):
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
        processor.process(ROOM_MESSAGES_PATH, self.store, False)

        # check data got created
        with self.store.session_scope():
            # there must be states after the import
            comments = self.store.session.query(self.store.db_classes.Comment).all()
            assert len(comments) == 2

            # there must be platforms after the import
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            assert len(platforms) == 1

            # there must be one datafile afterwards
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            assert len(datafiles) == 1

            results = (
                self.store.session.query(self.store.db_classes.Comment)
                .order_by(self.store.db_classes.Comment.time)
                .all()
            )
            assert results[0].content == "COMMS TEST"
            assert results[1].content == "Replay bravo"

    def test_marker_messages_ignored(self):
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
        processor.process(MARKER_MESSAGES_PATH, self.store, False)

        # check data got created
        with self.store.session_scope():
            # there must be states after the import
            comments = self.store.session.query(self.store.db_classes.Comment).all()
            assert len(comments) == 2

            # there must be platforms after the import
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            assert len(platforms) == 1

            # there must be one datafile afterwards
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            assert len(datafiles) == 1

            results = (
                self.store.session.query(self.store.db_classes.Comment)
                .order_by(self.store.db_classes.Comment.time)
                .all()
            )
            assert len(results) == 2
            assert results[0].content == "COMMS TEST"
            assert results[1].content == "Replay bravo"

    def test_filename_with_dot_in_name_no_html_ext(self):
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
        processor.process(NO_HTML_EXT_DOT_IN_NAME_PATH, self.store, False)

        # check data got created
        with self.store.session_scope():
            # there must be states after the import
            comments = self.store.session.query(self.store.db_classes.Comment).all()
            assert len(comments) == 3

            # there must be platforms after the import
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            assert len(platforms) == 2

            # there must be one datafile afterwards
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            assert len(datafiles) == 1

            results = (
                self.store.session.query(self.store.db_classes.Comment)
                .order_by(self.store.db_classes.Comment.time)
                .all()
            )
            assert results[0].content == "COMMS TEST"
            assert results[1].content == "Replay bravo"
            assert results[2].content == "Replay bravo"

    # Tests to include:
    # Various time wranging - e.g. month/year roll-over
    # HTML suffix
    # Missing data
    # Test Pepys is loading same platform rather than creating multiple of the same one
