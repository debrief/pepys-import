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

    def test_resolver_privacy(self):
        with self.store.session_scope():
            with StdinAuto(["1", "PRIVACY-TEST"]):
                privacy = self.resolver.resolve_privacy(self.store)
            self.assertEqual(privacy.name, "PRIVACY-TEST")

    def test_quit_works_for_resolver_privacy(self):
        with self.store.session_scope():
            with StdinAuto(["."]):
                with self.assertRaises(SystemExit):
                    self.resolver.resolve_privacy(self.store)

    def test_resolve_sensor(self):
        with self.store.session_scope():
            self.store.add_to_sensor_types("SENSOR-TYPE-1")
            self.store.add_to_privacies("PRIVACY-1")

            with StdinAuto(["2", "1", "SENSOR-TYPE-1", "1", "PRIVACY-1"]):
                sensor_type, privacy = self.resolver.resolve_sensor(
                    self.store, "TEST", sensor_type=None, privacy=None
                )

            self.assertEqual(sensor_type.name, "SENSOR-TYPE-1")
            self.assertEqual(privacy.name, "PRIVACY-1")

    def test_quit_works_for_resolver_sensor(self):
        with self.store.session_scope():
            with StdinAuto(["."]):
                with self.assertRaises(SystemExit):
                    self.resolver.resolve_sensor(self.store, "", "", "")
            with StdinAuto(["2", "."]):
                with self.assertRaises(SystemExit):
                    self.resolver.resolve_sensor(self.store, "", "", "")

    def test_resolver_platform(self):
        with self.store.session_scope():
            self.store.add_to_privacies("PRIVACY-1")
            self.store.add_to_platform_types("Warship")
            self.store.add_to_nationalities("UK")
            with StdinAuto(["2", "1", "UK", "1", "Warship", "1", "PRIVACY-1", "1"]):
                (
                    platform_name,
                    platform_type,
                    nationality,
                    privacy,
                ) = self.resolver.resolve_platform(
                    data_store=self.store,
                    platform_name="TEST",
                    platform_type=None,
                    nationality=None,
                    privacy=None,
                )
                self.assertEqual(platform_name, "TEST")
                self.assertEqual(platform_type.name, "Warship")
                self.assertEqual(nationality.name, "UK")
                self.assertEqual(privacy.name, "PRIVACY-1")

    def test_quit_works_for_resolver_platform(self):
        with self.store.session_scope():
            self.store.add_to_privacies("PRIVACY-1")
            self.store.add_to_platform_types("Warship")
            self.store.add_to_nationalities("UK")

            with StdinAuto(["."]):
                with self.assertRaises(SystemExit):
                    self.resolver.resolve_platform(self.store, "", "", "", "")
            with StdinAuto(["2", "."]):
                with self.assertRaises(SystemExit):
                    self.resolver.resolve_platform(self.store, "", "", "", "")
            with StdinAuto(["2", "1", "UK", "."]):
                with self.assertRaises(SystemExit):
                    self.resolver.resolve_platform(self.store, "", "", "", "")
            with StdinAuto(["2", "1", "UK", "1", "Warship", "."]):
                with self.assertRaises(SystemExit):
                    self.resolver.resolve_platform(self.store, "", "", "", "")
            with StdinAuto(["2", "1", "UK", "1", "Warship", "1", "PRIVACY-1", "."]):
                with self.assertRaises(SystemExit):
                    self.resolver.resolve_platform(self.store, "", "", "", "")


if __name__ == "__main__":
    unittest.main()
