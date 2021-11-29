import argparse
import os
from importlib import reload

from prompt_toolkit import prompt
from sqlalchemy.inspection import inspect

import config
from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor
from pepys_import.resolvers.command_line_resolver import CommandLineResolver
from pepys_import.resolvers.default_resolver import DefaultResolver
from pepys_import.utils.data_store_utils import is_schema_created
from pepys_import.utils.error_handling import handle_database_errors
from pepys_import.utils.text_formatting_utils import (
    custom_print_formatted_text,
    format_command,
    format_error_message,
)

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
    validation_help = "Skip the validation steps"
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

    parser.add_argument(
        "--skip-validation",
        help=validation_help,
        required=False,
        action="store_true",
        default=False,
    )
    args = parser.parse_args()
    process(
        path=args.path,
        archive=args.archive,
        db=args.db,
        resolver=args.resolver,
        skip_validation=args.skip_validation,
        training=args.training,
    )


def process(
    path=DIRECTORY_PATH,
    archive=False,
    db=None,
    resolver="command-line",
    training=False,
    skip_validation=None,
):
    if resolver == "command-line":
        resolver_obj = CommandLineResolver()
    elif resolver == "default":
        resolver_obj = DefaultResolver()
    else:
        custom_print_formatted_text(
            format_error_message(f"Invalid option '{resolver}' for --resolver.")
        )
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
            error_on_db_version_mismatch=True,
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
            error_on_db_version_mismatch=True,
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
            error_on_db_version_mismatch=True,
        )
    if not is_schema_created(data_store.engine, data_store.db_type):
        # The number of tables don't match the expected number of tables, so check
        # whether the number of tables is actually zero. If so, initialise, if not
        # then stop and give error.
        inspector = inspect(data_store.engine)
        table_names = inspector.get_table_names()
        if len(table_names) == 0:
            data_store.initialise()
        else:
            print(
                f"The number of tables in the database ({len(table_names)}) does not match the expected number of tables.\n"
                "Please run database migration."
            )
    with data_store.session_scope():
        if data_store.is_empty():
            data_store.populate_reference()
            data_store.populate_metadata()

    processor = FileProcessor(
        archive=archive,
        skip_validation=skip_validation,
        archive_path=config.ARCHIVE_PATH,
        local_parsers=config.LOCAL_PARSERS,
    )
    processor.load_importers_dynamically()

    try:
        with handle_database_errors():
            processor.process(path, data_store, True)
    except SystemExit:
        pass

    if training:
        answer = prompt(format_command("Would you like to reset the training database? (y/N) "))
        if answer.upper() == "Y":
            if os.path.exists(config.DB_NAME):
                os.remove(config.DB_NAME)


def set_up_training_mode():
    training_data_folder = os.path.expanduser(os.path.join("~", "Pepys_Training_Data"))
    # Training database will be located in user's home folder
    db_path = os.path.join(training_data_folder, "pepys_training_database.db")

    print("#" * 80)
    print(" " * 28 + "Running in Training Mode" + " " * 28)
    print("")
    print("Changes are only made to a local training database (see full path below)")
    print("#" * 80)

    if os.path.exists(db_path):
        # Training db already exists, ask if we want to clear it
        answer = prompt(format_command("Would you like to reset the training database? (y/N) "))
        if answer.upper() == "Y":
            os.remove(db_path)

    if not os.path.exists(training_data_folder):
        os.mkdir(training_data_folder)

    config_file_path = os.path.join(training_data_folder, "pepys_training_config.ini")

    archive_folder = os.path.join(training_data_folder, "output")

    config_contents = f"""[database]
database_username =
database_password =
database_host =
database_port = 0
database_name = {db_path}
database_type = sqlite

[archive]
path = {archive_folder}"""

    with open(config_file_path, "w") as f:
        f.write(config_contents)

    os.environ["PEPYS_CONFIG_FILE"] = config_file_path

    # If the database doesn't already exist, then import some example data
    # if not os.path.exists(db_path):


if __name__ == "__main__":
    main()
