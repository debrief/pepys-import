import os
import unicodedata
import unittest
from datetime import datetime

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
YEAR_MONTH_ROLLOVER_PATH = os.path.join(
    FILE_PATH, "jchat_importer_date_sensitive_files/year_month_rollover.html"
)
MODERN_FORMAT_PATH = os.path.join(FILE_PATH, "sample_data/jchat_files/jchat_modern_format.html")
LEGACY_NO_I_PATH = os.path.join(FILE_PATH, "sample_data/jchat_files/legacy_no_i.html")
COMBINED_FILE_PATH = os.path.join(FILE_PATH, "sample_data/jchat_files/combined_format.html")


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
            assert unicodedata.normalize("NFKC", results[2].content) == "Replay–bravo"

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

    def test_modern_jchat_format(self):
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
        processor.process(MODERN_FORMAT_PATH, self.store, False)

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
            assert len(results) == 3
            assert results[0].content == "COMMS TEST"
            assert results[1].content == "Replay bravo - no i tag and breaks"
            assert results[2].content == "Replay bravo - no i tag"

    def test_legacy_jchat_format_without_i_tag(self):
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
        processor.process(LEGACY_NO_I_PATH, self.store, False)

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
            assert results[1].content == "COMMS TEST - no i"

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

    def test_year_month_rollover(self):
        processor = FileProcessor(archive=False)
        importer = JChatImporter()
        processor.register_importer(importer)
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

        # Fixed Year/month to avoid flaky tests
        importer.year = 2020
        importer.month = 10

        # parse the data
        processor.process(YEAR_MONTH_ROLLOVER_PATH, self.store, False)

        # check data got created
        with self.store.session_scope():
            # there must be states after the import
            comments = self.store.session.query(self.store.db_classes.Comment).all()
            assert len(comments) == 6

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
            assert results[0].time == datetime(2020, 10, 31, 8, 27, 44)
            assert results[1].time == datetime(2020, 11, 1, 8, 29, 44)
            assert results[2].time == datetime(2020, 11, 30, 9, 14, 44)
            assert results[3].time == datetime(2020, 12, 1, 10, 28, 54)
            assert results[4].time == datetime(2020, 12, 31, 1, 8, 9)
            assert results[5].time == datetime(2021, 1, 1, 2, 8, 9)

    def test_combined_format(self):
        """Testing a file with elements of both styles to help develop a more generic approach"""
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
        processor.process(COMBINED_FILE_PATH, self.store, False)

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
            assert len(results) == 5
            assert results[0].content == "Modern - has i tag"
            assert results[1].content == "Modern - no i tag but has multiple breaks"
            assert results[2].content == "Modern - no i tag - no breaks"
            assert results[3].content == "Legacy - font a swap - no i tag - no breaks"
            assert results[4].content == "Legacy - font a swap - has i tag - no breaks"

    @staticmethod
    def test_simplify_html_no_html():
        simple_string = "A simple string with no tags"
        result = JChatImporter.simplify_jchat_html(simple_string)
        assert result == simple_string

    @staticmethod
    def test_simplify_html_no_banned_tags():
        html_string = "<html><head>Test</head><body>A simple string with no tags</body></html>"
        result = JChatImporter.simplify_jchat_html(html_string)
        assert result == html_string

    @staticmethod
    def test_simplify_html_banned_tags():
        html_string = """
        <html>
            <head> Header </head>
            <body>
                <div id="34544=34534">
                    <tt><font>[22092744A]</font></tt>
                    <b><a href=""><font>DAUN_AS</font></a></b>
                    <span class="msgcontent"><font><i>COMMS<br>TEST</i></font></span>
                </div>
            <body>
        <html>"""

        expected = """
        <html>
            <head> Header </head>
            <body>
                <div id="34544=34534">
                    <tt><font>[22092744A]</font></tt>
                    <b><a href=""><font>DAUN_AS</font></a></b>
                    <font>COMMS TEST</font>
                </div>
            <body>
        <html>"""

        result = JChatImporter.simplify_jchat_html(html_string)
        assert result == expected
