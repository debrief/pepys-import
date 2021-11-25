import csv
import json
import os
import sys
import uuid
from inspect import getfullargspec
from math import ceil

import sqlalchemy
from sqlalchemy import func, inspect, select
from sqlalchemy.sql.expression import text

from paths import MIGRATIONS_DIRECTORY, PEPYS_IMPORT_DIRECTORY
from pepys_import.resolvers.command_line_input import create_menu
from pepys_import.utils.sqlalchemy_utils import get_primary_key_for_table
from pepys_import.utils.table_name_utils import table_name_to_class_name
from pepys_import.utils.text_formatting_utils import (
    custom_print_formatted_text,
    format_error_message,
)

STORED_PROC_PATH = os.path.join(PEPYS_IMPORT_DIRECTORY, "database", "postgres_stored_procedures")


def import_from_csv(data_store, path, files, change_id):
    for file in sorted(files):
        # split file into filename and extension
        table_name, _ = os.path.splitext(file)
        if table_name.lower() == "synonyms":
            import_synonyms(data_store, os.path.join(path, file), change_id)
            continue
        possible_method = "add_to_" + table_name.lower().replace(" ", "_")
        method_to_call = getattr(data_store, possible_method, None)
        if method_to_call:
            # Get all arguments of the method, except the first argument which is 'self'
            arguments = getfullargspec(method_to_call).args[1:]
            possible_arguments = ",".join(arguments)
            with open(os.path.join(path, file), "r") as file_object:
                reader = csv.reader(file_object)
                # extract header
                header = next(reader)
                if not set(header).issubset(set(arguments)):
                    custom_print_formatted_text(
                        format_error_message(
                            f"Headers and the arguments of DataStore.{possible_method}() don't match!"
                            f"\nPossible arguments: {possible_arguments}"
                            f"\nPlease check your CSV file."
                        )
                    )
                    return
                for row_number, row in enumerate(reader):
                    row_as_string = "".join(row).strip()
                    if row_as_string == "":
                        continue
                    keyword_arguments = dict(zip(header, row))
                    try:
                        method_to_call(**keyword_arguments, change_id=change_id)
                    except Exception as e:
                        custom_print_formatted_text(
                            format_error_message(f"Error importing row {row} from {file}")
                        )
                        custom_print_formatted_text(format_error_message(f"  Error was '{str(e)}'"))
        else:
            custom_print_formatted_text(
                format_error_message(f"Method({possible_method}) not found!")
            )


def import_synonyms(data_store, filepath, change_id):
    with open(filepath, "r") as file_object:
        reader = csv.reader(file_object)
        # extract header
        header = next(reader)
        if not set(header).issubset({"synonym", "table", "target_name"}):
            custom_print_formatted_text(
                format_error_message(
                    "Headers of the Synonyms.csv file are wrong or missing!"
                    "\nNecessary arguments: synonym,table,target_name"
                    "\nPlease check your CSV file."
                )
            )
            return
        # For every row in the CSV
        for row in reader:
            row_as_string = "".join(row).strip()
            if row_as_string == "":
                continue

            values = dict(zip(header, row))

            # Search in the given table for the name
            class_name = table_name_to_class_name(values["table"])

            try:
                db_class = getattr(data_store.db_classes, class_name)
                pri_key_column_name = db_class.__table__.primary_key.columns.values()[0].name
            except AttributeError:
                custom_print_formatted_text(format_error_message(f"Error on row {row}"))
                custom_print_formatted_text(
                    format_error_message(f"  Invalid table name {values['table']}")
                )
                continue

            # Try and find a name column to use
            possibilities = ["name", "reference"]

            name_col = None
            for poss in possibilities:
                try:
                    name_col = getattr(db_class, poss)
                except AttributeError:
                    continue

            if name_col is None:
                custom_print_formatted_text(format_error_message(f"Error on row {row}"))
                custom_print_formatted_text(
                    format_error_message(f"  Cannot find name column for table {values['table']}")
                )
                continue

            results = (
                data_store.session.query(db_class).filter(name_col == values["target_name"]).all()
            )

            if len(results) == 0:
                # Nothing to link synonym to so give error
                custom_print_formatted_text(format_error_message(f"Error on row {row}"))
                custom_print_formatted_text(
                    format_error_message(
                        f"  Name '{values['target_name']}' is not found in table {values['table']}"
                    )
                )
                continue
            elif len(results) == 1:
                guid = getattr(results[0], pri_key_column_name)
                # Found one entry, so can create synonym
                data_store.add_to_synonyms(values["table"], values["synonym"], guid, change_id)
            elif len(results) > 1:
                if values["table"] != "Platforms":
                    custom_print_formatted_text(format_error_message(f"Error on row {row}"))
                    custom_print_formatted_text(
                        format_error_message(
                            f"  Name '{values['target_name']}' occurs multiple times in table {values['table']}."
                            f" Asking user to resolve is only supported for Platforms table."
                        )
                    )
                    continue

                results = sorted(results, key=lambda x: x.identifier)
                chosen_item = ask_user_for_synonym_link(data_store, results, values)

                if chosen_item is None:
                    print("Skipping row")
                    continue
                else:
                    guid = getattr(chosen_item, pri_key_column_name)
                    data_store.add_to_synonyms(values["table"], values["synonym"], guid, change_id)


def ask_user_for_synonym_link(data_store, results, values):
    options = [
        f"{result.name} / {result.identifier} / {result.nationality_name}" for result in results
    ]

    options += ["Skip this row"]

    def is_valid(option):  # pragma: no cover
        return option.lower() in [str(i) for i in range(1, len(options) + 1)] or option == "."

    choice = create_menu(
        f"Choose which Platform to link synonym '{values['target_name']}'' to:",
        options,
        validate_method=is_valid,
    )

    if choice == ".":
        print("Quitting")
        sys.exit(1)
    elif choice == str(len(options)):
        return None
    elif choice in [str(i) for i in range(1, len(options) + 1)]:
        return results[int(choice) - 1]


def is_schema_created(engine, db_type):
    """Returns True if Pepys Tables are created, False otherwise."""
    inspector = inspect(engine)
    if db_type == "sqlite":
        table_names = inspector.get_table_names()
        # SQLite table numbers vary by mod_spatialite. The version of mod_spatialiate
        # that is installed can vary by platform - so both numbers should be acceptable.
        if len(table_names) >= 77 and len(table_names) <= 79:
            return True
    else:
        table_names = inspector.get_table_names(schema="pepys")
        if len(table_names) == 41:
            return True

    if len(table_names) == 0:
        message = "Database tables are not found! (Hint: Did you initialise the DataStore?)"
    else:
        message = "Please run database migration to bring tables up to date."
    custom_print_formatted_text(format_error_message(message))
    return False


def create_spatial_tables_for_sqlite(engine):
    """Create geometry_columns and spatial_ref_sys metadata table"""

    if not inspect(engine).has_table("spatial_ref_sys"):
        with engine.begin() as connection:
            connection.execute(select(func.InitSpatialMetaData(1)))


def create_spatial_tables_for_postgres(engine):
    """Create schema pepys and extension for PostGIS"""
    query = """
        CREATE SCHEMA IF NOT EXISTS pepys;
        CREATE EXTENSION IF NOT EXISTS postgis;
        SET search_path = pepys,public;
    """
    with engine.begin() as connection:
        connection.execute(text(query))


def create_stored_procedures_for_postgres(engine):
    stored_procedure_files = [
        os.path.join(STORED_PROC_PATH, "dashboard_metadata.sql"),
        os.path.join(STORED_PROC_PATH, "dashboard_stats.sql"),
        os.path.join(STORED_PROC_PATH, "Comments_for.sql"),
        os.path.join(STORED_PROC_PATH, "Contacts_for.sql"),
        os.path.join(STORED_PROC_PATH, "Datafiles_for.sql"),
        os.path.join(STORED_PROC_PATH, "States_for.sql"),
    ]

    with engine.begin() as connection:
        for filename in stored_procedure_files:
            with open(filename) as f:
                procedure_definition = f.read()
            connection.execute(text(procedure_definition))


def create_alembic_version_table(engine, db_type):
    with open(os.path.join(MIGRATIONS_DIRECTORY, "latest_revisions.json"), "r") as file:
        versions = json.load(file)
    if "LATEST_POSTGRES_VERSION" not in versions or "LATEST_SQLITE_VERSION" not in versions:
        custom_print_formatted_text(format_error_message("Latest revision IDs couldn't found!"))
        return

    if db_type == "sqlite":
        # Try and get all entries from alembic_version table
        try:
            with engine.begin() as connection:
                table_contents = connection.execute(
                    text("SELECT * from alembic_version;")
                ).fetchall()

                if len(table_contents) == 0:
                    # Table exists but no version number row, so stamp it:
                    sql = "INSERT INTO alembic_version (version_num) VALUES (:id)"
                    connection.execute(text(sql), {"id": versions["LATEST_SQLITE_VERSION"]})
                if len(table_contents) == 1:
                    if table_contents[0][0] == versions["LATEST_SQLITE_VERSION"]:
                        # Current version already stamped in table - so just continue
                        print(
                            "Initialising database - alembic version in database matches latest version."
                        )
                    else:
                        # The version in the database doesn't match the current version - so raise an error
                        raise ValueError(
                            f"Database revision in alembic_version table ({table_contents[0][0]}) does not match latest revision ({versions['LATEST_SQLITE_VERSION']})."
                            "Please run database migration."
                        )
                if len(table_contents) > 1:
                    raise ValueError(
                        "Multiple rows detected in alembic_version table. Database potentially in inconsistent state."
                        "Migration functionality will not work. Please contact support."
                    )
        except sqlalchemy.exc.OperationalError:
            with engine.begin() as connection:
                # Error running select, so table doesn't exist - create it and stamp the current version
                connection.execute(
                    text(
                        """
                    CREATE TABLE IF NOT EXISTS alembic_version
                    (
                        version_num VARCHAR(32) NOT NULL,
                        CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                    );
                """
                    )
                )
                sql = "INSERT INTO alembic_version (version_num) VALUES (:id)"
                connection.execute(text(sql), {"id": versions["LATEST_SQLITE_VERSION"]})
    else:
        # Try and get all entries from alembic_version table
        try:
            with engine.begin() as connection:
                table_contents = connection.execute(
                    text("SELECT * from pepys.alembic_version;")
                ).fetchall()

                if len(table_contents) == 0:
                    # Table exists but no version number row, so stamp it:
                    sql = "INSERT INTO pepys.alembic_version (version_num) VALUES (:id)"
                    connection.execute(text(sql), {"id": versions["LATEST_POSTGRES_VERSION"]})
                if len(table_contents) == 1:
                    if table_contents[0][0] == versions["LATEST_POSTGRES_VERSION"]:
                        # Current version already stamped in table - so just continue
                        print(
                            "Initialising database - alembic version in database matches latest version."
                        )
                    else:
                        # The version in the database doesn't match the current version - so raise an error
                        raise ValueError(
                            f"Database revision in alembic_version table ({table_contents[0][0]}) does not match latest revision ({versions['LATEST_POSTGRES_VERSION']})."
                            "Please run database migration."
                        )
                if len(table_contents) > 1:
                    raise ValueError(
                        "Multiple rows detected in alembic_version table. Database potentially in inconsistent state."
                        "Migration functionality will not work. Please contact support."
                    )
        except (sqlalchemy.exc.OperationalError, sqlalchemy.exc.ProgrammingError):
            # Error running select, so table doesn't exist - create it and stamp the current version
            with engine.begin() as connection:
                connection.execute(
                    text(
                        """
                    CREATE TABLE IF NOT EXISTS pepys.alembic_version
                    (
                    version_num VARCHAR(32) NOT NULL,
                    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                    );
                """
                    )
                )
                sql = "INSERT INTO pepys.alembic_version (version_num) VALUES (:id)"
                connection.execute(text(sql), {"id": versions["LATEST_POSTGRES_VERSION"]})


def cache_results_if_not_none(cache_attribute):
    def real_decorator(f):
        def helper(self, name):
            cache = eval("self." + cache_attribute)
            if name not in cache:
                result = f(self, name)
                if result:
                    self.session.expunge(result)
                    cache[name] = result
                return result
            else:
                return cache[name]

        return helper

    return real_decorator


def shorten_uuid(id):  # pragma: no cover
    return str(id)[-6:]


class MissingDataException(Exception):
    pass


def lowercase_or_none(obj):
    if obj is None:
        return None
    else:
        return obj.lower()


def chunked_list(lst, size):
    """Split a list into multiple chunks of length size.
    Returns a list containing sublists of length size.

    If the list doesn't divide by size exactly, then the
    last sublist will have a length < size.
    """
    # Quick 'short-circuit' for a list less than size
    if len(lst) < size:
        return [lst]

    n_chunks = ceil(len(lst) / size)

    # We're returning a list containing lots of sublists
    # rather than yielding items as a generator
    # This is because we use a tqdm progress bar around this
    # function, and that needs to know the number of sublists
    # to be able to show a proper progress bar
    result = []

    for i in range(n_chunks):
        result.append(lst[i * size : (i + 1) * size])

    return result


def convert_edit_dict_columns(edit_dict, table_object):
    update_dict = {}
    # Convert the edit_dict we get from the GUI into a dict suitable for use in the update function
    # This involves converting any relationship columns into their ID column
    for col_name, new_value in edit_dict.items():
        attr_from_db_class = getattr(table_object, col_name)
        try:
            if isinstance(
                attr_from_db_class.prop, sqlalchemy.orm.relationships.RelationshipProperty
            ):
                local_column = list(attr_from_db_class.prop.local_columns)[0].key
                update_dict[local_column] = new_value
            else:
                update_dict[col_name] = new_value
        except Exception:
            update_dict[col_name] = new_value

    return update_dict


def convert_objects_to_ids(items, table_obj):
    if isinstance(items, list):
        new_id_list = []
        for value in items:
            if not isinstance(value, uuid.UUID):
                value = getattr(value, get_primary_key_for_table(table_obj))
            new_id_list.append(value)

        return new_id_list
    else:
        if not isinstance(items, uuid.UUID):
            value = getattr(items, get_primary_key_for_table(table_obj))
        else:
            value = items
        return value


def read_version_from_pepys_install(path):
    init_path = os.path.join(path, "pepys_import", "__init__.py")

    try:
        with open(init_path, "r") as f:
            for line in f:
                if "__version__" in line:
                    splitted = line.split("=")
                    # Remove whitespace, double-quotes and single-quotes from either end
                    version = splitted[1].strip().strip('"').strip("'")
                    return version
    except Exception:
        print(f"WARNING: Cannot read Pepys version from network master install at {path}")
        return None
