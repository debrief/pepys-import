import unittest

from pepys_import.resolvers.default_resolver import DefaultResolver
from pepys_import.core.store.data_store import DataStore


class DefaultResolverTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.resolver = DefaultResolver()
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
            privacy = self.resolver.resolve_privacy(self.store)
            self.assertEqual(privacy.name, "PRIVACY-1")

    def test_resolve_sensor(self):
        with self.store.session_scope():
            sensor_type, privacy = self.resolver.resolve_sensor(
                data_store=self.store,
                sensor_name="TEST",
                sensor_type=None,
                privacy=None,
            )
            self.assertEqual(sensor_type.name, "Position")
            self.assertEqual(privacy.name, "PRIVACY-1")

    def test_resolver_platform(self):
        with self.store.session_scope():
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


if __name__ == "__main__":
    unittest.main()
