import unittest
from datetime import datetime
from uuid import uuid4

from pepys_import.core.store.data_store import DataStore
from pepys_import.resolvers.default_resolver import DefaultResolver


class DefaultResolverTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.resolver = DefaultResolver()
        self.store = DataStore(
            "", "", "", 0, ":memory:", db_type="sqlite", missing_data_resolver=self.resolver,
        )
        self.store.initialise()
        with self.store.session_scope():
            self.store.populate_reference()
            self.change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id

    def test_resolver_privacy(self):
        with self.store.session_scope():
            privacy = self.resolver.resolve_privacy(self.store, self.change_id)
            self.assertEqual(privacy.name, "PRIVACY-1")

    def test_resolve_sensor(self):
        with self.store.session_scope():
            sensor_name, sensor_type, privacy = self.resolver.resolve_sensor(
                data_store=self.store,
                sensor_name=None,
                sensor_type=None,
                privacy=None,
                host_id=uuid4(),
                change_id=self.change_id,
            )
            self.assertEqual(sensor_name, "SENSOR-1")
            self.assertEqual(sensor_type.name, "Position")
            self.assertEqual(privacy.name, "PRIVACY-1")

    def test_resolve_sensor_gives_sensor_object_when_called_twice(self):
        Sensor = self.store.db_classes.Sensor

        with self.store.session_scope():
            # Create a platform for it to belong to
            platform_obj = self.store.add_to_platforms(
                "TestPlatform",
                "United Kingdom",
                "Fisher",
                "Private",
                trigraph="PLT",
                quadgraph="PLTT",
                pennant_number=1234,
                change_id=self.change_id,
            )

            # Call it first time
            result = self.resolver.resolve_sensor(
                data_store=self.store,
                sensor_name=None,
                sensor_type=None,
                privacy=None,
                host_id=platform_obj.platform_id,
                change_id=self.change_id,
            )

            sensor_name, sensor_type, privacy = result
            self.assertEqual(sensor_name, "SENSOR-1")
            self.assertEqual(sensor_type.name, "Position")
            self.assertEqual(privacy.name, "PRIVACY-1")

            # Add to database (like in get_sensor() in common_db.py)
            new_sensor_obj = Sensor().add_to_sensors(
                data_store=self.store,
                name=sensor_name,
                sensor_type=sensor_type.name,
                host=platform_obj.name,
                privacy_id=privacy.privacy_id,
                change_id=self.change_id,
            )

            # Now when we call resolve_sensor again, it should give us back the
            # same sensor object as above
            result = self.resolver.resolve_sensor(
                data_store=self.store,
                sensor_name=None,
                sensor_type=None,
                privacy=None,
                host_id=platform_obj.platform_id,
                change_id=self.change_id,
            )

            assert result == new_sensor_obj

    def test_resolver_platform(self):
        with self.store.session_scope():
            (
                platform_name,
                trigraph,
                quadgraph,
                pennant_number,
                platform_type,
                nationality,
                privacy,
            ) = self.resolver.resolve_platform(
                data_store=self.store,
                platform_name=None,
                platform_type=None,
                nationality=None,
                privacy=None,
                change_id=self.change_id,
            )
            self.assertEqual(platform_name, "PLATFORM-1")
            self.assertEqual(trigraph, "PL1")
            self.assertEqual(quadgraph, "PLT1")
            self.assertEqual(pennant_number, "123")
            self.assertEqual(platform_type.name, "Warship")
            self.assertEqual(nationality.name, "UK")
            self.assertEqual(privacy.name, "PRIVACY-1")

    def test_resolve_platform_gives_platform_object_when_called_twice(self):
        Platform = self.store.db_classes.Platform

        with self.store.session_scope():
            # Call it first time
            result = self.resolver.resolve_platform(
                data_store=self.store,
                platform_name=None,
                platform_type="Fisher",
                nationality="UK",
                privacy="Private",
                change_id=self.change_id,
            )

            (
                platform_name,
                trigraph,
                quadgraph,
                pennant_number,
                platform_type,
                nationality,
                privacy,
            ) = result

            # Add to database (like in get_sensor() in common_db.py)
            new_platform_obj = self.store.add_to_platforms(
                name=platform_name,
                trigraph=trigraph,
                quadgraph=quadgraph,
                pennant_number=pennant_number,
                nationality=nationality.name,
                platform_type=platform_type.name,
                privacy=privacy.name,
                change_id=self.change_id,
            )

            # Now when we call resolve_sensor again, it should give us back the
            # same sensor object as above
            result = self.resolver.resolve_platform(
                data_store=self.store,
                platform_name=None,
                platform_type="Fisher",
                nationality="UK",
                privacy="Private",
                change_id=self.change_id,
            )

            assert result == new_platform_obj

    def test_resolver_datafile(self):
        with self.store.session_scope():
            datafile_name, datafile_type, privacy = self.resolver.resolve_datafile(
                data_store=self.store,
                datafile_name=None,
                datafile_type=None,
                privacy=None,
                change_id=self.change_id,
            )
            self.assertEqual(datafile_name, "DATAFILE-1")
            self.assertEqual(datafile_type.name, "DATAFILE-TYPE-1")
            self.assertEqual(privacy.name, "PRIVACY-1")


if __name__ == "__main__":
    unittest.main()
