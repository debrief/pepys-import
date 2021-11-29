import unittest
from datetime import datetime
from uuid import UUID

from pepys_import.core.store.data_store import DataStore


class UnknownPlatformTestCase(unittest.TestCase):
    def setUp(self):
        self.ds = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.ds.initialise()
        with self.ds.session_scope():
            self.ds.populate_reference()
            self.ds.populate_metadata()

        with self.ds.session_scope():
            self.change_id = self.ds.add_to_changes("TEST", datetime.now(), "TEST reason").change_id

    def test_get_platform_unknown_no_name(self):
        plat = self.ds.get_platform(change_id=self.change_id, unknown=True)

        # This will fail if the name isn't a well-formed UUID
        _ = UUID(plat.name)

        assert plat.identifier == plat.name
        assert plat.platform_type_name == "Unknown"
        assert plat.nationality_name == "Unknown"
        assert plat.privacy_name == "Public"

    def test_get_platform_unknown_with_name(self):
        plat = self.ds.get_platform(
            platform_name="Test Name", change_id=self.change_id, unknown=True
        )

        assert plat.name == "Test Name"
        assert plat.identifier == plat.name
        assert plat.platform_type_name == "Unknown"
        assert plat.nationality_name == "Unknown"
        assert plat.privacy_name == "Public"

    def test_get_sensor_no_details(self):
        plat = self.ds.get_platform(
            platform_name="Test Name", change_id=self.change_id, unknown=True
        )

        sensor = plat.get_sensor(self.ds, change_id=self.change_id)

        _ = UUID(sensor.name)
        assert sensor.sensor_type_name == "Unknown"
        assert sensor.host__name == "Test Name"
        assert sensor.privacy_name == "Public"

    def test_get_sensor_given_name(self):
        plat = self.ds.get_platform(
            platform_name="Test Name", change_id=self.change_id, unknown=True
        )

        sensor = plat.get_sensor(self.ds, sensor_name="Test Sensor Name", change_id=self.change_id)

        assert sensor.name == "Test Sensor Name"
        assert sensor.sensor_type_name == "Unknown"
        assert sensor.host__name == "Test Name"
        assert sensor.privacy_name == "Public"

    def test_get_sensor_given_type(self):
        plat = self.ds.get_platform(
            platform_name="Test Name", change_id=self.change_id, unknown=True
        )

        sensor = plat.get_sensor(self.ds, sensor_type="Radar", change_id=self.change_id)

        assert sensor.sensor_type_name == "Radar"
        assert sensor.host__name == "Test Name"
        assert sensor.privacy_name == "Public"
