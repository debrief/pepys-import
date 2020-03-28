import argparse
import os

from config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_TYPE, DB_USERNAME
from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor

FILE_PATH = os.path.abspath(__file__)
DIRECTORY_PATH = os.path.dirname(FILE_PATH)
DEFAULT_DATABASE = ":memory:"


def main():
    # Parse arguments
    parser = argparse.ArgumentParser()
    path_help = "The path to import data from (The default value is the directory of the script)"
    archive_help = " Instruction to archive (move) imported files to designated archive folder"
    db_help = "SQLite database file to use (overrides config file database settings). Use `:memory:` for temporary in-memory instance"
    parser.add_argument("--path", help=path_help, required=False, default=DIRECTORY_PATH)
    parser.add_argument(
        "--archive", dest="archive", help=archive_help, action="store_true", default=False,
    )
    parser.add_argument("--db", help=db_help, required=False, default=None)
    args = parser.parse_args()
    process(path=args.path, archive=args.archive, db=args.db)


def process(path=DIRECTORY_PATH, archive=False, db=None):
    if db is None:
        data_store = DataStore(
            db_username=DB_USERNAME,
            db_password=DB_PASSWORD,
            db_host=DB_HOST,
            db_port=DB_PORT,
            db_name=DB_NAME,
            db_type=DB_TYPE,
        )
    else:
        data_store = DataStore(
            db_username="", db_password="", db_host="", db_port=0, db_name=db, db_type="sqlite"
        )

    data_store.initialise()

    processor = FileProcessor(archive=archive)
    processor.load_importers_dynamically()
    processor.process(path, data_store, True)


if __name__ == "__main__":
    main()
