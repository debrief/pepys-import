import os
import unittest
from unittest import TestCase


from pepys_import.core.debug.support_methods import SupportMethods
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
        self.assertEqual("REP", rep_file.get_data_file_type())

        with data_store.session_scope() as session:
            # TODO: The following line and privacy argument should be deleted.
            # Missing data resolver has to be used
            data_store.add_to_privacies("TEST")
            if data_store.search_datafile_type(rep_file.get_data_file_type()) is None:
                data_store.add_to_datafile_types(rep_file.get_data_file_type())
            datafile = data_store.add_to_datafiles(
                simulated=False,
                privacy="TEST",
                reference=rep_file.get_data_file_name(),
                file_type=rep_file.get_data_file_type(),
            )

            if data_store.search_privacy("Public") is None:
                data_store.add_to_privacies("Public")
            if data_store.search_nationality("UK") is None:
                data_store.add_to_nationalities("UK")
            if data_store.search_platform_type("Fisher") is None:
                data_store.add_to_platform_types("Fisher")
            if data_store.search_sensor_type("_GPS") is None:
                data_store.add_to_sensor_types("_GPS")
            for repLine in rep_file.get_lines():
                platform = data_store.add_to_platforms(
                    name=repLine.get_platform(),
                    nationality="UK",
                    platform_type="Fisher",
                    privacy="Public",
                )
                sensor = data_store.add_to_sensors(
                    name=platform.name, sensor_type="_GPS", host=platform.name
                )
                data_store.add_to_states(
                    time=repLine.get_timestamp(),
                    sensor=sensor.name,
                    datafile=datafile.reference,
                    location=repLine.get_location(),
                    heading=repLine.get_heading().to(unit_registry.radians).magnitude,
                    speed=repLine.get_speed()
                    .to(unit_registry.meter / unit_registry.second)
                    .magnitude,
                    privacy="TEST",
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
