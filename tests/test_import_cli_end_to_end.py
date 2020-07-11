import os
import random
import unittest
from unittest.mock import patch

import pytest
from sqlalchemy.exc import OperationalError
from testing.postgresql import Postgresql

from importers.nisida_importer import NisidaImporter
from importers.replay_importer import ReplayImporter
from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor
from pepys_import.resolvers.command_line_resolver import CommandLineResolver

FILE_PATH = os.path.dirname(__file__)
DATA_PATH = os.path.join(FILE_PATH, "sample_data")

FALLBACK_RESPONSES = [
    "A" * 500,
    "Hello",
    "TestEntry1",
    "123",
    " ",
    "",
    "\t",
    "TestEntry2WithAccént",
    "TestEntry\tWithWhitespace",
]


def create_menu_patch(*args, **kwargs):
    prompt = args[0]
    print(f"Prompt: {prompt}")
    if len(args) > 1:
        choices = args[1]
    else:
        choices = []

    if len(choices) > 0:
        random_choice = random.randint(1, len(choices))
        response = str(random_choice)
        response_explanation = choices[random_choice - 1]
        print(f"Response: {response} [{response_explanation}]")
    else:
        if "completer" in kwargs and len(kwargs["completer"].words) > 0:
            response = random.choice(kwargs["completer"].words)
        else:
            response = random.choice(FALLBACK_RESPONSES)
        print(f"Response: {response}")

    return response


def clr_prompt_patch(*args, **kwargs):
    prompt = args[0]
    print(f"Prompt: {prompt}")

    if "Please type level of" in prompt:
        response = str(random.randint(0, 10000))
        print(f"Response: {response}")
        return response
    else:
        response = random.choice(FALLBACK_RESPONSES)
        print(f"Response: {response}")

        return response


class TestClass:
    def setup_method(self, test_method):
        self.postgres = None
        self.store = None
        try:
            self.postgres = Postgresql(
                database="test", host="localhost", user="postgres", password="postgres", port=55527,
            )
        except RuntimeError:
            print("PostgreSQL database couldn't be created! Test is skipping.")
            return
        try:
            self.store = DataStore(
                db_name="test",
                db_host="localhost",
                db_username="postgres",
                db_password="postgres",
                db_port=55527,
                db_type="postgres",
                missing_data_resolver=CommandLineResolver(),
            )
            self.store.initialise()
        except OperationalError:
            print("Database schema and data population failed! Test is skipping.")
        with self.store.session_scope():
            self.store.populate_reference()

    def teardown_method(self):
        try:
            self.postgres.stop()
        except AttributeError:
            return

    @patch("pepys_import.resolvers.command_line_resolver.create_menu", new=create_menu_patch)
    @patch("pepys_import.resolvers.command_line_resolver.prompt", new=clr_prompt_patch)
    @pytest.mark.parametrize("execution_number", range(5))  # Used to just repeat the test 5 times
    def test_load_rep1(self, execution_number):
        seed = random.randint(0, 10000)
        print("---- Starting end-to-end automaton test")
        print(f"Running with seed = {seed}")

        # Replace this line with the seed printed out by a previous run of the test to duplicate that test
        random.seed(seed)

        processor = FileProcessor(archive=False)
        processor.register_importer(ReplayImporter())

        processor.process(
            os.path.join(DATA_PATH, "track_files", "rep_data", "rep_test1.rep"), self.store, False,
        )
        print("---- End of end-to-end autmaton test")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu", new=create_menu_patch)
    @patch("pepys_import.resolvers.command_line_resolver.prompt", new=clr_prompt_patch)
    @pytest.mark.parametrize("execution_number", range(5))  # Used to just repeat the test 5 times
    def test_load_nisida(self, execution_number):
        seed = random.randint(0, 10000)
        print("---- Starting end-to-end automaton test")
        print(f"Running with seed = {seed}")

        # Replace this line with the seed printed out by a previous run of the test to duplicate that test
        random.seed(seed)

        processor = FileProcessor(archive=False)
        processor.register_importer(NisidaImporter())

        processor.process(
            os.path.join(DATA_PATH, "track_files", "nisida", "nisida_example.txt"),
            self.store,
            False,
        )
        print("---- End of end-to-end automaton test")
