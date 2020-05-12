import unittest

from sqlalchemy.sql.ddl import CreateTable

from pepys_import.core.store.data_store import DataStore
from pepys_import.core.store.sqlite_db import Datafile


class NamingConventionsTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.store = DataStore("", "", "", 0, ":memory:", "sqlite")

    def test_constraint_names(self):
        sql_script = str(CreateTable(Datafile.__table__).compile(self.store.engine))
        assert "pk_Datafiles" in sql_script
        assert "ck_Datafiles_simulated" in sql_script


if __name__ == "__main__":
    unittest.main()
