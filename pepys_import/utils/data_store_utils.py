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


def is_schema_created(engine, db_type):
    """Returns True if Pepys Tables are created, False otherwise."""
    inspector = inspect(engine)
    if db_type == "sqlite":
        table_names = inspector.get_table_names()
        number_of_tables = 72 if platform.system() == "Windows" else 70
    else:
        table_names = inspector.get_table_names(schema="pepys")
        number_of_tables = 34

    if len(table_names) != number_of_tables:
        print(f"Database tables are not found! (Hint: Did you initialise the DataStore?)")
        return False
    return True


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
