import os
import unittest
from unittest import TestCase
from sqlalchemy import inspect

from pepys_import.core.store.data_store import DataStore
from pepys_import.core.formats.repl_file import REPFile
from pepys_import.resolvers.command_line_resolver import CommandLineResolver
from pepys_import.core.debug.support_methods import SupportMethods

FILE_PATH = os.path.dirname(__file__)
TEST_DATA_PATH = os.path.join(FILE_PATH, "sample_data", "rep_files")
TEST_FILE = os.path.join(TEST_DATA_PATH, "rep_test1.rep")
BROKEN_FILE = os.path.join(TEST_DATA_PATH, "rep_test2.rep")
INITIAL_DATA_PATH = os.path.join(FILE_PATH, "sample_data", "csv_files")


@unittest.skip("Skip until parsers are implemented")
class TestLoadReplay(TestCase):
    @unittest.skip("Skip until we can automate command-line-resolver")
    def test_load_replay(self):
        """Test  whether we can load REP data"""
        data_store = DataStore(
            "",
            "",
            "",
            0,
            ":memory:",
            db_type="sqlite",
            missing_data_resolver=CommandLineResolver(),
        )

        # creating database from schema
        data_store.initialise()

        data_store.populate_reference(INITIAL_DATA_PATH)

        rep_file = REPFile(TEST_FILE)
        self.assertEqual("REP", rep_file.get_data_file_type())

        with data_store.session_scope() as session:
            datafile = session.add_to_datafile_from_rep(
                rep_file.get_data_file_name(), rep_file.get_data_file_type()
            )
            for repLine in rep_file.get_lines():
                platform = session.add_to_platforms_from_rep(
                    repLine.get_platform(), None, "UK", "Public"
                )
                sensor = session.add_to_sensors_from_rep("GPS", platform)
                session.add_to_states_from_rep(
                    repLine.get_timestamp(),
                    datafile,
                    sensor,
                    repLine.get_latitude(),
                    repLine.get_longitude(),
                    repLine.get_heading(),
                    repLine.get_speed(),
                )

        inspector = inspect(data_store.engine)
        table_names = inspector.get_table_names()

        # 11 tables must be created. A few of them tested
        self.assertEqual(len(table_names), 11)
        self.assertIn("Entry", table_names)
        self.assertIn("Platforms", table_names)
        self.assertIn("States", table_names)
        self.assertIn("Datafiles", table_names)
        self.assertIn("Nationalities", table_names)

        support = SupportMethods()
        self.assertEqual(8, support.count_states(data_store))


if __name__ == "__main__":
    unittest.main()
