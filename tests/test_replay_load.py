import os
import unittest
from unittest import TestCase
from sqlalchemy import inspect, MetaData, Table


from pepys_import.core.debug.support_methods import SupportMethods
from pepys_import.core.store.data_store import DataStore
from pepys_import.core.formats.repl_file import REPFile
from pepys_import.core.store.sqlite_db import State


FILE_PATH = os.path.dirname(__file__)
TEST_DATA_PATH = os.path.join(FILE_PATH, "sample_data", "track_files", "rep_data")
TEST_FILE = os.path.join(TEST_DATA_PATH, "rep_test1.rep")
BROKEN_FILE = os.path.join(TEST_DATA_PATH, "rep_test2.rep")


@unittest.skip("Skip until parsers are implemented")
class TestLoadReplay(TestCase):
    @unittest.skip("Skip until datafile parsers are implemented")
    def test_load_replay(self):
        """Test  whether we can load REP data"""
        data_store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")

        # creating database from schema
        data_store.initialise()

        rep_file = REPFile(TEST_FILE)
        self.assertEqual("REP", rep_file.get_data_file_type())

        with data_store.session_scope() as session:
            datafile = session.add_to_datafile_from_rep(
                rep_file.get_data_file_name(), rep_file.get_data_file_type()
            )
            for repLine in rep_file.get_lines():
                platform = session.add_to_platforms_from_rep(
                    repLine.get_platform(), "Fisher", "UK", "Public"
                )

                sensor = session.add_to_sensors_from_rep(
                    platform.name + "_GPS", platform
                )
                session.add_to_states_from_rep(
                    repLine.get_timestamp(),
                    datafile,
                    sensor,
                    (repLine.get_latitude(), repLine.get_longitude()),
                    repLine.get_heading(),
                    repLine.get_speed(),
                )

        support = SupportMethods()
        print("Found:" + str(support.count_states(data_store)))

        support = SupportMethods()
        self.assertEqual(
            8, support.count_states(data_store), "Should have loaded 8 states"
        )

        support.list_all(data_store)


if __name__ == "__main__":
    unittest.main()
