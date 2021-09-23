import os
import platform
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
from pepys_import import __version__
from pepys_import.core.store.data_store import DataStore
from pepys_import.core.validators import constants as validation_constants
from pepys_import.file.file_processor import FileProcessor
from pepys_import.file.importer import Importer
from pepys_import.resolvers.command_line_resolver import CommandLineResolver
from pepys_import.resolvers.default_resolver import DefaultResolver
from pepys_import.utils.import_utils import sort_files

FILE_PATH = os.path.dirname(__file__)
CURRENT_DIR = os.getcwd()
BAD_DATA_PATH = os.path.join(FILE_PATH, "sample_data_bad")
DATA_PATH = os.path.join(FILE_PATH, "sample_data")
OUTPUT_PATH = os.path.join(DATA_PATH, "output_test")

REP_DATA_PATH = os.path.join(DATA_PATH, "track_files", "rep_data")
SINGLE_REP_FILE = os.path.join(DATA_PATH, "track_files", "rep_data", "rep_test1.rep")
SINGLE_REP_FILE_2 = os.path.join(DATA_PATH, "track_files", "rep_data", "uk_track.rep")


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
    def test_archiving_files(self, patched_prompt):
        """Test whether archive flag correctly works for File Processor"""
        # Assert that REP files exist in the original location
        input_files = os.listdir(REP_DATA_PATH)
        assert "rep_test1.rep" in input_files
        assert "sen_ssk_freq.dsf" in input_files
        assert "sen_tracks.rep" in input_files
        assert "uk_track.rep" in input_files

        names = list()
        processor = FileProcessor(archive=True, archive_path=OUTPUT_PATH)
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
        for f in sort_files(os.scandir(moved_files_path)):
            # Append the name of the file to test it later on
            names.append(f.name)
            # Assert that the moved file is read-only
            # Convert file permission to octal and keep only the last three bits
            if platform.system() != "Windows":
                # Can only check file mode properly on Unix systems
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
    def test_summary_with_archive(self, patched_prompt):
        """Test whether descending processing works for the given path"""
        processor = FileProcessor("import_status_test2.db", archive=True, archive_path=OUTPUT_PATH)

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
        for f in sort_files(os.scandir(moved_files_path)):
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
                self.set_highlighting_level("none")

            def can_load_this_header(self, header) -> bool:
                return True

            def can_load_this_filename(self, filename):
                return True

            def can_load_this_type(self, suffix):
                return True

            def can_load_this_file(self, file_contents):
                return True

            def _load_this_file(self, data_store, path, file_object, datafile, change_id):
                assert "Test Importer" in file_object.importer_highlighting_levels
                assert file_object.importer_highlighting_levels["Test Importer"] == "none"

        processor = FileProcessor()

        processor.register_importer(TestImporter())
        processor.process(DATA_PATH, None, False)

    def test_record_to_database(self):
        class TestImporter(Importer):
            def __init__(self):
                super().__init__(
                    name="Test Importer",
                    validation_level=validation_constants.BASIC_LEVEL,
                    short_name="Test Importer",
                    datafile_type="Importer",
                )
                self.set_highlighting_level("database")

            def can_load_this_header(self, header) -> bool:
                return True

            def can_load_this_filename(self, filename):
                return True

            def can_load_this_type(self, suffix):
                return True

            def can_load_this_file(self, file_contents):
                return True

            def _load_this_file(self, data_store, path, file_object, datafile, change_id):
                assert "Test Importer" in file_object.importer_highlighting_levels
                assert file_object.importer_highlighting_levels["Test Importer"] == "database"

        processor = FileProcessor()

        processor.register_importer(TestImporter())
        processor.process(DATA_PATH, None, False)

    def test_default_recording_level(self):
        class TestImporter(Importer):
            def __init__(self):
                super().__init__(
                    name="Test Importer",
                    validation_level=validation_constants.BASIC_LEVEL,
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
                assert "Test Importer" in file_object.importer_highlighting_levels
                assert file_object.importer_highlighting_levels["Test Importer"] == "html"

        processor = FileProcessor()

        processor.register_importer(TestImporter())
        processor.process(DATA_PATH, None, False)


class ImporterGetCachedSensorTest(unittest.TestCase):
    @patch("pepys_import.core.store.common_db.prompt", return_value="2")
    def test_platform_sensor_mapping_has_sensible_values(self, patched_prompt):
        processor = FileProcessor(":memory:", archive=False)

        processor.register_importer(ReplayImporter())

        processor.process(SINGLE_REP_FILE, None, False)

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

    @patch("pepys_import.file.file_processor.prompt")
    @patch("pepys_import.resolvers.command_line_input.prompt")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_import_with_duplicate_platform_names(
        self, resolver_prompt, menu_prompt, file_processor_prompt
    ):
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
            "2",  # Public
            "1",  # Yes, create
            "1",  # Add new platform
            "2",  # UK
            "2",  # PLATFORM-TYPE-1
            "2",  # Public
            "1",  # Yes, create
            "1",  # Add new sensor
            "2",  # GPS
            "2",  # Public
            "1",  # Yes, create
            "1",  # Add new platform
            "4",  # France
            "2",  # PLATFORM-TYPE-1
            "2",  # Public
            "1",  # Yes, create
            "1",  # Add new sensor
            "2",  # GPS
            "2",  # Public
            "1",  # Yes, create
        ]
        file_processor_prompt.side_effect = [
            "2",  # Import metadata and measurement
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


class TestImportMetadataOnly(unittest.TestCase):
    def setUp(self) -> None:
        self.resolver = CommandLineResolver()
        self.store = DataStore(
            "",
            "",
            "",
            0,
            ":memory:",
            db_type="sqlite",
            missing_data_resolver=self.resolver,
        )
        self.store.initialise()
        with self.store.session_scope():
            self.store.populate_reference()
            self.store.populate_metadata()
        self.processor = FileProcessor(archive=False)
        self.processor.register_importer(ReplayImporter())

    @patch("pepys_import.file.file_processor.prompt")
    @patch("pepys_import.resolvers.command_line_input.prompt")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_import_metadata_only(self, resolver_prompt, menu_prompt, file_processor_prompt):
        resolver_prompt.side_effect = [
            # For rep_test1.rep import
            "SENSOR",
            "123",
            "SEN",
            "SENS",
            "TA",
            "SEARCH_PLATFORM",
            "123",
            "SEA",
            "SEAR",
            "TA",
            # For uk_track.rep import,
            "SPLENDID",
            "123",
            "SPL",
            "SPLE",
            "GPS",
        ]

        menu_prompt.side_effect = [
            # For rep_test1.rep import
            "3",  # Public
            "1",  # Yes, correct
            "1",  # Add platform
            "3",  # UK
            "3",  # PLATFORM-TYPE-1,
            "3",  # Public
            "1",  # Yes, create
            "1",  # Add sensor
            "3",  # GPS
            "3",  # Public
            "1",  # Yes, create
            "1",  # Add platform
            "3",  # UK
            "5",  # Fisher
            "3",  # Public
            "1",  # Yes, create
            "1",  # Add sensor
            "4",  # SENSOR-TYPE-1
            "3",  # Public
            "1",  # Yes, create
            # For uk_track.rep import
            "3",  # Public
            "1",  # Yes, correct
            "1",  # Add platform
            "3",  # UK
            "3",  # PLATFORM-TYPE-1,
            "3",  # Public
            "1",  # Yes, create
            "1",  # Add sensor
            "3",  # GPS
            "3",  # Public
            "1",  # Yes, create
        ]
        file_processor_prompt.side_effect = [
            "2",  # Import metadata and measurement
            "1",  # Import metadata
        ]

        # Import metadata and measurements
        self.processor.process(
            SINGLE_REP_FILE,
            self.store,
            False,
        )

        with self.store.session_scope():
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            assert len(platforms) == 6

            sensors = self.store.session.query(self.store.db_classes.Sensor).all()
            assert len(sensors) == 8

            states = len(self.store.session.query(self.store.db_classes.State).all())
            contacts = len(self.store.session.query(self.store.db_classes.Contact).all())
            comments = len(self.store.session.query(self.store.db_classes.Comment).all())

        # import metadata only this time
        self.processor.process(
            SINGLE_REP_FILE_2,
            self.store,
            False,
        )

        with self.store.session_scope():
            # SPLENDID platform should be added to the database
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            assert len(platforms) == 7
            assert platforms[-1].name == "SPLENDID"

            # GPS Sensor on SPLENDID platform should be added to the database
            sensors = self.store.session.query(self.store.db_classes.Sensor).all()
            assert len(sensors) == 9
            assert sensors[-1].name == "GPS"
            assert sensors[-1].host__name == "SPLENDID"

            # Measurements should be the same
            assert len(self.store.session.query(self.store.db_classes.State).all()) == states
            assert len(self.store.session.query(self.store.db_classes.Contact).all()) == contacts
            assert len(self.store.session.query(self.store.db_classes.Comment).all()) == comments


class TestImportSkipFile(unittest.TestCase):
    def setUp(self) -> None:
        self.resolver = CommandLineResolver()
        self.store = DataStore(
            "",
            "",
            "",
            0,
            ":memory:",
            db_type="sqlite",
            missing_data_resolver=self.resolver,
        )
        self.store.initialise()
        with self.store.session_scope():
            self.store.populate_reference()
            self.store.populate_metadata()
        self.processor = FileProcessor(archive=False)
        self.processor.register_importer(ReplayImporter())

    @patch("pepys_import.file.file_processor.prompt")
    @patch("pepys_import.resolvers.command_line_input.prompt")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_skip_file(self, resolver_prompt, menu_prompt, file_processor_prompt):
        resolver_prompt.side_effect = [
            # For rep_test1.rep import
            "rep_test1.rep",
            "SENSOR",
            "123",
            "SEN",
            "SENS",
            "TA",
            "SEARCH_PLATFORM",
            "123",
            "SEA",
            "SEAR",
            "TA",
            # For sen_tracks.rep import,
            "sen_tracks.rep",
            "New_SSK",
            "123",
            "New",
            "New_",
            "New_SSK_FREQ",
        ]

        menu_prompt.side_effect = [
            # For rep_test1.rep import
            "3",  # Public
            "1",  # Yes, correct
            "1",  # Add platform
            "3",  # UK
            "3",  # PLATFORM-TYPE-1,
            "3",  # Public
            "1",  # Yes, create
            "1",  # Add sensor
            "3",  # GPS
            "3",  # Public
            "1",  # Yes, create
            "1",  # Add platform
            "3",  # UK
            "5",  # Fisher
            "3",  # Public
            "1",  # Yes, create
            "1",  # Add sensor
            "4",  # SENSOR-TYPE-1
            "3",  # Public
            "1",  # Yes, create
            # For sen_tracks.rep import
            "3",  # Public
            "1",  # Yes, correct
            "1",  # Add platform
            "3",  # UK
            "3",  # PLATFORM-TYPE-1,
            "3",  # Public
            "1",  # Yes, create
            "1",  # Add sensor
            "3",  # GPS
            "3",  # Public
            "1",  # Yes, create
            "3",  # New_SSK / 123 / United Kingdom
        ]
        file_processor_prompt.side_effect = [
            "3",  # Don't import this file
        ]

        with self.store.session_scope():
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            assert len(platforms) == 4
            platform_ids = [p.platform_id for p in platforms]

            sensors = self.store.session.query(self.store.db_classes.Sensor).all()
            assert len(sensors) == 6
            sensor_ids = [p.sensor_id for p in sensors]

            states = len(self.store.session.query(self.store.db_classes.State).all())
            contacts = len(self.store.session.query(self.store.db_classes.Contact).all())
            comments = len(self.store.session.query(self.store.db_classes.Comment).all())

        self.processor.process(
            SINGLE_REP_FILE,
            self.store,
            False,
        )

        with self.store.session_scope():
            # All tables should have the same number of rows
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            assert len(platforms) == 4
            new_platform_ids = [p.platform_id for p in platforms]
            assert platform_ids == new_platform_ids

            sensors = self.store.session.query(self.store.db_classes.Sensor).all()
            assert len(sensors) == 6
            new_sensor_ids = [p.sensor_id for p in sensors]
            assert sensor_ids == new_sensor_ids

            assert len(self.store.session.query(self.store.db_classes.State).all()) == states
            assert len(self.store.session.query(self.store.db_classes.Contact).all()) == contacts
            assert len(self.store.session.query(self.store.db_classes.Comment).all()) == comments


def test_changes_table_entry_contains_version():
    store = DataStore(
        "",
        "",
        "",
        0,
        ":memory:",
        db_type="sqlite",
        missing_data_resolver=DefaultResolver(),
    )

    store.initialise()
    with store.session_scope():
        store.populate_reference()
        store.populate_metadata()
    processor = FileProcessor(archive=False)
    processor.register_importer(ReplayImporter())

    processor.process(SINGLE_REP_FILE, store)

    with store.session_scope():
        change_entries = store.session.query(store.db_classes.Change).all()

        # Check at least one of the entries contains the right text
        # (we use contains not equals, as release versions of Pepys will have an extra
        # bit of text giving the build date - but this won't be present for dev versions)
        for entry in change_entries:
            if f"Importing 'rep_test1.rep' using Pepys {__version__}" in entry.reason:
                return

        assert False


if __name__ == "__main__":
    unittest.main()
