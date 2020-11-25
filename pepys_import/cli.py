import argparse
import os
from importlib import reload

from prompt_toolkit import prompt

import config
from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor
from pepys_import.resolvers.command_line_resolver import CommandLineResolver
from pepys_import.resolvers.command_line_input import format_command
from pepys_import.resolvers.default_resolver import DefaultResolver
from pepys_import.utils.data_store_utils import is_schema_created
from pepys_import.utils.error_handling import handle_database_errors

FILE_PATH = os.path.abspath(__file__)
DIRECTORY_PATH = os.path.dirname(FILE_PATH)
DEFAULT_DATABASE = ":memory:"


def main():  # pragma: no cover
    # Parse arguments
    parser = argparse.ArgumentParser()
    path_help = "The path to import data from (The default value is the directory of the script)"
    archive_help = " Instruction to archive (move) imported files to designated archive folder"
    db_help = (
        "SQLite database file to use (overrides config file database settings). "
        "Use `:memory:` for temporary in-memory instance"
    )
    resolver_help = (
        "Resolver to use for unknown entities. Valid values: 'default' (resolves "
        "using static default values), 'command-line' (resolves using interactive command-line interface, "
        "default option)"
    )
    training_help = (
        "Uses training mode, where all interactions take place with a training database located "
        "in the user's home folder. No actions will affect the database configured in the Pepys config file."
    )
    parser.add_argument("--path", help=path_help, required=False, default=DIRECTORY_PATH)
    parser.add_argument(
        "--archive",
        dest="archive",
        help=archive_help,
        action="store_true",
        default=False,
    )
    parser.add_argument("--resolver", help=resolver_help, required=False, default="command-line")

    # Make --training and --db mutually exclusive, as --training automatically specifies the db
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--training", help=training_help, dest="training", default=False, action="store_true"
    )
    group.add_argument("--db", help=db_help, required=False, default=None)

    args = parser.parse_args()

    process(
        path=args.path,
        archive=args.archive,
        db=args.db,
        resolver=args.resolver,
        training=args.training,
    )


def process(path=DIRECTORY_PATH, archive=False, db=None, resolver="command-line", training=False):
    if resolver == "command-line":
        resolver_obj = CommandLineResolver()
    elif resolver == "default":
        resolver_obj = DefaultResolver()
    else:
        print(f"Invalid option '{resolver}' for --resolver.")
        return

    if training:
        set_up_training_mode()

    # Reload the config file in case we're in a long-running process because of pytest and
    # the config file details have changed since the last test
    reload(config)

    if db is None:
        data_store = DataStore(
            db_username=config.DB_USERNAME,
            db_password=config.DB_PASSWORD,
            db_host=config.DB_HOST,
            db_port=config.DB_PORT,
            db_name=config.DB_NAME,
            db_type=config.DB_TYPE,
            missing_data_resolver=resolver_obj,
            training_mode=training,
        )
    elif type(db) is dict:
        data_store = DataStore(
            db_username=db["username"],
            db_password=db["password"],
            db_host=db["host"],
            db_port=db["port"],
            db_name=db["name"],
            db_type=db["type"],
            missing_data_resolver=resolver_obj,
            training_mode=training,
        )
    else:
        data_store = DataStore(
            db_username="",
            db_password="",
            db_host="",
            db_port=0,
            db_name=db,
            db_type="sqlite",
            missing_data_resolver=resolver_obj,
            training_mode=training,
        )
    if not is_schema_created(data_store.engine, data_store.db_type):
        data_store.initialise()
    with data_store.session_scope():
        if data_store.is_empty():
            data_store.populate_reference()

    processor = FileProcessor(archive=archive)
    processor.load_importers_dynamically()

    try:
        with handle_database_errors():
            processor.process(path, data_store, True)
    except SystemExit:
        pass

    if training:
        answer = prompt(format_command("Would you like to reset the training database? (y/n) "))
        if answer.upper() == "Y":
            if os.path.exists(config.DB_NAME):
                os.remove(config.DB_NAME)


def set_up_training_mode():
    # Training database will be located in user's home folder
    db_path = os.path.expanduser(os.path.join("~", "pepys_training_database.db"))

    if os.path.exists(db_path):
        # Training db already exists, ask if we want to clear it
        print("====================================================")
        print("              Running in training mode              ")
        print("====================================================")
        answer = prompt(format_command("Would you like to reset the training database? (y/n) "))
        if answer.upper() == "Y":
            os.remove(db_path)
        

    config_file_path = os.path.expanduser(os.path.join("~", "pepys_training_config.ini"))

    config_contents = f"""[database]
db_username =
db_password =
db_host =
db_port = 0
db_name = {db_path}
db_type = sqlite"""

    with open(config_file_path, "w") as f:
        f.write(config_contents)

    os.environ["PEPYS_CONFIG_FILE"] = config_file_path

    # If the database doesn't already exist, then import some example data
    # if not os.path.exists(db_path):


if __name__ == "__main__":
    main()
