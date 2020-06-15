import csv
import json
import os
import sys

from sqlalchemy import func, inspect, select

from paths import MIGRATIONS_DIRECTORY
from pepys_import.resolvers.command_line_input import create_menu
from pepys_import.utils.table_name_utils import table_name_to_class_name


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
            with open(os.path.join(path, file), "r") as file_object:
                reader = csv.reader(file_object)
                # extract header
                header = next(reader)
                for row_number, row in enumerate(reader):
                    keyword_arguments = dict(zip(header, row))
                    try:
                        method_to_call(**keyword_arguments, change_id=change_id)
                    except MissingDataException as e:
                        print(f"Error importing row {row} from {file}")
                        print(f"  Error was '{str(e)}'")
        else:
            print(f"Method({possible_method}) not found!")


def import_synonyms(data_store, filepath, change_id):
    with open(filepath, "r") as file_object:
        reader = csv.reader(file_object)
        # extract header
        header = next(reader)
        # For every row in the CSV
        for row in reader:
            values = dict(zip(header, row))

            # Search in the given table for the name
            class_name = table_name_to_class_name(values["table"])

            try:
                db_class = getattr(data_store.db_classes, class_name)
                pri_key_column_name = db_class.__table__.primary_key.columns.values()[0].name
            except AttributeError:
                print(f"Error on row {row}")
                print(f"  Invalid table name {values['table']}")
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
                print(f"Error on row {row}")
                print(f"  Cannot find name column for table {values['table']}")
                continue

            results = (
                data_store.session.query(db_class).filter(name_col == values["target_name"]).all()
            )

            if len(results) == 0:
                # Nothing to link synonym to so give error
                print(f"Error on row {row}")
                print(f"  Name '{values['target_name']}' is not found in table {values['table']}")
                continue
            elif len(results) == 1:
                guid = getattr(results[0], pri_key_column_name)
                # Found one entry, so can create synonym
                data_store.add_to_synonyms(values["table"], values["synonym"], guid, change_id)
            elif len(results) > 1:
                if values["table"] != "Platforms":
                    print(f"Error on row {row}")
                    print(
                        f"  Name '{values['target_name']}' occurs multiple times in table {values['table']}."
                        f" Asking user to resolve is only supported for Platforms table."
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
        f"{result.name}: Nationality = {result.nationality_name}, Identifier = {result.identifier}"
        for result in results
    ]

    options += ["Skip this row"]

    def is_valid(option):
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
        # SQLite can have either 73 tables (if on Windows, with the new version of mod_spatialite)
        # or 71 if on another platform (with the stable release of mod_spatialite)
        if len(table_names) == 73 or len(table_names) == 71:
            return True
        else:
            print(f"Database tables are not found! (Hint: Did you initialise the DataStore?)")
            return False
    else:
        table_names = inspector.get_table_names(schema="pepys")
        # We expect 35 tables on Postgres
        if len(table_names) == 35:
            return True
        else:
            print(f"Database tables are not found! (Hint: Did you initialise the DataStore?)")
            return False


def create_spatial_tables_for_sqlite(engine):
    """Create geometry_columns and spatial_ref_sys metadata table"""
    if not engine.dialect.has_table(engine, "spatial_ref_sys"):
        with engine.connect() as connection:
            connection.execute(select([func.InitSpatialMetaData(1)]))


def create_spatial_tables_for_postgres(engine):
    """Create schema pepys and extension for PostGIS"""
    query = """
        CREATE SCHEMA IF NOT EXISTS pepys;
        CREATE EXTENSION IF NOT EXISTS postgis;
        SET search_path = pepys,public;
    """
    with engine.connect() as connection:
        connection.execute(query)


def create_alembic_version_table(engine, db_type):
    with open(os.path.join(MIGRATIONS_DIRECTORY, "latest_revisions.json"), "r") as file:
        versions = json.load(file)
    if "LATEST_POSTGRES_VERSION" not in versions or "LATEST_SQLITE_VERSION" not in versions:
        print("Latest revision IDs couldn't found!")
        return

    if db_type == "sqlite":
        create_table = """
            CREATE TABLE IF NOT EXISTS alembic_version
            (
                version_num VARCHAR(32) NOT NULL,
                CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
            );
        """
        insert_value = """
            INSERT INTO alembic_version (version_num)
            SELECT '{id}'
            WHERE NOT EXISTS(SELECT 1 FROM alembic_version WHERE version_num = '{id}');
        """.format(
            id=versions["LATEST_SQLITE_VERSION"]
        )
    else:
        create_table = """
            CREATE TABLE IF NOT EXISTS pepys.alembic_version
            (
                version_num VARCHAR(32) NOT NULL,
                CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
            );
        """
        insert_value = """
            INSERT INTO pepys.alembic_version (version_num) 
            SELECT '{id}'
            WHERE NOT EXISTS(
                SELECT '{id}' FROM pepys.alembic_version WHERE version_num = '{id}'
            );
        """.format(
            id=versions["LATEST_POSTGRES_VERSION"]
        )
    with engine.connect() as connection:
        connection.execute(create_table)
        connection.execute(insert_value)


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


def shorten_uuid(id):
    return str(id)[-6:]


class MissingDataException(Exception):
    pass
