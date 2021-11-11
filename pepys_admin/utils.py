import json
import os
import sqlite3
import sys
from contextlib import contextmanager

import pint
from sqlalchemy.sql.schema import UniqueConstraint

from paths import MIGRATIONS_DIRECTORY
from pepys_import.utils.sqlalchemy_utils import get_primary_key_for_table
from pepys_import.utils.text_formatting_utils import (
    custom_print_formatted_text,
    format_error_message,
)


def get_default_export_folder():
    current_folder_name = os.path.basename(os.path.normpath(os.getcwd()))
    if current_folder_name == "bin":
        return os.path.expanduser("~")
    else:
        return os.getcwd()


def round_object_if_necessary(obj):
    if isinstance(obj, pint.quantity._Quantity) or isinstance(obj, float):
        return round(obj, 3)
    else:
        return obj


def sqlalchemy_obj_to_dict(obj, remove_id=False):
    """Converts a SQLAlchemy result from a query into a dict of {column_name: value}s,
    excluding the 'created_date' column.

    This is used for tests. To make the tests work on machines that round floats differently,
    we round the objects if necessary before putting them in the dict. This deals with
    issues we have if we have a Quantity with a value of 5.0000000024 from Postgres
    and a value of 5.0000 on SQLite.
    """
    d = {
        column.name: round_object_if_necessary(getattr(obj, column.name))
        for column in obj.__table__.columns
    }

    del d["created_date"]

    if remove_id:
        pri_key_col_name = get_primary_key_for_table(obj)
        del d[pri_key_col_name]

    return d


def check_sqlalchemy_results_are_equal(results1, results2):
    """Compare two lists of SQLAlchemy results to see if they are equal"""
    list1 = [sqlalchemy_obj_to_dict(item) for item in results1]
    list2 = [sqlalchemy_obj_to_dict(item) for item in results2]

    return list1 == list2


def make_query_for_cols(table_object, comparison_object, columns, session):
    """Create a SQLAlchemy query for the given table_object, with a filter comparing the given
    columns with the given comparison_object.

    For example, if the comparison object contains values
    {'name': GPS, 'host': 42, 'type':12, 'blah': 'hello},
    and the columns are ['name', 'host']
    then this will return a query like this:

    session.query(table_object).filter(table_object.name == "GPS").filter(table_object.host == 42)
    """
    query = session.query(table_object)

    for col_name in columns:
        query = query.filter(
            getattr(table_object, col_name) == getattr(comparison_object, col_name)
        )

    return query


def make_query_for_unique_cols_or_all(table_object, comparison_object, session):
    """Create a SQLAlchemy query object for the given table_object, with a filter comparing it
    to the comparison object. The filter will use just the columns defined in the unique constraint
    for the table if a unique constraint is defined, otherwise it will compare all columns.
    """
    unique_constraints = [
        c for c in table_object.__table__.constraints if isinstance(c, UniqueConstraint)
    ]

    if len(unique_constraints) == 0:
        return make_query_for_all_data_columns(table_object, comparison_object, session)
    elif len(unique_constraints) == 1:
        unique_col_names = [c.name for c in unique_constraints[0].columns]
        return make_query_for_cols(table_object, comparison_object, unique_col_names, session)


def make_query_for_all_data_columns(table_object, comparison_object, session):
    """Makes a query to search for an object where all data columns match the comparison object

    In this case, the data columns are all columns excluding the primary key and the
    created_date column.
    """
    primary_key = get_primary_key_for_table(table_object)

    column_names = [col.name for col in table_object.__table__.columns.values()]

    # Get rid of the primary key column from the list
    column_names.remove(primary_key)
    # And get rid of the created_date column
    column_names.remove("created_date")
    # And get rid of the privacy column, if it exists
    if "privacy_id" in column_names:
        column_names.remove("privacy_id")

    query = session.query(table_object)

    for col_name in column_names:
        # Don't add a filter to match any columns which have missing values in the comparison object
        if getattr(comparison_object, col_name) is None:
            continue
        query = query.filter(
            getattr(table_object, col_name) == getattr(comparison_object, col_name)
        )

    return query


def get_name_for_obj(obj):
    """Return a 'name' field for an object. Most objects have a field called `name`, so we try this first.
    If this fails, we try `reference` (for Datafiles) and `synonym` (for Synonyms), otherwise we just return
    'Unknown'.
    """
    if "name" in obj.__dict__:
        return obj.name
    elif "reference" in obj.__dict__:
        return obj.reference
    elif "synonym" in obj.__dict__:
        return obj.synonym
    else:
        return "Unknown"


def statistics_to_table_data(statistics):
    """Convert a dictionary of statistics data into tuples ready for displaying as a table with the tabulate function."""
    return [
        (k, v["already_there"], v["added"], v["modified"]) for k, v in sorted(statistics.items())
    ]


def print_names_added(names):
    """Print the list of names of items added in a sensible format"""
    if len(names) == 0:
        print("No entries added")
    else:
        print("\nEntries added:")

    for table_name, names in sorted(names.items()):
        print(f"- {table_name}")
        for name in names:
            print(f"  - {name}")


def create_statistics_from_ids(ids):
    """Create a statistics dictionary from a dict of ids/details for items added, modified and already_there"""
    return {
        "added": len(ids["added"]),
        "modified": len([item for item in ids["modified"] if item["data_changed"]]),
        "already_there": len(ids["already_there"]),
    }


def database_at_latest_revision(db_path):
    try:
        conn = sqlite3.connect(db_path)
        result = conn.execute("SELECT version_num from alembic_version;")
        slave_version = next(result)[0]
        conn.close()
    except Exception:
        custom_print_formatted_text(
            format_error_message(
                "Could not read schema revision from database - is this a valid Pepys database file?"
            )
        )
        return False

    versions = read_latest_revisions_file()

    if slave_version == versions["LATEST_SQLITE_VERSION"]:
        return True
    else:
        return False


def read_latest_revisions_file():
    try:
        with open(os.path.join(MIGRATIONS_DIRECTORY, "latest_revisions.json"), "r") as file:
            versions = json.load(file)
    except Exception:
        custom_print_formatted_text(format_error_message("Could not find latest_revisions.json"))
        return {}

    if "LATEST_SQLITE_VERSION" not in versions:
        custom_print_formatted_text(
            format_error_message("Latest revision IDs couldn't found from latest_revisions.json")
        )
        return {}
    return versions


class StdoutAndFileWriter:
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, "a")

    # Pretend not to be a terminal
    def isatty(self):
        return False

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def close(self):
        self.log.close()

    def flush(self):
        # this flush method is needed for python 3 compatibility.
        # this handles the flush command by doing nothing.
        # you might want to specify some extra behavior here.
        pass


@contextmanager
def redirect_stdout_to_file_and_screen(filename):
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = StdoutAndFileWriter(filename)
    sys.stderr = sys.stdout

    yield

    sys.stdout.close()
    sys.stdout = old_stdout
    sys.stderr = old_stderr
