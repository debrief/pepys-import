import os
import argparse

from pepys_import.file.file_processor import FileProcessor
from pepys_import.core.store.data_store import DataStore

FILE_PATH = os.path.abspath(__file__)
DIRECTORY_PATH = os.path.dirname(FILE_PATH)
DEFAULT_DATABASE = ":memory:"


def main(path=DIRECTORY_PATH, db=DEFAULT_DATABASE, archive=True):
    data_store = DataStore("", "", "", 0, db_name=db, db_type="sqlite")
    data_store.initialise()

    processor = FileProcessor(archive=archive)

    processor.load_importers_dynamically()

    processor.process(path, data_store, True)


if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser()
    path_help = "The path to import data from (The default value is the directory of the script)"
    db_help = "The database to connect to: (The is to use an in-memory database)"
    archive_help = "The flag to move files after the import (The default value is True)"
    parser.add_argument(
        "--path", help=path_help, required=False, default=DIRECTORY_PATH
    )
    parser.add_argument("--db", help=db_help, required=False, default=DEFAULT_DATABASE)
    parser.add_argument(
        "--archive", dest="archive", help=archive_help, action="store_true"
    )
    parser.add_argument(
        "--no-archive", dest="archive", help=archive_help, action="store_false"
    )
    parser.set_defaults(archive=True)
    args = parser.parse_args()
    main(path=args.path, db=args.db, archive=args.archive)
