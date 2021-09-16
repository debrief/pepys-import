from sqlalchemy import MetaData
from sqlalchemy.orm import declarative_base

# SQLite allows constraints to exist in the database that have no identifying name. This unnamed
# constraints create problems for migration. Therefore, naming_convention is passed to declarative
# base of SQLite:
# https://docs.sqlalchemy.org/en/13/core/constraints.html#configuring-constraint-naming-conventions
postgres_naming_convention = {
    "ix": "ix_%(column_0_N_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

sqlite_naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
meta_sqlite = MetaData(naming_convention=sqlite_naming_convention)
meta_postgres = MetaData(naming_convention=postgres_naming_convention, schema="pepys")
# define this as the base for all the DB tables here in a common module
BasePostGIS = declarative_base(metadata=meta_postgres)
BaseSpatiaLite = declarative_base(metadata=meta_sqlite)
