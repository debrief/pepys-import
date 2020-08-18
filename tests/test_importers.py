import os
import shutil
import stat
import unittest
from contextlib import redirect_stdout
from datetime import datetime
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

from importers.nmea_importer import NMEAImporter
from importers.replay_importer import ReplayImporter
from pepys_import.core.store.data_store import DataStore
from pepys_import.core.validators import constants as validation_constants
from pepys_import.file.file_processor import FileProcessor
from pepys_import.file.importer import Importer
from pepys_import.resolvers.command_line_resolver import CommandLineResolver

FILE_PATH = os.path.dirname(__file__)
CURRENT_DIR = os.getcwd()
BAD_DATA_PATH = os.path.join(FILE_PATH, "sample_data_bad")
DATA_PATH = os.path.join(FILE_PATH, "sample_data")
OUTPUT_PATH = os.path.join(DATA_PATH, "output_test")

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

    @patch("pepys_import.core.store.common_db.prompt", return_value="2")
    def test_process_folders_descending(self, patched_prompt):
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

    @patch("pepys_import.core.store.common_db.prompt", return_value="2")
    def test_process_folders_descending_in_memory(self, patched_prompt):
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

    @patch("pepys_import.core.store.common_db.prompt", return_value="2")
    @patch("pepys_import.file.file_processor.ARCHIVE_PATH", OUTPUT_PATH)
    def test_archiving_files(self, patched_prompt):
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
        for f in os.scandir(moved_files_path):
            # Append the name of the file to test it later on
            names.append(f.name)
            # Assert that the moved file is read-only
            # Convert file permission to octal and keep only the last three bits
            file_mode = oct(os.stat(f.path).st_mode & 0o777)
            assert file_mode == oct(stat.S_IREAD)
            # Move files back
            source_path = os.path.join(REP_DATA_PATH, f.name)
            shutil.move(f.path, source_path)
            # Change file permission to -rw-r--r--
            os.chmod(source_path, stat.S_IWRITE | stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)

        # Assert that only correctly imported files were moved to the output folder
        assert "rep_test1.rep" in names
        assert "sen_ssk_freq.dsf" in names
        assert "sen_tracks.rep" in names
        assert "uk_track.rep" in names

        # Assert that there is no file in the sources folder anymore
        assert len(os.listdir(moved_files_path)) == 0

        # Delete the output path
        shutil.rmtree(OUTPUT_PATH)


class ImporterSummaryTest(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def tearDown(self) -> None:
        descending_file = os.path.join(CURRENT_DIR, "import_status_test.db")
        if os.path.exists(descending_file):
            os.remove(descending_file)

        descending_file = os.path.join(CURRENT_DIR, "import_status_test2.db")
        if os.path.exists(descending_file):
            os.remove(descending_file)

    @patch("pepys_import.core.store.common_db.prompt", return_value="2")
    def test_summary_no_archive(self, patched_prompt):
        """Test whether descending processing works for the given path"""
        processor = FileProcessor("import_status_test.db", archive=False)

        processor.load_importers_dynamically()

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            processor.process(os.path.join(DATA_PATH, "track_files/rep_data"), None, True)
        output = temp_output.getvalue()

        lines = output.split("\n")

        # List of files which should be listed in the 'Import succeeded for' section
        succeeded_files = [
            "sen_tracks.rep",
            "sen_ssk_freq.dsf",
            "sen_frig_sensor.dsf",
            "rep_test1.rep",
            "uk_track.rep",
        ]

        succeeded_index = lines.index("Import succeeded for:")
        index = succeeded_index + 1
        while lines[index] != "":
            # First line is a filename
            filename = lines[index].replace("  - ", "")

            # Check the filename we've found is one that's supposed to be
            # listed in this section
            assert filename in succeeded_files

            # Remove it from the list once we've seen it
            succeeded_files.remove(filename)

            index += 1

        # Check there's nothing left in the list
        assert len(succeeded_files) == 0

        # List of details for files that should be in the 'import failed for' section
        failed_files = {
            "rep_test1_bad.rep": "REP Comment Importer",
            "rep_test2.rep": "REP Importer",
            "uk_track_failing_enh_validation.rep": "Enhanced Validator",
        }

        failed_index = lines.index("Import failed for:")
        index = failed_index + 1
        while lines[index] != "":
            # First line is a filename
            filename = lines[index].replace("  - ", "")
            # next line is Importers/Validators failing line
            assert "failing" in lines[index + 1]

            assert filename in failed_files.keys()

            # Next line has type of importer that is failing
            assert failed_files[filename] in lines[index + 2]

            # Remove it from the dict so we can check it's empty at the end
            del failed_files[filename]

            # Next line lists failure report
            assert "Failure report" in lines[index + 3]

            index += 4

        # Check there's nothing left in the dict
        assert len(failed_files) == 0

    @patch("pepys_import.core.store.common_db.prompt", return_value="2")
    @patch("pepys_import.file.file_processor.ARCHIVE_PATH", OUTPUT_PATH)
    def test_summary_with_archive(self, patched_prompt):
        """Test whether descending processing works for the given path"""
        processor = FileProcessor("import_status_test2.db", archive=True)

        processor.load_importers_dynamically()

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            processor.process(os.path.join(DATA_PATH, "track_files/rep_data"), None, True)
        output = temp_output.getvalue()

        lines = output.split("\n")

        # List of files which should be listed in the 'Import succeeded for' section
        succeeded_files = [
            "sen_tracks.rep",
            "sen_ssk_freq.dsf",
            "sen_frig_sensor.dsf",
            "rep_test1.rep",
            "uk_track.rep",
        ]

        succeeded_index = lines.index("Import succeeded for:")
        index = succeeded_index + 1
        while lines[index] != "":
            # First line is a filename
            filename = lines[index].replace("  - ", "")
            # next line is 'Archived to' line
            assert "Archived to" in lines[index + 1]

            # Check the filename we've found is one that's supposed to be
            # listed in this section
            assert filename in succeeded_files

            # Remove it from the list once we've seen it
            succeeded_files.remove(filename)

            index += 2

        # Check there's nothing left in the list
        assert len(succeeded_files) == 0

        # List of details for files that should be in the 'import failed for' section
        failed_files = {
            "rep_test1_bad.rep": "REP Comment Importer",
            "rep_test2.rep": "REP Importer",
            "uk_track_failing_enh_validation.rep": "Enhanced Validator",
        }

        failed_index = lines.index("Import failed for:")
        index = failed_index + 1
        while lines[index] != "":
            # First line is a filename
            filename = lines[index].replace("  - ", "")
            # next line is Importers/Validators failing line
            assert "failing" in lines[index + 1]

            assert filename in failed_files.keys()

            # Next line has type of importer that is failing
            assert failed_files[filename] in lines[index + 2]

            # Remove it from the dict so we can check it's empty at the end
            del failed_files[filename]

            # Next line lists failure report
            assert "Failure report" in lines[index + 3]

            index += 4

        # Check there's nothing left in the dict
        assert len(failed_files) == 0

        moved_files_path = str(list(Path(OUTPUT_PATH).rglob("sources"))[0])
        assert os.path.exists(moved_files_path) is True

        # Scan the files in sources folder
        for f in os.scandir(moved_files_path):
            # Move files back
            source_path = os.path.join(REP_DATA_PATH, f.name)
            shutil.move(f.path, source_path)
            # Change file permission to -rw-r--r--
            os.chmod(source_path, stat.S_IWRITE | stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)

        # Delete the output path
        shutil.rmtree(OUTPUT_PATH)


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

        processor.register_importer(TestImporter("", "", "", ""))
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

        processor.register_importer(TestImporter("", "", "", ""))
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

        processor.register_importer(TestImporter("", "", "", ""))
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

        processor.register_importer(TestImporter("", "", "", ""))
        self.assertEqual(len(processor.importers), 1)
        self.assertEqual(type(processor.importers[0]), TestImporter)

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            processor.process(DATA_PATH, None, False)
        output = temp_output.getvalue()

        self.assertIn("Files got processed: 0 times", output)


class ImporterInvalidValidationLevelTest(unittest.TestCase):
    def test_invalid_validation_level(self):
        class TestImporter(Importer):
            def __init__(self):
                super().__init__(
                    name="Test Importer",
                    validation_level="invalid level",
                    short_name="Test Importer",
                    datafile_type="Importer",
                )

            def can_load_this_header(self, header) -> bool:
                return True

            def can_load_this_filename(self, filename):
                return True

            def can_load_this_type(self, suffix):
                return True

            def can_load_this_file(self, file_contents):
                return True

            def _load_this_file(self, data_store, path, file_object, datafile, change_id):
                pass

        with pytest.raises(ValueError, match="Invalid Validation Level"):
            processor = FileProcessor()

            processor.register_importer(TestImporter())
            processor.process(DATA_PATH, None, False)


class ImporterDisableRecordingTest(unittest.TestCase):
    def test_turn_off_recording(self):
        class TestImporter(Importer):
            def __init__(self):
                super().__init__(
                    name="Test Importer",
                    validation_level=validation_constants.BASIC_LEVEL,
                    short_name="Test Importer",
                    datafile_type="Importer",
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


class ImporterGetCachedSensorTest(unittest.TestCase):
    @patch("pepys_import.core.store.common_db.prompt", return_value="2")
    def test_platform_sensor_mapping_has_sensible_values(self, patched_prompt):
        processor = FileProcessor(":memory:", archive=False)

        processor.register_importer(ReplayImporter())

        processor.process(REP_DATA_PATH, None, False)

        cache = processor.importers[0].platform_sensor_mapping

        # There must be at least one entry in the cache
        assert len(cache) > 0

        # All the values must not be None
        assert all([value is not None for value in cache.values()])

    def test_get_cached_sensor(self):
        data_store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        data_store.initialise()

        with data_store.session_scope():
            replay_importer = ReplayImporter()
            replay_importer.platform_sensor_mapping = {}

            change_id = data_store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id

            platform = data_store.get_platform(
                platform_name="TestPlatformName", change_id=change_id
            )

            # Should be nothing in the mapping to start with
            assert len(replay_importer.platform_sensor_mapping) == 0

            # Call first time - should create sensor and store in cache
            sensor = replay_importer.get_cached_sensor(
                data_store=data_store,
                sensor_name=None,
                sensor_type=None,
                platform_id=platform.platform_id,
                change_id=change_id,
            )

            assert sensor is not None

            # Check stored in cache
            assert len(replay_importer.platform_sensor_mapping) == 1
            assert sensor in replay_importer.platform_sensor_mapping.values()

            # Call a second time
            sensor = replay_importer.get_cached_sensor(
                data_store=data_store,
                sensor_name=None,
                sensor_type=None,
                platform_id=platform.platform_id,
                change_id=change_id,
            )

            # Check cache still only has one sensor in it
            assert len(replay_importer.platform_sensor_mapping) == 1
            assert sensor in replay_importer.platform_sensor_mapping.values()

    def test_get_cached_sensor_specifying_sensor_name(self):
        data_store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        data_store.initialise()

        with data_store.session_scope():
            replay_importer = ReplayImporter()
            replay_importer.platform_sensor_mapping = {}

            change_id = data_store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id

            platform = data_store.get_platform(
                platform_name="TestPlatformName", change_id=change_id
            )

            # Should be nothing in the mapping to start with
            assert len(replay_importer.platform_sensor_mapping) == 0

            # Call first time - should create sensor and store in cache
            sensor = replay_importer.get_cached_sensor(
                data_store=data_store,
                sensor_name=None,
                sensor_type=None,
                platform_id=platform.platform_id,
                change_id=change_id,
            )

            assert sensor is not None

            # Check stored in cache
            assert len(replay_importer.platform_sensor_mapping) == 1
            assert sensor in replay_importer.platform_sensor_mapping.values()

            # Call a second time, but this time specify a name
            sensor = replay_importer.get_cached_sensor(
                data_store=data_store,
                sensor_name="Test Sensor",
                sensor_type=None,
                platform_id=platform.platform_id,
                change_id=change_id,
            )

            # Check name of returned sensor
            assert sensor.name == "Test Sensor"

            # Check cache still only has one sensor in it
            assert len(replay_importer.platform_sensor_mapping) == 1


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
        self.nmea_importer = NMEAImporter()

    def test_parse_timestamp(self):
        """Test whether the method correctly converts the given string date and time"""
        timestamp = self.nmea_importer.parse_timestamp("010101", "010101")
        self.assertEqual(type(timestamp), datetime)
        self.assertEqual(str(timestamp), "2001-01-01 01:01:01")


class TestImportWithDuplicatePlatformNames(unittest.TestCase):
    def setUp(self):
        self.store = DataStore(
            "",
            "",
            "",
            0,
            ":memory:",
            db_type="sqlite",
            missing_data_resolver=CommandLineResolver(),
        )
        self.store.initialise()
        with self.store.session_scope():
            self.store.populate_reference()
            self.change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id

    @patch("pepys_import.resolvers.command_line_input.prompt")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_import_with_duplicate_platform_names(self, resolver_prompt, menu_prompt):
        # Provide datafile name, and approve creation of datafile
        # Add platform with name DOLPHIN, identifier 123, trigraph and quadgraph
        # Select UK nationality, and select platform type, privacy etc
        # Appove creation
        # Add sensor called TestSensor, type GPS, Public
        # Add platform with name DOLPHIN, identifier 123, trigraph and quadgraph
        # Select France nationality, plus platform type, privacy etc
        # Add sensor called TestSensor, type GPS, Public

        # The upshot of all of this is that we have two rows imported from this datafile
        # both with the same name platform, but referring to two separate platforms that belong
        # to UK and France
        resolver_prompt.side_effect = [
            "rep_duplicate_name_test.rep",
            "DOLPHIN",
            "123",
            "DLP",
            "DLPH",
            "TestSensor",
            "DOLPHIN",
            "123",
            "DLP",
            "DLPH",
            "TestSensor",
        ]

        menu_prompt.side_effect = [
            "3",
            "1",
            "2",
            "3",
            "3",
            "3",
            "1",
            "2",
            "3",
            "3",
            "1",
            "2",
            "5",
            "3",
            "3",
            "1",
            "2",
            "3",
            "3",
            "1",
        ]

        processor = FileProcessor(archive=False)
        processor.register_importer(ReplayImporter())

        processor.process(
            os.path.join(DATA_PATH, "track_files", "other_data", "rep_duplicate_name_test.rep"),
            self.store,
            False,
        )

        with self.store.session_scope():
            # Check the State entries refer to two different platforms, one that is UK and one that is France
            states = self.store.session.query(self.store.db_classes.State).all()

            assert len(states) == 2

            plat1_id = states[0].platform_id
            plat2_id = states[1].platform_id

            plat1 = (
                self.store.session.query(self.store.db_classes.Platform)
                .filter(self.store.db_classes.Platform.platform_id == plat1_id)
                .all()
            )

            assert len(plat1) == 1
            assert plat1[0].name == "DOLPHIN"
            assert plat1[0].nationality_name == "United Kingdom"

            plat2 = (
                self.store.session.query(self.store.db_classes.Platform)
                .filter(self.store.db_classes.Platform.platform_id == plat2_id)
                .all()
            )

            assert len(plat2) == 1
            assert plat2[0].name == "DOLPHIN"
            assert plat2[0].nationality_name == "France"


if __name__ == "__main__":
    unittest.main()
