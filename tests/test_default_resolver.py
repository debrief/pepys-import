import unittest
from datetime import datetime
from uuid import uuid4

from pepys_import.core.store.data_store import DataStore
from pepys_import.resolvers.default_resolver import DefaultResolver


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
        with self.store.session_scope():
            self.store.populate_reference()
            self.change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id

    def test_resolver_privacy(self):
        with self.store.session_scope():
            privacy = self.resolver.resolve_privacy(self.store, self.change_id)
            self.assertEqual(privacy.name, "Public")

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
            self.assertEqual(privacy.name, "Public")

    def test_resolve_sensor_gives_sensor_object_when_called_twice(self):
        with self.store.session_scope():
            # Create a platform for it to belong to
            platform_obj = self.store.add_to_platforms(
                "TestPlatform",
                "1234",
                "United Kingdom",
                "Fishing Vessel",
                "Private",
                trigraph="PLT",
                quadgraph="PLTT",
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
            self.assertEqual(privacy.name, "Public")

            # Add to database (like in get_sensor() in common_db.py)
            new_sensor_obj = self.store.add_to_sensors(
                name=sensor_name,
                sensor_type=sensor_type.name,
                host_name=None,
                host_nationality=None,
                host_identifier=None,
                host_id=platform_obj.platform_id,
                privacy=privacy.name,
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
                identifier,
                platform_type,
                nationality,
                privacy,
            ) = self.resolver.resolve_platform(
                data_store=self.store,
                platform_name=None,
                identifier=None,
                platform_type=None,
                nationality=None,
                privacy=None,
                change_id=self.change_id,
            )
            self.assertEqual(platform_name, "PLATFORM-1")
            self.assertEqual(trigraph, "PL1")
            self.assertEqual(quadgraph, "PLT1")
            self.assertEqual(identifier, "123")
            self.assertEqual(platform_type.name, "Warship")
            self.assertEqual(nationality.name, "UK")
            self.assertEqual(privacy.name, "Public")

    def test_resolve_platform_gives_platform_object_when_called_twice(self):
        with self.store.session_scope():
            # Call it first time
            result = self.resolver.resolve_platform(
                data_store=self.store,
                platform_name=None,
                identifier=None,
                platform_type="Fisher",
                nationality="UK",
                privacy="Private",
                change_id=self.change_id,
            )

            (
                platform_name,
                trigraph,
                quadgraph,
                identifier,
                platform_type,
                nationality,
                privacy,
            ) = result

            # Add to database (like in get_sensor() in common_db.py)
            new_platform_obj = self.store.add_to_platforms(
                name=platform_name,
                trigraph=trigraph,
                quadgraph=quadgraph,
                identifier=identifier,
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
                identifier=identifier,
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
            self.assertEqual(privacy.name, "Public")

    def test_resolve_missing_info(self):
        info_str = self.resolver.resolve_missing_info("Test question?", "DEFAULT")
        self.assertEqual(info_str, "DEFAULT")

        info_int = self.resolver.resolve_missing_info("The Question", 10)
        self.assertEqual(info_int, 10)


class DefaultResolverTestCaseWithNoRefLoaded(unittest.TestCase):
    """
    Does the same as the test above, but doesn't load reference data into data store first, so we can test that
    the privacy is created properly even if it doesn't exist
    """

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
        with self.store.session_scope():
            self.change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id

    def test_resolver_privacy(self):
        with self.store.session_scope():
            privacy = self.resolver.resolve_privacy(self.store, self.change_id)
            self.assertEqual(privacy.name, "Public")

    def test_resolve_sensor_with_given_privacy(self):
        with self.store.session_scope():
            self.store.add_to_platform_types("PlatType", change_id=self.change_id)
            self.store.add_to_nationalities("UK", change_id=self.change_id)
            self.store.add_to_privacies("Priv1", 0, change_id=self.change_id)
            platform = self.store.add_to_platforms(
                "TestPlatform", "P123", "UK", "PlatType", "Priv1", change_id=self.change_id
            )
            self.resolver.resolve_sensor(
                self.store,
                "TestSensorName",
                "TestSensorType",
                platform.platform_id,
                "TestPrivacy",
                self.change_id,
            )

            result = self.store.search_privacy("TestPrivacy")
            assert result is not None


if __name__ == "__main__":
    unittest.main()
