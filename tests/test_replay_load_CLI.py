import os
import unittest
from unittest import TestCase
from sqlalchemy import inspect

from pepys_import.core.store.data_store import DataStore
from pepys_import.core.formats.repl_file import REPFile
from pepys_import.resolvers.command_line_resolver import CommandLineResolver
from pepys_import.core.debug.support_methods import count_states

FILE_PATH = os.path.dirname(__file__)
TEST_DATA_PATH = os.path.join(FILE_PATH, "sample_data", "track_files", "rep_data")
TEST_FILE = os.path.join(TEST_DATA_PATH, "rep_test1.rep")
BROKEN_FILE = os.path.join(TEST_DATA_PATH, "rep_test2.rep")
INITIAL_DATA_PATH = os.path.join(FILE_PATH, "sample_data", "csv_files")


class TestLoadReplay(TestCase):
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
        self.assertEqual("REP", rep_file.datafile_type)

        with data_store.session_scope():
            datafile = data_store.add_to_datafiles(
                simulated=False,
                privacy="TEST",
                file_type=rep_file.datafile_type,
                reference=rep_file.filepath,
            )
            for rep_line in rep_file.lines:
                platform = data_store.add_to_platforms(
                    rep_line.get_platform(), None, "UK", "Public"
                )
                sensor = data_store.add_to_sensors("GPS", "_GPS", platform)
                data_store.add_to_states(
                    rep_line.timestamp,
                    datafile,
                    sensor,
                    rep_line.latitude,
                    rep_line.longitude,
                    rep_line.heading,
                    rep_line.speed,
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

        self.assertEqual(8, count_states(data_store))


if __name__ == "__main__":
    unittest.main()
