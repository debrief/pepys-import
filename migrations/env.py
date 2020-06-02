import os
from logging.config import fileConfig
from re import search

from alembic import context
from alembic.script import write_hooks
from sqlalchemy import engine_from_config
from sqlalchemy.event import listen

from config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_TYPE, DB_USERNAME
from pepys_import.core.store import (  # Don't remove, they are necessary for the discovery of changes!
    postgres_db,
    sqlite_db,
)
from pepys_import.core.store.db_base import BasePostGIS, BaseSpatiaLite
from pepys_import.utils.data_store_utils import (
    create_spatial_tables_for_postgres,
    create_spatial_tables_for_sqlite,
    is_schema_created,
)
from pepys_import.utils.sqlite_utils import load_spatialite

DIR_PATH = os.path.dirname(__file__)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
db_type = config.attributes.get("db_type", DB_TYPE)

version_path = os.path.join(DIR_PATH, "versions")
if db_type == "postgres":
    driver = "postgresql+psycopg2"
    version_path = os.path.join(DIR_PATH, "postgres_versions")
elif db_type == "sqlite":
    driver = "sqlite+pysqlite"
    version_path = os.path.join(DIR_PATH, "sqlite_versions")

context.script.version_locations = [version_path]
context.script.__dict__.pop("_version_locations", None)

connection_string = "{}://{}:{}@{}:{}/{}".format(
    driver, DB_USERNAME, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
)
config.set_main_option("sqlalchemy.url", connection_string)
# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = BaseSpatiaLite.metadata if db_type == "sqlite" else BasePostGIS.metadata


def exclude_tables_from_config(config_):
    tables_ = config_.get("tables", None)
    if tables_ is not None:
        tables = tables_.split(",")
    return tables


exclude_tables = exclude_tables_from_config(config.get_section("alembic:exclude"))


def include_object_postgres(object_, name, type_, reflected, compare_to):
    if type_ == "table" and (
        name in exclude_tables
        or name.startswith("idx_")
        or name.startswith("virts_")
        or "geometry_columns" in name
    ):
        return object_.schema == "pepys"
    elif type_ == "index" and name.startswith("idx_"):
        return False
    else:
        return True


def include_object_sqlite(object_, name, type_, reflected, compare_to):
    if type_ == "table" and (
        name in exclude_tables
        or name.startswith("idx_")
        or name.startswith("virts_")
        or "geometry_columns" in name
    ):
        return False
    else:
        return True


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    if db_type == "sqlite":
        context.configure(
            url=url,
            target_metadata=target_metadata,
            literal_binds=True,
            dialect_opts={"paramstyle": "named"},
            include_object=include_object_sqlite,
            render_as_batch=True,
            compare_type=True,
        )
    else:
        context.configure(
            url=url,
            target_metadata=target_metadata,
            literal_binds=True,
            dialect_opts={"paramstyle": "named"},
            version_table_schema="pepys",
            include_schemas=True,
            include_object=include_object_postgres,
            render_as_batch=True,
            compare_type=True,
        )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # This function prevents to create empty migration files when there is no change in the DB
    # Please check: https://alembic.sqlalchemy.org/en/latest/cookbook.html#don-t-generate-empty-migrations-with-autogenerate
    def process_revision_directives(context_, revision, directives):
        if config.cmd_opts.autogenerate:
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []

    connectable = config.attributes.get("connection", None)
    if connectable is None:
        # only create Engine if we don't have a Connection
        # from the outside
        connectable = engine_from_config(
            config.get_section(config.config_ini_section), prefix="sqlalchemy.",
        )
        if db_type == "sqlite":
            listen(connectable, "connect", load_spatialite)

    if not is_schema_created(connectable, db_type):
        print("Database tables are going to be created by Alembic.")
        if db_type == "sqlite":
            create_spatial_tables_for_sqlite(connectable)
        elif db_type == "postgres":
            create_spatial_tables_for_postgres(connectable)
    with connectable.connect() as connection:
        if db_type == "postgres":
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                version_table_schema="pepys",
                include_schemas=True,
                include_object=include_object_postgres,
                render_as_batch=True,
                process_revision_directives=process_revision_directives,
                compare_type=True,
            )
            with context.begin_transaction():
                context.execute("SET search_path TO pepys,public")
                context.run_migrations()
        else:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                include_object=include_object_sqlite,
                render_as_batch=True,
                process_revision_directives=process_revision_directives,
                compare_type=True,
            )
            with context.begin_transaction():
                context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()


@write_hooks.register("add_copy_from")
def add_copy_from(filename, options):
    qouted_name_regex = r"op\.batch_alter_table\(([\"'])((?:(?=(\\?)).)*?)\1"
    with open(filename) as file_:
        lines = file_.readlines()

    data = "\n".join(lines)
    if 'schema="pepys"' in data:
        lines.insert(10, "from pepys_import.core.store.postgres_db import *\n")
    else:
        lines.insert(10, "from pepys_import.core.store.sqlite_db import *\n")

    for index, line in enumerate(lines):
        match = search(qouted_name_regex, line)
        if match:
            table_name = match.group(2)
            # Table names are plural in the database, therefore make it singular
            if table_name in ["alembic_version", "HostedBy", "Media"]:
                table = table_name
            elif table_name == "Geometries":
                table = "Geometry1"
            elif table_name.endswith("ies"):
                table = table_name[:-3] + "y"
            else:
                table = table_name[:-1]
            argument = f", copy_from={table}.__table__"
            idx = line.index(") as batch_op:")
            lines[index] = line[:idx] + argument + line[idx:]

    with open(filename, "w") as to_write:
        to_write.writelines(lines)
