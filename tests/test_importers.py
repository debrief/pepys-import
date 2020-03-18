import os
import stat
import shutil
import unittest

from contextlib import redirect_stdout
from io import StringIO
from datetime import datetime
from unittest.mock import patch

from pepys_import.file.importer import Importer
from pepys_import.file.file_processor import FileProcessor
from importers.replay_importer import ReplayImporter
from importers.nmea_importer import NMEAImporter

FILE_PATH = os.path.dirname(__file__)
CURRENT_DIR = os.getcwd()
BAD_DATA_PATH = os.path.join(FILE_PATH, "sample_data_bad")
DATA_PATH = os.path.join(FILE_PATH, "sample_data")
OUTPUT_PATH = os.path.join(DATA_PATH, "output")
REP_DATA_PATH = os.path.join(DATA_PATH, "track_files", "rep_data")


class SampleImporterTests(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def tearDown(self) -> None:
        single_level_file = os.path.join(CURRENT_DIR, "single_level.db")
        if os.path.exists(single_level_file):
            os.remove(single_level_file)

        descending_file = os.path.join(CURRENT_DIR, "descending.db")
        if os.path.exists(descending_file):
            os.remove(descending_file)

    def test_process_folders_not_descending(self):
        """Test whether single level processing works for the given path"""
        processor = FileProcessor("single_level.db", archive=False)

        processor.load_importers_dynamically()

        # try bad file
        exception = False
        try:
            processor.process(BAD_DATA_PATH, None, False)
        except FileNotFoundError:
            exception = True
        self.assertTrue(exception)

        # now good one
        processor.process(DATA_PATH, None, False)

    def test_process_folders_descending(self):
        """Test whether descending processing works for the given path"""
        processor = FileProcessor("descending.db", archive=False)

        processor.load_importers_dynamically()

        # try bad file
        exception = False
        try:
            processor.process(BAD_DATA_PATH, None, True)
        except FileNotFoundError:
            exception = True
        self.assertTrue(exception)

        # now good one
        processor.process(DATA_PATH, None, True)

    def test_process_folders_descending_in_memory(self):
        """Test whether :memory: is used when no filename is given"""
        processor = FileProcessor(archive=False)

        processor.load_importers_dynamically()

        # try bad file
        exception = False
        try:
            processor.process(BAD_DATA_PATH, None, True)
        except FileNotFoundError:
            exception = True
        self.assertTrue(exception)

        # now good one
        processor.process(DATA_PATH, None, True)

    def test_class_name(self):
        """Test whether class names are correct"""
        replay_importer = ReplayImporter()
        self.assertEqual(str(replay_importer), "Replay File Format Importer")
        nmea_importer = NMEAImporter()
        self.assertEqual(str(nmea_importer), "NMEA File Format Importer")

    def test_giving_file_path_only(self):
        """Test whether process method works when a file path is given"""
        processor = FileProcessor(archive=False)

        processor.load_importers_dynamically()

        file_path = os.path.join(DATA_PATH, "test_importers.csv")

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            processor.process(file_path, None, False)
        output = temp_output.getvalue()

        self.assertIn("Files got processed: 0 times", output)

    @patch("pepys_import.file.file_processor.ARCHIVE_PATH", OUTPUT_PATH)
    def test_archiving_files(self):
        """Test whether archive flag correctly works for File Processor"""
        names = list()
        processor = FileProcessor(archive=True)
        processor.register_importer(ReplayImporter())
        processor.process(REP_DATA_PATH, None, False)

        moved_files_path = os.path.join(OUTPUT_PATH, "input_files")
        assert os.path.exists(moved_files_path) is True

        # Scan the files in input_files folder
        for file in os.scandir(moved_files_path):
            # Append the name of the file to test it later on
            names.append(file.name)
            # Move files back
            source_path = os.path.join(REP_DATA_PATH, file.name)
            shutil.move(file.path, source_path)
            # Change file permission to -rw-r--r--
            os.chmod(
                source_path, stat.S_IWRITE | stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH
            )

        # Assert that only correctly imported files were moved to the output folder
        assert "rep_test1.rep" in names
        assert "sen_ssk_freq.dsf" in names
        assert "sen_tracks.rep" in names
        assert "uk_track.rep" in names


class ImporterRemoveTestCase(unittest.TestCase):
    def test_can_load_this_header(self):
        """Test whether can_load_this_header removes the importer from the importers"""

        class TestImporter(Importer):
            def can_load_this_header(self, header) -> bool:
                return False

            def can_load_this_filename(self, filename):
                return True

            def can_load_this_type(self, suffix):
                return True

            def can_load_this_file(self, file_contents):
                return True

            def _load_this_file(self, data_store, path, file_contents, data_file):
                pass

        processor = FileProcessor()

        processor.register_importer(TestImporter("", "", ""))
        self.assertEqual(len(processor.importers), 1)
        self.assertEqual(type(processor.importers[0]), TestImporter)

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            processor.process(DATA_PATH, None, False)
        output = temp_output.getvalue()

        self.assertIn("Files got processed: 0 times", output)

    def test_can_load_this_filename(self):
        """Test whether can_load_this_filename removes the importer from the importers"""

        class TestImporter(Importer):
            def can_load_this_header(self, header) -> bool:
                return True

            def can_load_this_filename(self, filename):
                return False

            def can_load_this_type(self, suffix):
                return True

            def can_load_this_file(self, file_contents):
                return True

            def _load_this_file(self, data_store, path, file_contents, data_file):
                pass

        processor = FileProcessor()

        processor.register_importer(TestImporter("", "", ""))
        self.assertEqual(len(processor.importers), 1)
        self.assertEqual(type(processor.importers[0]), TestImporter)

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            processor.process(DATA_PATH, None, False)
        output = temp_output.getvalue()

        self.assertIn("Files got processed: 0 times", output)

    def test_can_load_this_type(self):
        """Test whether can_load_this_type removes the importer from the importers"""

        class TestImporter(Importer):
            def can_load_this_header(self, header) -> bool:
                return True

            def can_load_this_filename(self, filename):
                return True

            def can_load_this_type(self, suffix):
                return False

            def can_load_this_file(self, file_contents):
                return True

            def _load_this_file(self, data_store, path, file_contents, data_file):
                pass

        processor = FileProcessor()

        processor.register_importer(TestImporter("", "", ""))
        self.assertEqual(len(processor.importers), 1)
        self.assertEqual(type(processor.importers[0]), TestImporter)

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            processor.process(DATA_PATH, None, False)
        output = temp_output.getvalue()

        self.assertIn("Files got processed: 0 times", output)

    def test_can_load_this_file(self):
        """Test whether can_load_this_file removes the importer from the importers"""

        class TestImporter(Importer):
            def can_load_this_header(self, header) -> bool:
                return True

            def can_load_this_filename(self, filename):
                return True

            def can_load_this_type(self, suffix):
                return True

            def can_load_this_file(self, file_contents):
                return False

            def _load_this_file(self, data_store, path, file_contents, data_file):
                pass

        processor = FileProcessor()

        processor.register_importer(TestImporter("", "", ""))
        self.assertEqual(len(processor.importers), 1)
        self.assertEqual(type(processor.importers[0]), TestImporter)

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            processor.process(DATA_PATH, None, False)
        output = temp_output.getvalue()

        self.assertIn("Files got processed: 0 times", output)


class ReplayImporterTestCase(unittest.TestCase):
    def test_degrees_for(self):
        """Test whether the method correctly converts the given values to degree"""
        replay_importer = ReplayImporter()
        degree = replay_importer.degrees_for(1.0, 60.0, 3600.0, "S")
        self.assertEqual(degree, -3.0)

        degree_2 = replay_importer.degrees_for(1.0, 60.0, 3600.0, "N")
        self.assertEqual(degree_2, 3.0)


class NMEAImporterTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.nmea_importer = NMEAImporter(separator=" ")

    def test_parse_timestamp(self):
        """Test whether the method correctly converts the given string date and time"""
        timestamp = self.nmea_importer.parse_timestamp("010101", "010101")
        self.assertEqual(type(timestamp), datetime)
        self.assertEqual(str(timestamp), "2001-01-01 01:01:01")


if __name__ == "__main__":
    unittest.main()
