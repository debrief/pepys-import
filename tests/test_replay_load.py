import os
import unittest
from unittest import TestCase


from pepys_import.core.debug.support_methods import list_all, count_states
from pepys_import.core.store.data_store import DataStore
from pepys_import.core.formats.repl_file import REPFile
from pepys_import.core.formats import unit_registry
from pepys_import.core.validators import constants
from pepys_import.file.importer import Importer

FILE_PATH = os.path.dirname(__file__)
TEST_DATA_PATH = os.path.join(FILE_PATH, "sample_data", "track_files", "rep_data")
TEST_FILE = os.path.join(TEST_DATA_PATH, "rep_test1.rep")
BROKEN_FILE = os.path.join(TEST_DATA_PATH, "rep_test2.rep")


class TestLoadReplay(TestCase):
    def setUp(self) -> None:
        class TestParser(Importer):
            def __init__(
                self,
                name="Test Importer",
                validation_level=constants.NONE_LEVEL,
                short_name="Test Importer",
                separator=" ",
            ):
                super().__init__(name, validation_level, short_name)
                self.separator = separator
                self.text_label = None
                self.depth = 0.0
                self.errors = list()

            def can_load_this_header(self, header) -> bool:
                return True

            def can_load_this_filename(self, filename):
                return True

            def can_load_this_type(self, suffix):
                return True

            def can_load_this_file(self, file_contents):
                return True

            def load_this_file(self, data_store, path, file_contents, datafile):
                pass

        self.parser = TestParser()

    def test_load_replay(self):
        """Test  whether we can load REP data"""
        data_store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")

        # creating database from schema
        data_store.initialise()

        rep_file = REPFile(TEST_FILE)
        self.assertEqual("REP", rep_file.datafile_type)

        with data_store.session_scope():
            datafile = data_store.get_datafile(
                rep_file.filepath, rep_file.datafile_type
            )
            datafile.measurements[self.parser.short_name] = list()
            for rep_line in rep_file.lines:
                platform = data_store.get_platform(
                    platform_name=rep_line.get_platform(),
                    nationality="UK",
                    platform_type="Fisher",
                    privacy="Public",
                )
                sensor_type = data_store.add_to_sensor_types("_GPS")
                privacy = data_store.missing_data_resolver.resolve_privacy(data_store)
                sensor = platform.get_sensor(
                    data_store=data_store,
                    sensor_name=platform.name,
                    sensor_type=sensor_type,
                    privacy=privacy.name,
                )
                state = datafile.create_state(
                    sensor, rep_line.timestamp, parser_name=self.parser.short_name
                )
                state.location = rep_line.get_location()
                state.heading = rep_line.heading.to(unit_registry.radians).magnitude
                state.speed = rep_line.speed
                state.privacy = privacy.privacy_id
                if datafile.validate():
                    datafile.commit(data_store.session)

        print("Found:" + str(count_states(data_store)))

        self.assertEqual(8, count_states(data_store), "Should have loaded 8 states")

        list_all(data_store)


if __name__ == "__main__":
    unittest.main()
