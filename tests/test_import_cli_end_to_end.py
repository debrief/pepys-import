import os
import random
from unittest.mock import patch

from hypothesis import example, given, settings
from hypothesis.strategies import characters, data, floats, from_regex, integers, just, one_of, text

from importers.replay_importer import ReplayImporter
from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor
from pepys_import.resolvers.command_line_resolver import CommandLineResolver

FILE_PATH = os.path.dirname(__file__)
DATA_PATH = os.path.join(FILE_PATH, "sample_data")


@given(data())
def test_example(data):
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
                response = data.draw(text(characters(blacklist_categories="C"), min_size=1))
            print(f"Response: {response}")

        return response

    def input_patch(*args):
        print("Input with prompt: {args}")
        return "Hello"

    def clr_prompt_patch(*args, **kwargs):
        prompt = args[0]
        print(f"Prompt: {prompt}")

        response = data.draw(text(characters(blacklist_categories="C"), min_size=1))
        print(f"Response: {response}")

        return response

    with patch("pepys_import.resolvers.command_line_resolver.create_menu", new=create_menu_patch):
        with patch("pepys_import.resolvers.command_line_resolver.prompt", new=clr_prompt_patch):
            with patch("pepys_import.resolvers.command_line_resolver.input", new=input_patch):
                data_store = DataStore(
                    "",
                    "",
                    "",
                    0,
                    ":memory:",
                    db_type="sqlite",
                    missing_data_resolver=CommandLineResolver(),
                )
                data_store.initialise()
                with data_store.session_scope():
                    data_store.populate_reference()

                processor = FileProcessor(archive=False)
                processor.register_importer(ReplayImporter())

                processor.process(
                    os.path.join(DATA_PATH, "track_files", "rep_data", "rep_test1.rep"),
                    data_store,
                    False,
                )
