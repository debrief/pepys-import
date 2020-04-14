import os
import shutil
import stat
import unittest
from contextlib import redirect_stdout
from datetime import datetime
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from importers.nmea_importer import NMEAImporter
from importers.replay_importer import ReplayImporter
from pepys_import.file.file_processor import FileProcessor
from pepys_import.file.importer import Importer
from pepys_import.core.validators import constants as validation_constants


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
        # Assert that REP files exist in the original location
        input_files = os.listdir(REP_DATA_PATH)
        assert "rep_test1.rep" in input_files
        assert "sen_ssk_freq.dsf" in input_files
        assert "sen_tracks.rep" in input_files
        assert "uk_track.rep" in input_files

        names = list()
        processor = FileProcessor(archive=True)
        processor.register_importer(ReplayImporter())
        processor.process(REP_DATA_PATH, None, False)

        # Assert that successfully imported files are not in the original location
        input_files = os.listdir(REP_DATA_PATH)
        assert "rep_test1.rep" not in input_files
        assert "sen_ssk_freq.dsf" not in input_files
        assert "sen_tracks.rep" not in input_files
        assert "uk_track.rep" not in input_files

        moved_files_path = str(list(Path(OUTPUT_PATH).rglob("sources"))[0])
        assert os.path.exists(moved_files_path) is True

        # Scan the files in sources folder
        for file in os.scandir(moved_files_path):
            # Append the name of the file to test it later on
            names.append(file.name)
            # Assert that the moved file is read-only
            # Convert file permission to octal and keep only the last three bits
            file_mode = oct(os.stat(file.path).st_mode & 0o777)
            assert file_mode == oct(stat.S_IREAD)
            # Move files back
            source_path = os.path.join(REP_DATA_PATH, file.name)
            shutil.move(file.path, source_path)
            # Change file permission to -rw-r--r--
            os.chmod(source_path, stat.S_IWRITE | stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)

        # Assert that only correctly imported files were moved to the output folder
        assert "rep_test1.rep" in names
        assert "sen_ssk_freq.dsf" in names
        assert "sen_tracks.rep" in names
        assert "uk_track.rep" in names

        # Assert that there is no file in the sources folder anymore
        assert len(os.listdir(moved_files_path)) == 0


class ImporterSummaryTest(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def tearDown(self) -> None:
        descending_file = os.path.join(CURRENT_DIR, "import_status_test.db")
        if os.path.exists(descending_file):
            os.remove(descending_file)

    def test_summary_no_archive(self):
        """Test whether descending processing works for the given path"""
        processor = FileProcessor("import_status_test.db", archive=False)

        processor.load_importers_dynamically()

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            processor.process(os.path.join(DATA_PATH, "track_files/rep_data"), None, True)
        output = temp_output.getvalue()
        
        assert """Import succeeded for:
  - sen_tracks.rep
  - sen_ssk_freq.dsf
  - rep_test1.rep
  - uk_track.rep""" in output

        assert """  - uk_track_failing_enh_validation.rep
    - Validators failing:
      - Enhanced Validator""" in output

        assert """  - rep_test1_bad.rep
    - Importers failing:
      - REP Comment Importer""" in output

        assert """  - rep_test2.rep
    - Importers failing:
      - REP Importer""" in output

        assert """  - sen_frig_sensor.dsf
    - Importers failing:
      - REP Importer""" in output

    def test_summary_with_archive(self):
        """Test whether descending processing works for the given path"""
        processor = FileProcessor("import_status_test.db", archive=True)

        processor.load_importers_dynamically()

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            processor.process(os.path.join(DATA_PATH, "track_files/rep_data"), None, True)
        output = temp_output.getvalue()
        
        assert """Import succeeded for:
  - sen_tracks.rep
    - Archived to """ in output

        assert """  - sen_ssk_freq.dsf
    - Archived to """ in output

        assert """  - rep_test1.rep
    - Archived to """ in output

        assert """  - uk_track.rep
    - Archived to """ in output

        assert """  - uk_track_failing_enh_validation.rep
    - Validators failing:
      - Enhanced Validator""" in output

        assert """  - rep_test1_bad.rep
    - Importers failing:
      - REP Comment Importer""" in output

        assert """  - rep_test2.rep
    - Importers failing:
      - REP Importer""" in output

        assert """  - sen_frig_sensor.dsf
    - Importers failing:
      - REP Importer""" in output

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


class ImporterDisableRecordingTest(unittest.TestCase):
    def test_turn_off_recording(self):
        class TestImporter(Importer):
            def __init__(self):
                super().__init__(
                    name="Test Importer", validation_level=validation_constants.BASIC_LEVEL, short_name="Test Importer"
                )
                self.disable_recording()

            def can_load_this_header(self, header) -> bool:
                return True

            def can_load_this_filename(self, filename):
                return True

            def can_load_this_type(self, suffix):
                return True

            def can_load_this_file(self, file_contents):
                return True

            def _load_this_file(self, data_store, path, file_object, datafile, change_id):
                assert file_object.ignored_importers == ["Test Importer"]

        processor = FileProcessor()

        processor.register_importer(TestImporter())
        processor.process(DATA_PATH, None, False)


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
