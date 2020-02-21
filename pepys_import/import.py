import os
import argparse

from pepys_import.file.file_processor import FileProcessor
from pepys_import.core.store.data_store import DataStore
from pepys_import.file.nmea_importer import NMEAImporter
from pepys_import.file.replay_importer import ReplayImporter

FILE_PATH = os.path.abspath(__file__)
DIRECTORY_PATH = os.path.dirname(FILE_PATH)
DEFAULT_DATABASE = ":memory:"


def main(path=DIRECTORY_PATH, db=DEFAULT_DATABASE):
    data_store = DataStore("", "", "", 0, db_name=db, db_type="sqlite")
    data_store.initialise()

    processor = FileProcessor("descending.db")
    processor.register_importer(ReplayImporter())
    processor.register_importer(NMEAImporter())
    processor.process(path, data_store, True)


if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser()
    path_help = "The path to import data from (The default value is the directory of the script)"
    db_help = "The database to connect to: (The is to use an in-memory database)"
    parser.add_argument(
        "--path", help=path_help, required=False, default=DIRECTORY_PATH
    )
    parser.add_argument("--db", help=db_help, required=False, default=DEFAULT_DATABASE)
    args = parser.parse_args()
    main(path=args.path, db=args.db)
