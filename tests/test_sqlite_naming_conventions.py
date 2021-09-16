import unittest

from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.sql.ddl import CreateTable

from pepys_import.core.store.postgres_db import Datafile as Datafile_pg
from pepys_import.core.store.postgres_db import DatafileType as Datafile_type_pg
from pepys_import.core.store.sqlite_db import Datafile, DatafileType


def test_constraint_names_sqlite():
    sql_script = str(CreateTable(Datafile.__table__).compile(dialect=sqlite.dialect()))
    assert "pk_Datafiles" in sql_script
    assert "fk_Datafiles_privacy_id_Privacies" in sql_script

    sql_script = str(CreateTable(DatafileType.__table__).compile(dialect=sqlite.dialect()))
    assert "uq_DatafileTypes_name" in sql_script


def test_constraint_names_postgres():
    sql_script = str(CreateTable(Datafile_pg.__table__).compile(dialect=postgresql.dialect()))
    assert "pk_Datafiles" in sql_script
    assert "fk_Datafiles_privacy_id_Privacies" in sql_script

    sql_script = str(CreateTable(Datafile_type_pg.__table__).compile(dialect=postgresql.dialect()))
    assert "uq_DatafileTypes_name" in sql_script


if __name__ == "__main__":
    unittest.main()
