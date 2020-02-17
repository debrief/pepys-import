import os
import unittest
from unittest import TestCase
from sqlalchemy import inspect
from qprompt import StdinAuto

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
            datafile = data_store.get_datafile(
                rep_file.datafile_type, rep_file.filepath
            )
            for rep_line in rep_file.lines:
                with StdinAuto([2, 1]):
                    platform = data_store.get_platform(
                        rep_line.get_platform(), None, "UK", "Public"
                    )
                sensors = data_store.session.query(data_store.db_classes.Sensor).all()
                sensor = platform.get_sensor(data_store.session, sensors, "GPS", "_GPS")
                state = datafile.create_state(sensor, rep_line.timestamp)
                state.location = rep_line.get_location()
                state.heading = rep_line.heading
                state.speed = rep_line.speed
                privacy = data_store.search_privacy("TEST")
                state.privacy = privacy.privacy_id
                if datafile.validate():
                    state.submit(data_store.session)

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
