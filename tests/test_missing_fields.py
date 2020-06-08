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
                    platform_type="PLATFORM-TYPE-1",
                    privacy="PRIVACY-1",
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
                    privacy="PRIVACY-1",
                    trigraph="TPL",
                    quadgraph="TPLT",
                    identifier="123",
                    change_id=self.change_id,
                )

            with pytest.raises(MissingDataException):
                self.store.add_to_platforms(
                    name="TestPlatform",
                    nationality="United Kingdom",
                    platform_type="PLATFORM-TYPE-1",
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
                platform_type="PLATFORM-TYPE-1",
                privacy="PRIVACY-1",
                trigraph="TPL",
                quadgraph="TPLT",
                identifier="123",
                change_id=self.change_id,
            )

    def test_missing_fields_for_add_to_sensors(self):
        self.store.add_to_platforms(
            name="TestPlatform",
            nationality="United Kingdom",
            platform_type="PLATFORM-TYPE-1",
            privacy="PRIVACY-1",
            trigraph="TPL",
            quadgraph="TPLT",
            identifier="123",
            change_id=self.change_id,
        )

        with self.store.session_scope():
            with pytest.raises(MissingDataException):
                self.store.add_to_sensors(
                    name="TestSensor",
                    sensor_type="MissingSensorType",
                    host="TestPlatform",
                    privacy="PRIVACY-1",
                    change_id=self.change_id,
                )

            with pytest.raises(MissingDataException):
                self.store.add_to_sensors(
                    name="TestSensor",
                    sensor_type="GPS",
                    host="MissingPlatform",
                    privacy="PRIVACY-1",
                    change_id=self.change_id,
                )

            with pytest.raises(MissingDataException):
                self.store.add_to_sensors(
                    name="TestSensor",
                    sensor_type="GPS",
                    host="TestPlatform",
                    privacy="MissingPrivacy",
                    change_id=self.change_id,
                )

            # Shouldn't raise an exception, as all valid
            self.store.add_to_sensors(
                name="TestSensor",
                sensor_type="GPS",
                host="TestPlatform",
                privacy="PRIVACY-1",
                change_id=self.change_id,
            )

    def test_missing_fields_for_add_to_datafiles(self):
        with self.store.session_scope():
            with pytest.raises(MissingDataException):
                self.store.add_to_datafiles(
                    "PRIVACY-DoesNotExist",
                    "DATAFILE-TYPE-1",
                    "DATAFILE-1",
                    True,
                    0,
                    "HASHED-1",
                    change_id=self.change_id,
                )

            with pytest.raises(MissingDataException):
                self.store.add_to_datafiles(
                    "PRIVACY-1",
                    "DATAFILE-TYPE-1-DoesNotExist",
                    "DATAFILE-1",
                    True,
                    0,
                    "HASHED-1",
                    change_id=self.change_id,
                )

            # Shouldn't raise an exception, as all valid
            self.store.add_to_datafiles(
                "PRIVACY-1",
                "DATAFILE-TYPE-1",
                "DATAFILE-1",
                True,
                0,
                "HASHED-1",
                change_id=self.change_id,
            )


if __name__ == "__main__":
    unittest.main()
