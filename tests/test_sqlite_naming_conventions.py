import unittest
from datetime import datetime
from sqlite3 import OperationalError

from sqlalchemy.sql.ddl import CreateTable
from testing.postgresql import Postgresql

from pepys_import.core.store.data_store import DataStore
from pepys_import.core.store.postgres_db import Datafile as pg_datafile
from pepys_import.core.store.postgres_db import DatafileType as pg_datafile_type
from pepys_import.core.store.sqlite_db import Datafile, DatafileType


class NamingConventionsTestCase(unittest.TestCase):
    def test_constraint_names_sqlite(self):
        store = DataStore("", "", "", 0, ":memory:", "sqlite")
        sql_script = str(CreateTable(Datafile.__table__).compile(store.engine))
        assert "pk_Datafiles" in sql_script
        assert "ck_Datafiles_simulated" in sql_script

        sql_script = str(CreateTable(DatafileType.__table__).compile(store.engine))
        assert "uq_DatafileTypes_name" in sql_script
        # TODO: extend the test when foreign key constraints are added to SQLite

    def test_constraint_names_postgres(self):
        self.postgres = None
        self.store = None
        try:
            self.postgres = Postgresql(
                database="test", host="localhost", user="postgres", password="postgres", port=55527,
            )
        except RuntimeError:
            print("PostgreSQL database couldn't be created! Test is skipping.")
            return
        try:
            self.store = DataStore(
                db_name="test",
                db_host="localhost",
                db_username="postgres",
                db_password="postgres",
                db_port=55527,
                db_type="postgres",
            )
        except OperationalError:
            print("Database schema and data population failed! Test is skipping.")
        sql_script = str(CreateTable(pg_datafile.__table__).compile(self.store.engine))
        assert "pk_Datafiles" in sql_script
        assert "fk_Datafiles_privacy_id_Privacies" in sql_script

        sql_script = str(CreateTable(pg_datafile_type.__table__).compile(self.store.engine))
        assert "uq_DatafileTypes_name" in sql_script


if __name__ == "__main__":
    unittest.main()
