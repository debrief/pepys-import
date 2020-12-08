import unittest
from datetime import datetime

import pytest

from pepys_import.core.store.data_store import DataStore
from pepys_import.utils.data_store_utils import MissingDataException


class MissingFieldsTestCase(unittest.TestCase):
    """This class includes tests where missing fields given to add methods"""

    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

        with self.store.session_scope():
            self.store.populate_reference()
            self.change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id

    def tearDown(self):
        pass

    def test_missing_fields_for_add_to_platforms(self):
        with self.store.session_scope():
            with pytest.raises(MissingDataException):
                self.store.add_to_platforms(
                    name="TestPlatform",
                    nationality="MissingNationality",
                    platform_type="Fishing Vessel",
                    privacy="Public",
                    trigraph="TPL",
                    quadgraph="TPLT",
                    identifier="123",
                    change_id=self.change_id,
                )

            with pytest.raises(MissingDataException):
                self.store.add_to_platforms(
                    name="TestPlatform",
                    nationality="United Kingdom",
                    platform_type="MissingPlatformType",
                    privacy="Public",
                    trigraph="TPL",
                    quadgraph="TPLT",
                    identifier="123",
                    change_id=self.change_id,
                )

            with pytest.raises(MissingDataException):
                self.store.add_to_platforms(
                    name="TestPlatform",
                    nationality="United Kingdom",
                    platform_type="Fishing Vessel",
                    privacy="MissingPrivacy",
                    trigraph="TPL",
                    quadgraph="TPLT",
                    identifier="123",
                    change_id=self.change_id,
                )

            # Shouldn't raise an exception, as all valid
            self.store.add_to_platforms(
                name="TestPlatform",
                nationality="United Kingdom",
                platform_type="Fishing Vessel",
                privacy="Public",
                trigraph="TPL",
                quadgraph="TPLT",
                identifier="123",
                change_id=self.change_id,
            )

    def test_missing_fields_for_add_to_sensors(self):
        plat_id = self.store.add_to_platforms(
            name="TestPlatform",
            nationality="United Kingdom",
            platform_type="Fishing Vessel",
            privacy="Public",
            trigraph="TPL",
            quadgraph="TPLT",
            identifier="123",
            change_id=self.change_id,
        ).platform_id

        with self.store.session_scope():
            with pytest.raises(MissingDataException):
                self.store.add_to_sensors(
                    name="TestSensor",
                    sensor_type="MissingSensorType",
                    host_name=None,
                    host_identifier=None,
                    host_nationality=None,
                    host_id=plat_id,
                    privacy="Public",
                    change_id=self.change_id,
                )

            with pytest.raises(MissingDataException):
                self.store.add_to_sensors(
                    name="TestSensor",
                    sensor_type="Location-Satellite",
                    host_name="MissingPlatform",
                    host_identifier="123",
                    host_nationality="UK",
                    privacy="Public",
                    change_id=self.change_id,
                )

            with pytest.raises(MissingDataException):
                self.store.add_to_sensors(
                    name="TestSensor",
                    sensor_type="Location-Satellite",
                    host_name=None,
                    host_identifier=None,
                    host_nationality=None,
                    host_id=plat_id,
                    privacy="MissingPrivacy",
                    change_id=self.change_id,
                )

            # Shouldn't raise an exception, as all valid
            self.store.add_to_sensors(
                name="TestSensor",
                sensor_type="Location-Satellite",
                host_name=None,
                host_identifier=None,
                host_nationality=None,
                host_id=plat_id,
                privacy="Public",
                change_id=self.change_id,
            )

    def test_missing_fields_for_add_to_datafiles(self):
        with self.store.session_scope():
            with pytest.raises(MissingDataException):
                self.store.add_to_datafiles(
                    "PRIVACY-DoesNotExist",
                    "GPX",
                    "DATAFILE-1",
                    True,
                    0,
                    "HASHED-1",
                    change_id=self.change_id,
                )

            with pytest.raises(MissingDataException):
                self.store.add_to_datafiles(
                    "Public",
                    "DATAFILE-TYPE-1-DoesNotExist",
                    "DATAFILE-1",
                    True,
                    0,
                    "HASHED-1",
                    change_id=self.change_id,
                )

            # Shouldn't raise an exception, as all valid
            self.store.add_to_datafiles(
                "Public",
                "GPX",
                "DATAFILE-1",
                True,
                0,
                "HASHED-1",
                change_id=self.change_id,
            )


if __name__ == "__main__":
    unittest.main()
