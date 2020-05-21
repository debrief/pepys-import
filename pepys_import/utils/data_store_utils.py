import csv
import os

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
            SELECT 'ccc37f794db6'
            WHERE NOT EXISTS(SELECT 1 FROM alembic_version WHERE version_num = 'ccc37f794db6');
        """
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
            SELECT 'e2f70908043d'
            WHERE NOT EXISTS(
                SELECT 'e2f70908043d' FROM pepys.alembic_version WHERE version_num = 'e2f70908043d'
            );
        """
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
