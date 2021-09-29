import os
import random
from unittest.mock import patch

import pytest
from prompt_toolkit.formatted_text import FormattedText
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


@patch("pepys_import.file.file_processor.prompt")
@patch("pepys_import.resolvers.command_line_input.prompt")
@patch("pepys_import.resolvers.command_line_resolver.prompt")
def test_rep_test_1_import(prompt, menu_prompt, processor_prompt):
    """Tests a full run of an import of rep_test1.rep using the importer CLI

    **Note:** This will fail if the CLI interface changes at all!"""
    menu_prompt.side_effect = [
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
        "2",  # Search for platform
        "2",  # No to synonym creation
        "3",  # TA
        "1",  # SEARCH-PLATFORM
        "1",  # SENSOR
        "1",  # SEARCH_PLATFORM
    ]
    prompt.side_effect = [
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
    processor_prompt.side_effect = [
        "2",  # Import metadata and measurement
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


@patch("pepys_import.file.file_processor.prompt")
@patch("pepys_import.resolvers.command_line_input.prompt")
@patch("pepys_import.resolvers.command_line_resolver.prompt")
def test_gpx_1_0_import(prompt, menu_prompt, processor_prompt):
    """Tests a full run of an import of gpx_1_0.gpx using the importer CLI.

    **Note:** This will fail if the CLI interface changes at all!"""
    menu_prompt.side_effect = [
        "4",  # Private
        "1",  # Yes, create
        "1",  # Add new platform
        "5",  # Germany
        "5",  # Ferry
        "5",  # Private
        "1",  # Yes, create
        "1",  # Add new sensor
        "5",  # Private
        "1",  # Yes, create
    ]
    prompt.side_effect = [
        "NELSON",
        "N123",
        "NEL",
        "NELS",
        "GPS",
    ]
    processor_prompt.side_effect = [
        "2",  # Import metadata and measurement
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
        if "completer" in kwargs and len(kwargs["completer"].completer.words) > 0:
            response = random.choice(kwargs["completer"].completer.words)
        else:
            response = random.choice(FALLBACK_RESPONSES)
        print(f"Response: {response}")

    return response


def clr_prompt_patch(*args, **kwargs):
    prompt = args[0]
    # FormattedText is a list of (style, text) tuples
    if isinstance(prompt, FormattedText):
        prompt = prompt[0][1]
    print(f"Prompt: {prompt}")

    if "Please type level of" in prompt:
        response = str(random.randint(0, 10000))
        print(f"Response: {response}")
        return response
    else:
        response = random.choice(FALLBACK_RESPONSES)
        print(f"Response: {response}")

        return response


def processor_prompt_patch(*args, **kwargs):
    prompt = args[0]
    print(f"Prompt: {prompt}")

    response = str(random.randint(1, 3))
    print(f"Response: {response}")

    return response


@pytest.mark.postgres
class TestEndToEndAutomaton:
    """
    These tests use an 'automaton' to do end-to-end testing of the import command-line interface.
    This automaton gives reasonable answers to each question asked by the command-line resolver:
    either choosing from the list, where a list or auto-completion list is given, or giving one of a
    predefined set of answers.

    This means, whenever the test is run, the interface is 'exercised' with a load of potential
    interactions, which can flush out various bugs. The tests use randomness in choosing which
    answers to give, so are run ten times each to get a reasonable coverage, and I have implemented
    tests for importing a REP file and a Nisida file. If the test fails then the output that will be
    shown includes the random seed used to run the test, so it can be recreated for testing
    purposes. A lot of the interactions 'go round in circles' a bit, as it gives invalid input, so
    the question is asked again, and again, until it randomly picks a valid input. Still, that is a
    good test of our invalid input handling code! Basically, if the CLI can deal with this automaton
    hammering it with crazy stuff, then it should be able to deal with a real human operating it
    sensibly!

    This is a relatively naive automaton at the moment, and doesn't do absolutely everything that is
    possible in the GUI, but it has already brought a number of bugs to my attention. These bugs are
    mostly around checking input from the user more carefully to deal with empty input, input that
    is too long, input that isn't properly parsed etc. The actual results of the import are not
    checked: if the CLI doesn't fail with an exception then the test passes.

    **Note:** There is a possibility that these tests will randomly fail when *something else* in the
    repo has been changed. This does not mean that your other change caused these tests to fail: it could
    be just the randomness in the automaton finding a bug that hasn't been found before.
    """

    def setup_method(self, test_method):
        self.postgres = None
        self.store = None
        try:
            self.postgres = Postgresql(
                database="test",
                host="localhost",
                user="postgres",
                password="postgres",
                port=55527,
            )
        except RuntimeError:
            raise Exception("Testing Postgres server could not be started/accessed")
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
            raise Exception("Creating database schema in testing Postgres database failed")
        with self.store.session_scope():
            self.store.populate_reference()

    def teardown_method(self):
        try:
            self.postgres.stop()
        except AttributeError:
            return

    @pytest.mark.automaton
    @patch("pepys_import.file.file_processor.prompt", new=processor_prompt_patch)
    @patch("pepys_import.resolvers.command_line_resolver.create_menu", new=create_menu_patch)
    @patch("pepys_import.resolvers.command_line_resolver.prompt", new=clr_prompt_patch)
    @pytest.mark.parametrize("execution_number", range(10))  # Used to just repeat the test 5 times
    @patch("pepys_import.core.store.common_db.prompt", return_value="2")
    def test_automaton_load_rep1(self, patched_prompt, execution_number):
        seed = random.randint(0, 10000)
        print("---- Starting end-to-end automaton test")
        print(f"Running with seed = {seed}")

        # Replace this line with the seed printed out by a previous run of the test to duplicate that test
        random.seed(seed)

        processor = FileProcessor(archive=False)
        processor.register_importer(ReplayImporter())

        processor.process(
            os.path.join(DATA_PATH, "track_files", "rep_data", "rep_test1.rep"),
            self.store,
            False,
        )
        print("---- End of end-to-end autmaton test")

    @pytest.mark.automaton
    @patch("pepys_import.file.file_processor.prompt", new=processor_prompt_patch)
    @patch("pepys_import.resolvers.command_line_resolver.create_menu", new=create_menu_patch)
    @patch("pepys_import.resolvers.command_line_resolver.prompt", new=clr_prompt_patch)
    @pytest.mark.parametrize("execution_number", range(10))  # Used to just repeat the test 5 times
    def test_automaton_load_nisida(self, execution_number):
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
