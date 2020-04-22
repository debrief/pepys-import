import csv
import os
import platform

from sqlalchemy import func, inspect, select


def import_from_csv(data_store, path, files, change_id):
    for file in sorted(files):
        # split file into filename and extension
        table_name, _ = os.path.splitext(file)
        possible_method = "add_to_" + table_name.lower().replace(" ", "_")
        method_to_call = getattr(data_store, possible_method, None)
        if method_to_call:
            with open(os.path.join(path, file), "r") as file_object:
                reader = csv.reader(file_object)
                # extract header
                header = next(reader)
                for row in reader:
                    keyword_arguments = dict(zip(header, row))
                    method_to_call(**keyword_arguments, change_id=change_id)
        else:
            print(f"Method({possible_method}) not found!")


def is_schema_created(self):
    """Returns True if Pepys Tables are created, False otherwise."""
    inspector = inspect(self.engine)
    if self.db_type == "sqlite":
        table_names = inspector.get_table_names()
        # SQLite can have either 72 tables (if on Windows, with the new version of mod_spatialite)
        # or 70 if on another platform (with the stable release of mod_spatialite)
        if len(table_names) == 72 or len(table_names) == 70:
            return True
        else:
            print(f"Database tables are not found! (Hint: Did you initialise the DataStore?)")
            return False
    else:
        table_names = inspector.get_table_names(schema="pepys")
        # We expect 34 tables on Postgres
        if len(table_names) == 34:
            return True
        else:
            print(f"Database tables are not found! (Hint: Did you initialise the DataStore?)")
            return False


def create_spatialite_tables_for_sqlite(engine):
    """Create geometry_columns and spatial_ref_sys metadata table"""
    if not engine.dialect.has_table(engine, "spatial_ref_sys"):
        with engine.connect() as conn:
            conn.execute(select([func.InitSpatialMetaData(1)]))


def create_spatialite_tables_for_postgres(engine):
    """Create schema pepys and extension for PostGIS"""
    query = """
        CREATE SCHEMA IF NOT EXISTS pepys;
        CREATE EXTENSION IF NOT EXISTS postgis;
        SET search_path = pepys,public;
    """
    with engine.connect() as conn:
        conn.execute(query)
