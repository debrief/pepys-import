import os
import unittest
import uuid
from datetime import datetime
from unittest.mock import patch
from uuid import UUID

import pytest

from pepys_import.core.store.data_store import DataStore
from pepys_import.core.validators import constants
from pepys_import.file.file_processor import FileProcessor
from pepys_import.file.importer import Importer
from pepys_import.resolvers.command_line_resolver import CommandLineResolver

FILE_PATH = os.path.dirname(__file__)
DATA_PATH = os.path.join(FILE_PATH, "sample_data")

SINGLE_REP_FILE = os.path.join(DATA_PATH, "track_files", "rep_data", "rep_test1.rep")
SINGLE_NISIDA_FILE = os.path.join(DATA_PATH, "track_files", "nisida", "nisida_example.txt")
NISIDA_FOLDER = os.path.join(DATA_PATH, "track_files", "nisida")


class UnknownPlatformTestCase(unittest.TestCase):
    def setUp(self):
        self.ds = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.ds.initialise()
        with self.ds.session_scope():
            self.ds.populate_reference()
            self.ds.populate_metadata()

        with self.ds.session_scope():
            self.change_id = self.ds.add_to_changes("TEST", datetime.now(), "TEST reason").change_id

    def test_get_platform_unknown_no_name(self):
        plat = self.ds.get_platform(change_id=self.change_id, unknown=True)

        # This will fail if the name isn't a well-formed UUID
        _ = UUID(plat.name)

        assert plat.identifier == plat.name
        assert plat.platform_type_name == "Unknown"
        assert plat.nationality_name == "Unknown"
        assert plat.privacy_name == "Public"

    def test_get_platform_unknown_with_name(self):
        plat = self.ds.get_platform(
            platform_name="Test Name", change_id=self.change_id, unknown=True
        )

        assert plat.name == "Test Name"
        assert plat.identifier == plat.name
        assert plat.platform_type_name == "Unknown"
        assert plat.nationality_name == "Unknown"
        assert plat.privacy_name == "Public"

    def test_get_sensor_no_details(self):
        plat = self.ds.get_platform(
            platform_name="Test Name", change_id=self.change_id, unknown=True
        )

        sensor = plat.get_sensor(self.ds, change_id=self.change_id)

        _ = UUID(sensor.name)
        assert sensor.sensor_type_name == "Unknown"
        assert sensor.host__name == "Test Name"
        assert sensor.privacy_name == "Public"

    def test_get_sensor_given_name(self):
        plat = self.ds.get_platform(
            platform_name="Test Name", change_id=self.change_id, unknown=True
        )

        sensor = plat.get_sensor(self.ds, sensor_name="Test Sensor Name", change_id=self.change_id)

        assert sensor.name == "Test Sensor Name"
        assert sensor.sensor_type_name == "Unknown"
        assert sensor.host__name == "Test Name"
        assert sensor.privacy_name == "Public"

    def test_get_sensor_given_type(self):
        plat = self.ds.get_platform(
            platform_name="Test Name", change_id=self.change_id, unknown=True
        )

        sensor = plat.get_sensor(self.ds, sensor_type="Radar", change_id=self.change_id)

        assert sensor.sensor_type_name == "Radar"
        assert sensor.host__name == "Test Name"
        assert sensor.privacy_name == "Public"


def test_unknown_platform_from_importer():
    class TestParser(Importer):
        def __init__(
            self,
            name="Test Importer",
            validation_level=constants.NONE_LEVEL,
            short_name="Test Importer",
            datafile_type="Test",
        ):
            super().__init__(name, validation_level, short_name, datafile_type)
            self.errors = list()

        def can_load_this_header(self, header) -> bool:
            return True

        def can_load_this_filename(self, filename):
            return True

        def can_load_this_type(self, suffix):
            return True

        def can_load_this_file(self, file_contents):
            return True

        def _load_this_file(self, data_store, path, file_object, datafile, change_id):
            self.test_platform = self.get_cached_platform(
                data_store, None, change_id=change_id, unknown=True
            )

    ds = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    ds.initialise()

    with ds.session_scope():
        ds.populate_reference()
        ds.populate_metadata()

    test_parser = TestParser()

    processor = FileProcessor()
    processor.register_importer(test_parser)

    with ds.session_scope():
        processor.process(SINGLE_REP_FILE, ds, False)
        ds.session.add(test_parser.test_platform)
        _ = uuid.UUID(test_parser.test_platform.name)
        assert test_parser.test_platform.platform_type_name == "Unknown"
        assert test_parser.test_platform.nationality_name == "Unknown"


class UnknownPlatformsResolverTestCase(unittest.TestCase):
    def setUp(self):
        self.ds = DataStore(
            "", "", "", 0, ":memory:", db_type="sqlite", missing_data_resolver=CommandLineResolver()
        )
        self.ds.initialise()

        with self.ds.session_scope():
            self.ds.populate_reference()

        self.processor = FileProcessor()
        self.processor.load_importers_dynamically()

    @patch("pepys_import.file.file_processor.prompt")
    @patch("pepys_import.resolvers.command_line_input.prompt")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_answering_store_as_unknown(self, prompt, menu_prompt, processor_prompt):
        menu_prompt.side_effect = [
            "2",  # Public
            "1",  # Yes, correct
            "3",  # Store platform as Unknown
        ]

        processor_prompt.side_effect = ["2"]

        self.processor.process(SINGLE_NISIDA_FILE, data_store=self.ds)

        with self.ds.session_scope():
            # Should have imported the right number of State entries
            states = self.ds.session.query(self.ds.db_classes.State).all()
            assert len(states) == 5

            # The platform that has been imported should be marked as Unknown
            platforms = self.ds.session.query(self.ds.db_classes.Platform).all()
            assert len(platforms) == 1

            plat = platforms[0]

            assert plat.name == "ADRI"
            assert plat.platform_type_name == "Unknown"
            assert plat.nationality_name == "Unknown"

    @patch("pepys_import.file.file_processor.prompt")
    @patch("pepys_import.resolvers.command_line_input.prompt")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_answering_store_remaining_as_unknown(self, prompt, menu_prompt, processor_prompt):
        menu_prompt.side_effect = [
            "2",  # Public
            "1",  # Yes, correct
            "4",  # Store remaining platforms as Unknown
        ]

        processor_prompt.side_effect = ["2"]

        self.processor.process(SINGLE_REP_FILE, data_store=self.ds)

        with self.ds.session_scope():
            # Should have imported the right number of State entries
            states = self.ds.session.query(self.ds.db_classes.State).all()
            assert len(states) == 8

            # The platforms that have been imported should be marked as Unknown
            platforms = self.ds.session.query(self.ds.db_classes.Platform).all()
            assert len(platforms) == 3

            for plat in platforms:
                # Check platform name is NOT a UUID
                with pytest.raises(ValueError):
                    _ = uuid.UUID(plat.name)
                assert plat.platform_type_name == "Unknown"
                assert plat.nationality_name == "Unknown"

    @patch("pepys_import.file.file_processor.prompt")
    @patch("pepys_import.resolvers.command_line_input.prompt")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_answering_store_remaining_as_unknown_multiple_files(
        self, prompt, menu_prompt, processor_prompt
    ):
        menu_prompt.side_effect = [
            "2",  # Public
            "1",  # Yes, correct
            "4",  # Store remaining platforms as Unknown
            "2",  # Public
            "1",  # Yes, correct
            "5",  # ADRI (not the Unknown one)
            "2",  # Public
            "1",  # Yes, correct
            "5",  # ADRI (not the Unknown one)
        ]

        with self.ds.session_scope():
            self.ds.populate_metadata()

        with self.ds.session_scope():
            # There should be two Platforms - one unknown and one not
            platforms = self.ds.session.query(self.ds.db_classes.Platform).all()
            # assert len(platforms) == 2

            names = [plat.name for plat in platforms]
            print(names)

        processor_prompt.side_effect = ["2", "2", "2"]

        self.processor.process(NISIDA_FOLDER, data_store=self.ds)

        with self.ds.session_scope():
            platforms = self.ds.session.query(self.ds.db_classes.Platform).all()

            nationalities = [plat.nationality_name for plat in platforms]

            # We should have the default platform nationalities (UK and FR)
            # plus a new Unknown one
            assert set(nationalities) == set(["Unknown", "United Kingdom", "France"])

            count_adri = (
                self.ds.session.query(self.ds.db_classes.Platform)
                .filter(self.ds.db_classes.Platform.name == "ADRI")
                .count()
            )
            assert count_adri == 2
