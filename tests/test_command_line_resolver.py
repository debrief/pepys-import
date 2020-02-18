import unittest

from qprompt import StdinAuto

from pepys_import.resolvers.command_line_resolver import CommandLineResolver
from pepys_import.core.store.data_store import DataStore


class CommandLineResolverTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.resolver = CommandLineResolver()
        self.store = DataStore(
            "",
            "",
            "",
            0,
            ":memory:",
            db_type="sqlite",
            missing_data_resolver=self.resolver,
        )
        self.store.initialise()

    def test_resolve_sensor(self):
        with self.store.session_scope():
            self.store.add_to_sensor_types("SENSOR-TYPE-1")
            privacy = self.store.add_to_privacies("PRIVACY-1")

            with StdinAuto(["1", "1", "SENSOR-TYPE-1"]):
                sensor_name, sensor_type, privacy = self.resolver.resolve_sensor(
                    self.store, "TEST", privacy
                )

            self.assertEqual(sensor_name, "TEST")
            self.assertEqual(sensor_type.name, "SENSOR-TYPE-1")


if __name__ == "__main__":
    unittest.main()
