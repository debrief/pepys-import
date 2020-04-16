import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config
# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
from sqlalchemy.event import listen

sys.path.append(".")
from config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_TYPE, DB_USERNAME
from pepys_import.core.store import postgres_db, sqlite_db
from pepys_import.core.store.db_base import BasePostGIS, BaseSpatiaLite
from pepys_import.utils.data_store_utils import (
    create_spatialite_tables_for_postgres,
    create_spatialite_tables_for_sqlite,
    is_schema_created,
)
from pepys_import.utils.geoalchemy_utils import load_spatialite


config = context.config

driver = "sqlite"
if DB_TYPE == "postgres":
    driver = "postgresql+psycopg2"
elif DB_TYPE == "sqlite":
    driver = "sqlite+pysqlite"
connection_string = "{}://{}:{}@{}:{}/{}".format(
    driver, DB_USERNAME, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
)
config.set_main_option("sqlalchemy.url", connection_string)
# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = BaseSpatiaLite.metadata if DB_TYPE == "sqlite" else BasePostGIS.metadata


def exclude_tables_from_config(config_):
    tables_ = config_.get("tables", None)
    if tables_ is not None:
        tables = tables_.split(",")
    return tables


exclude_tables = exclude_tables_from_config(config.get_section("alembic:exclude"))


def include_object(object_, name, type_, reflected, compare_to):
    if type_ == "table" and name in exclude_tables:
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
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    engine = engine_from_config(
        config.get_section(config.config_ini_section), prefix="sqlalchemy.",
    )
    if DB_TYPE == "sqlite":
        listen(engine, "connect", load_spatialite)
    with engine.connect() as connection:
        if not is_schema_created(engine, DB_TYPE):
            if DB_TYPE == "sqlite":
                create_spatialite_tables_for_sqlite(engine)
            elif DB_TYPE == "postgres":
                create_spatialite_tables_for_postgres(engine)
        context.configure(
            connection=connection, target_metadata=target_metadata, include_object=include_object
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
