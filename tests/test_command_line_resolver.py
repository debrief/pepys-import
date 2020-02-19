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

    def test_resolver_sensor_with_sensor_given(self):
        with self.store.session_scope():
            sensor_type = self.store.add_to_sensor_types("SENSOR-TYPE-1")
            privacy = self.store.add_to_privacies("PRIVACY-1")
            platform_type = self.store.add_to_platform_types("Warship")
            nationality = self.store.add_to_nationalities("UK")
            platform = self.store.get_platform(
                "PLATFORM-1",
                nationality=nationality.name,
                platform_type=platform_type.name,
                privacy=privacy.name,
            )
            all_sensors = self.store.session.query(self.store.db_classes.Sensor).all()
            platform.get_sensor(
                data_store=self.store,
                all_sensors=all_sensors,
                sensor_name="TEST",
                sensor_type=sensor_type,
                privacy=privacy,
            )
            sensor = self.resolver.resolve_sensor(
                data_store=self.store,
                sensor_name="TEST",
                sensor_type=sensor_type,
                privacy=privacy,
            )
            self.assertEqual(sensor.name, "TEST")
            self.assertEqual(sensor.sensor_type_id, sensor_type.sensor_type_id)

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

    def test_resolver_platform_with_values(self):
        with self.store.session_scope():
            privacy = self.store.add_to_privacies("PRIVACY-1").name
            platform_type = self.store.add_to_platform_types("Warship").name
            nationality = self.store.add_to_nationalities("UK").name
            with StdinAuto(["2", "1"]):
                (
                    platform_name,
                    platform_type,
                    nationality,
                    privacy,
                ) = self.resolver.resolve_platform(
                    data_store=self.store,
                    platform_name="TEST",
                    platform_type=platform_type,
                    nationality=nationality,
                    privacy=privacy,
                )
                self.assertEqual(platform_name, "TEST")
                self.assertEqual(platform_type.name, "Warship")
                self.assertEqual(nationality.name, "UK")
                self.assertEqual(privacy.name, "PRIVACY-1")

    def test_resolver_platform_with_platform_given(self):
        with self.store.session_scope():
            privacy = self.store.add_to_privacies("PRIVACY-1")
            platform_type = self.store.add_to_platform_types("Warship")
            nationality = self.store.add_to_nationalities("UK")
            self.store.get_platform(
                "TEST",
                nationality=nationality.name,
                platform_type=platform_type.name,
                privacy=privacy.name,
            )
            platform = self.resolver.resolve_platform(
                data_store=self.store,
                platform_name="TEST",
                platform_type=platform_type.name,
                nationality=nationality.name,
                privacy=privacy.name,
            )
            self.assertEqual(platform.name, "TEST")
            self.assertEqual(platform.platform_type_id, platform_type.platform_type_id)
            self.assertEqual(platform.nationality_id, nationality.nationality_id)
            self.assertEqual(platform.privacy_id, privacy.privacy_id)


if __name__ == "__main__":
    unittest.main()
