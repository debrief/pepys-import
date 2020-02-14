import os
import unittest
from unittest import TestCase


from pepys_import.core.debug.support_methods import list_all, count_states
from pepys_import.core.store.data_store import DataStore
from pepys_import.core.formats.repl_file import REPFile
from pepys_import.core.formats import unit_registry

FILE_PATH = os.path.dirname(__file__)
TEST_DATA_PATH = os.path.join(FILE_PATH, "sample_data", "track_files", "rep_data")
TEST_FILE = os.path.join(TEST_DATA_PATH, "rep_test1.rep")
BROKEN_FILE = os.path.join(TEST_DATA_PATH, "rep_test2.rep")


class TestLoadReplay(TestCase):
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
            for repLine in rep_file.lines:
                platform = data_store.get_platform(
                    platform_name=repLine.get_platform(),
                    nationality="UK",
                    platform_type="Fisher",
                    privacy="Public",
                )
                all_sensors = data_store.session.query(
                    data_store.db_classes.Sensor
                ).all()
                data_store.add_to_sensor_types("_GPS")
                sensor = platform.get_sensor(
                    session=data_store.session,
                    all_sensors=all_sensors,
                    sensor_name=platform.name,
                    sensor_type="_GPS",
                    privacy="TEST",
                )
                state = datafile.create_state(sensor, repLine.timestamp)
                state.set_location(repLine.get_location())
                state.set_heading(repLine.heading.to(unit_registry.radians).magnitude)
                state.set_speed(
                    repLine.speed.to(
                        unit_registry.meter / unit_registry.second
                    ).magnitude
                )
                privacy = data_store.search_privacy("TEST")
                state.set_privacy(privacy)
                if datafile.validate():
                    state.submit(data_store.session)

        print("Found:" + str(count_states(data_store)))

        self.assertEqual(8, count_states(data_store), "Should have loaded 8 states")

        list_all(data_store)


if __name__ == "__main__":
    unittest.main()
