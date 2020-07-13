import os
import random
import unittest
from unittest.mock import patch

import pytest
from sqlalchemy.exc import OperationalError
from testing.postgresql import Postgresql

from importers.gpx_importer import GPXImporter
from importers.nisida_importer import NisidaImporter
from importers.replay_importer import ReplayImporter
from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor
from pepys_import.resolvers.command_line_resolver import CommandLineResolver

FILE_PATH = os.path.dirname(__file__)
DATA_PATH = os.path.join(FILE_PATH, "sample_data")


@patch("pepys_import.resolvers.command_line_input.prompt")
@patch("pepys_import.resolvers.command_line_resolver.prompt")
def test_rep_test_1_import(prompt, menu_prompt):
    """Tests a full run of an import of rep_test1.rep using the importer CLI"""
    menu_prompt.side_effect = [
        "3",  # Public
        "1",  # Yes, correct
        "2",  # Add platform
        "3",  # UK
        "3",  # PLATFORM-TYPE-1,
        "3",  # Public
        "1",  # Yes, create
        "2",  # Add sensor
        "3",  # GPS
        "3",  # Public
        "1",  # Yes, create
        "2",  # Add platform
        "3",  # UK
        "5",  # Fisher
        "3",  # Public
        "1",  # Yes, create
        "2",  # Add sensor
        "4",  # SENSOR-TYPE-1
        "3",  # Public
        "1",  # Yes, create
        "1",  # Search for platform
        "2",  # No to synonym creation
        "3",  # TA
        "1",  # SEARCH-PLATFORM
        "1",  # SENSOR
        "1",  # SEARCH_PLATFORM
    ]
    prompt.side_effect = [
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
        "SEARCH_PLATFORM / 123 / United Kingdom ",
    ]

    store = DataStore(
        "", "", "", 0, ":memory:", db_type="sqlite", missing_data_resolver=CommandLineResolver()
    )
    store.initialise()
    with store.session_scope():
        store.populate_reference()
        store.populate_metadata()

    processor = FileProcessor(archive=False)
    processor.register_importer(ReplayImporter())

    processor.process(
        os.path.join(DATA_PATH, "track_files", "rep_data", "rep_test1.rep"), store, False
    )


@patch("pepys_import.resolvers.command_line_input.prompt")
@patch("pepys_import.resolvers.command_line_resolver.prompt")
def test_gpx_1_0_import(prompt, menu_prompt):
    """Tests a full run of an import of rep_test1.rep using the importer CLI"""
    menu_prompt.side_effect = [
        "5",  # Private
        "1",  # Yes, create
        "2",  # Add new platform
        "6",  # Germany
        "6",  # Ferry
        "5",  # Private
        "1",  # Yes, create
        "2",  # Add new sensor
        "5",  # Private
        "1",  # Yes, create
    ]
    prompt.side_effect = [
        "gpx_1_0.gpx",
        "NELSON",
        "N123",
        "NEL",
        "NELS",
        "GPS",
    ]

    store = DataStore(
        "", "", "", 0, ":memory:", db_type="sqlite", missing_data_resolver=CommandLineResolver()
    )
    store.initialise()
    with store.session_scope():
        store.populate_reference()
        store.populate_metadata()

    processor = FileProcessor(archive=False)
    processor.register_importer(GPXImporter())

    processor.process(os.path.join(DATA_PATH, "track_files", "gpx", "gpx_1_0.gpx"), store, False)
