import argparse
import os

from config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_TYPE, DB_USERNAME
from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor
from pepys_import.resolvers.command_line_resolver import CommandLineResolver
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
    validation_help = "Skip the validation steps"
    parser.add_argument("--path", help=path_help, required=False, default=DIRECTORY_PATH)
    parser.add_argument(
        "--archive",
        dest="archive",
        help=archive_help,
        action="store_true",
        default=False,
    )
    parser.add_argument("--db", help=db_help, required=False, default=None)
    parser.add_argument("--resolver", help=resolver_help, required=False, default="command-line")
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
    )


def process(
    path=DIRECTORY_PATH, archive=False, db=None, resolver="command-line", skip_validation=None
):
    if resolver == "command-line":
        resolver_obj = CommandLineResolver()
    elif resolver == "default":
        resolver_obj = DefaultResolver()
    else:
        print(f"Invalid option '{resolver}' for --resolver.")
        return

    if db is None:
        data_store = DataStore(
            db_username=DB_USERNAME,
            db_password=DB_PASSWORD,
            db_host=DB_HOST,
            db_port=DB_PORT,
            db_name=DB_NAME,
            db_type=DB_TYPE,
            missing_data_resolver=resolver_obj,
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
        )
    if not is_schema_created(data_store.engine, data_store.db_type):
        data_store.initialise()
    with data_store.session_scope():
        if data_store.is_empty():
            data_store.populate_reference()

    processor = FileProcessor(archive=archive, skip_validation=skip_validation)
    processor.load_importers_dynamically()

    with handle_database_errors():
        processor.process(path, data_store, True)


if __name__ == "__main__":
    main()
