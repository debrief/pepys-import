import os
import shutil
import unittest
from datetime import datetime
from getpass import getuser
from unittest.mock import patch

import pytest
from testing.postgresql import Postgresql

from pepys_admin.merge import (
    merge_all_metadata_tables,
    merge_all_reference_tables,
    merge_all_tables,
    merge_metadata_table,
    merge_reference_table,
    table_name_to_class_name,
)
from pepys_admin.snapshot_cli import SnapshotShell
from pepys_admin.utils import check_sqlalchemy_results_are_equal, sqlalchemy_obj_to_dict
from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor
from pepys_import.resolvers.default_resolver import DefaultResolver
from pepys_import.utils.sqlalchemy_utils import get_primary_key_for_table

SAMPLE_DATA_PATH = os.path.join(os.path.dirname(__file__), "sample_data")


class TestSensorTypeMerge(unittest.TestCase):
    def setUp(self):
        """Creates the master and slave databases and contents required for the test.

        At the end of this set up we will have We have two unique SensorTypes on master, two unique
        on slave, one shared with same name and different GUID, and one shared with same name and
        same GUID.

        """
        if os.path.exists("master.sqlite"):
            os.remove("master.sqlite")

        if os.path.exists("slave.sqlite"):
            os.remove("slave.sqlite")

        self.master_store = DataStore("", "", "", 0, db_name="master.sqlite", db_type="sqlite")
        self.slave_store = DataStore("", "", "", 0, db_name="slave.sqlite", db_type="sqlite")

        self.master_store.initialise()
        self.slave_store.initialise()

        with self.master_store.session_scope():
            change_id = self.master_store.add_to_changes(
                "TEST", datetime.utcnow(), "TEST"
            ).change_id
            self.master_store.add_to_sensor_types("ST_Master_1", change_id)
            self.master_store.add_to_sensor_types("ST_Master_2", change_id)
            self.master_store.add_to_sensor_types("ST_Shared_1", change_id)
            st_obj = self.master_store.add_to_sensor_types("ST_Shared_2GUIDMatch", change_id)
            st_obj_guid = st_obj.sensor_type_id

        with self.slave_store.session_scope():
            change_id = self.slave_store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id
            self.slave_store.add_to_sensor_types("ST_Slave_1", change_id)
            self.slave_store.add_to_sensor_types("ST_Slave_2", change_id)
            slave_shared_obj = self.slave_store.add_to_sensor_types("ST_Shared_1", change_id)
            self.slave_shared_id = slave_shared_obj.sensor_type_id
            st_obj_slave = self.slave_store.add_to_sensor_types("ST_Shared_2GUIDMatch", change_id)
            st_obj_slave.sensor_type_id = st_obj_guid
            self.slave_store.session.add(st_obj_slave)
            self.slave_store.session.commit()

            self.slave_store.add_to_platform_types("PlatformType1", change_id)
            self.slave_store.add_to_nationalities("UK", change_id)
            self.slave_store.add_to_privacies("Private", change_id)
            self.slave_store.add_to_platforms(
                "Platform1", "UK", "PlatformType1", "Private", change_id=change_id
            )
            self.slave_store.add_to_sensors(
                "Sensor1", "ST_Shared_1", "Platform1", "Private", change_id
            )

    def tearDown(self):
        if os.path.exists("master.sqlite"):
            os.remove("master.sqlite")

        if os.path.exists("slave.sqlite"):
            os.remove("slave.sqlite")

    def test_sensor_type_merge(self):
        # Do the merge
        id_results = merge_reference_table("SensorType", self.master_store, self.slave_store)

        master_table = self.master_store.db_classes.SensorType
        slave_table = self.slave_store.db_classes.SensorType

        # Check there are now 6 rows in the master database
        results = self.master_store.session.query(master_table).all()
        assert len(results) == 6

        # Check the rows that were originally just in the slave db have been copied across
        # and that all their fields match (including GUID, but excluding created_date)
        master_results = (
            self.master_store.session.query(master_table)
            .filter(master_table.name.in_(["ST_Slave_1", "ST_Slave_2"]))
            .all()
        )
        slave_results = (
            self.slave_store.session.query(slave_table)
            .filter(slave_table.name.in_(["ST_Slave_1", "ST_Slave_2"]))
            .all()
        )

        assert check_sqlalchemy_results_are_equal(master_results, slave_results)

        assert slave_results[0].sensor_type_id in id_results["added"]
        assert slave_results[1].sensor_type_id in id_results["added"]

        # Check that the row that had the same name and same GUID in each db is still in both
        # databases
        master_results = (
            self.master_store.session.query(master_table)
            .filter(master_table.name == "ST_Shared_2GUIDMatch")
            .all()
        )
        slave_results = (
            self.slave_store.session.query(slave_table)
            .filter(slave_table.name == "ST_Shared_2GUIDMatch")
            .all()
        )

        assert check_sqlalchemy_results_are_equal(master_results, slave_results)

        assert id_results["already_there"] == [slave_results[0].sensor_type_id]

        # Check that the row that had the same name but different GUID in each db now
        # matches in both databases
        master_results = (
            self.master_store.session.query(master_table)
            .filter(master_table.name == "ST_Shared_1")
            .all()
        )
        slave_results = (
            self.slave_store.session.query(slave_table)
            .filter(slave_table.name == "ST_Shared_1")
            .all()
        )
        new_guid = slave_results[0].sensor_type_id

        assert check_sqlalchemy_results_are_equal(master_results, slave_results)

        assert id_results["modified"]["from"] == [self.slave_shared_id]
        assert id_results["modified"]["to"] == [new_guid]

        # Check that the new GUID for this row has propagated to the Sensors table in the slave database
        # (so we can copy this table later with no problems)
        results = (
            self.slave_store.session.query(self.slave_store.db_classes.Sensor)
            .filter(self.slave_store.db_classes.Sensor.sensor_type_id == new_guid)
            .all()
        )

        assert len(results) == 1


class TestPlatformTypeMerge(unittest.TestCase):
    def setUp(self):
        """Creates the master and slave databases and contents required for the test.

        At the end of this set up we will have We have two unique PlatformTypes on master, two unique
        on slave, one shared with same name and different GUID, and one shared with same name and
        same GUID.

        """

        self.master_store = DataStore("", "", "", 0, db_name="master.sqlite", db_type="sqlite")
        self.slave_store = DataStore("", "", "", 0, db_name="slave.sqlite", db_type="sqlite")

        self.master_store.initialise()
        self.slave_store.initialise()

        with self.master_store.session_scope():
            change_id = self.master_store.add_to_changes(
                "TEST", datetime.utcnow(), "TEST"
            ).change_id
            self.master_store.add_to_platform_types("PT_Master_1", change_id)
            self.master_store.add_to_platform_types("PT_Master_2", change_id)
            self.master_store.add_to_platform_types("PT_Shared_1", change_id)
            st_obj = self.master_store.add_to_platform_types("PT_Shared_2GUIDMatch", change_id)
            st_obj_guid = st_obj.platform_type_id

        with self.slave_store.session_scope():
            change_id = self.slave_store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id
            self.slave_store.add_to_platform_types("PT_Slave_1", change_id)
            self.slave_store.add_to_platform_types("PT_Slave_2", change_id)
            slave_shared_obj = self.slave_store.add_to_platform_types("PT_Shared_1", change_id)
            self.slave_shared_id = slave_shared_obj.platform_type_id
            st_obj_slave = self.slave_store.add_to_platform_types("PT_Shared_2GUIDMatch", change_id)
            st_obj_slave.platform_type_id = st_obj_guid
            self.slave_store.session.add(st_obj_slave)
            self.slave_store.session.commit()

            self.slave_store.add_to_nationalities("UK", change_id)
            self.slave_store.add_to_privacies("Private", change_id)
            self.slave_store.add_to_platforms(
                "Platform1", "UK", "PT_Shared_1", "Private", change_id=change_id
            )

    def tearDown(self):
        if os.path.exists("master.sqlite"):
            os.remove("master.sqlite")

        if os.path.exists("slave.sqlite"):
            os.remove("slave.sqlite")

    def test_platform_type_merge(self):
        # Do the merge
        id_results = merge_reference_table("PlatformType", self.master_store, self.slave_store)

        master_table = self.master_store.db_classes.PlatformType
        slave_table = self.slave_store.db_classes.PlatformType

        # Check there are now 6 rows in the master database
        results = self.master_store.session.query(master_table).all()
        assert len(results) == 6

        # Check the rows that were originally just in the slave db have been copied across
        # and that all their fields match (including GUID, but excluding created_date)
        master_results = (
            self.master_store.session.query(master_table)
            .filter(master_table.name.in_(["PT_Slave_1", "PT_Slave_2"]))
            .all()
        )
        slave_results = (
            self.slave_store.session.query(slave_table)
            .filter(slave_table.name.in_(["PT_Slave_1", "PT_Slave_2"]))
            .all()
        )

        assert check_sqlalchemy_results_are_equal(master_results, slave_results)

        assert slave_results[0].platform_type_id in id_results["added"]
        assert slave_results[1].platform_type_id in id_results["added"]

        # Check that the row that had the same name and same GUID in each db is still in both
        # databases
        master_results = (
            self.master_store.session.query(master_table)
            .filter(master_table.name == "PT_Shared_2GUIDMatch")
            .all()
        )
        slave_results = (
            self.slave_store.session.query(slave_table)
            .filter(slave_table.name == "PT_Shared_2GUIDMatch")
            .all()
        )

        assert check_sqlalchemy_results_are_equal(master_results, slave_results)

        assert id_results["already_there"] == [slave_results[0].platform_type_id]

        # Check that the row that had the same name but different GUID in each db now
        # matches in both databases
        master_results = (
            self.master_store.session.query(master_table)
            .filter(master_table.name == "PT_Shared_1")
            .all()
        )
        slave_results = (
            self.slave_store.session.query(slave_table)
            .filter(slave_table.name == "PT_Shared_1")
            .all()
        )
        new_guid = slave_results[0].platform_type_id

        assert check_sqlalchemy_results_are_equal(master_results, slave_results)

        assert id_results["modified"]["from"] == [self.slave_shared_id]
        assert id_results["modified"]["to"] == [new_guid]

        # Check that the new GUID for this row has propagated to the Platforms table in the slave database
        # (so we can copy this table later with no problems)
        results = (
            self.slave_store.session.query(self.slave_store.db_classes.Platform)
            .filter(self.slave_store.db_classes.Platform.platform_type_id == new_guid)
            .all()
        )

        assert len(results) == 1


class TestMergeAllReferenceTables(unittest.TestCase):
    def setUp(self):
        self.master_store = DataStore("", "", "", 0, db_name="master.sqlite", db_type="sqlite")
        self.slave_store = DataStore("", "", "", 0, db_name="slave.sqlite", db_type="sqlite")

        self.master_store.initialise()
        self.slave_store.initialise()

        with self.master_store.session_scope():
            change_id = self.master_store.add_to_changes(
                "TEST", datetime.utcnow(), "TEST"
            ).change_id
            self.master_store.add_to_nationalities("Nat_Master_1", change_id)
            self.master_store.add_to_nationalities("Nat_Master_2", change_id)
            self.master_store.add_to_nationalities("Nat_Shared_1", change_id)
            shared_obj = self.master_store.add_to_nationalities("Nat_Shared_2_SameGUID", change_id)
            shared_nat_guid = shared_obj.nationality_id

            self.master_store.add_to_comment_types("CT_Master_1", change_id)
            self.master_store.add_to_comment_types("CT_Master_2", change_id)
            self.master_store.add_to_comment_types("CT_Shared_1", change_id)
            shared_obj = self.master_store.add_to_comment_types("CT_Shared_2_SameGUID", change_id)
            shared_ct_guid = shared_obj.comment_type_id

            gt1 = self.master_store.db_classes.GeometryType(name="GeomType_Master_1")
            gt2 = self.master_store.db_classes.GeometryType(name="GeomType_Master_2")
            gt3 = self.master_store.db_classes.GeometryType(name="GeomType_Shared_1")
            self.master_store.session.add_all([gt1, gt2, gt3])
            self.master_store.session.commit()
            gst1 = self.master_store.db_classes.GeometrySubType(
                name="GST_Master_1", parent=gt1.geo_type_id
            )
            self.master_store.session.add(gst1)
            self.master_store.session.commit()

        with self.slave_store.session_scope():
            change_id = self.slave_store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id
            self.slave_store.add_to_nationalities("Nat_Slave_1", change_id)
            self.slave_store.add_to_nationalities("Nat_Slave_2", change_id)
            self.slave_store.add_to_nationalities("Nat_Shared_1", change_id)
            shared_nat_obj = self.slave_store.add_to_nationalities(
                "Nat_Shared_2_SameGUID", change_id
            )
            shared_nat_obj.nationality_id = shared_nat_guid
            self.slave_store.session.add(shared_nat_obj)
            self.slave_store.session.commit()

            self.slave_store.add_to_comment_types("CT_Slave_1", change_id)
            self.slave_store.add_to_comment_types("CT_Slave_2", change_id)
            self.slave_store.add_to_comment_types("CT_Shared_1", change_id)
            shared_ct_obj = self.slave_store.add_to_comment_types("CT_Shared_2_SameGUID", change_id)
            shared_ct_obj.comment_type_id = shared_ct_guid
            self.slave_store.session.add(shared_ct_obj)
            self.slave_store.session.commit()

            # Object that refers to nationality object
            self.slave_store.add_to_privacies("Private", change_id)
            self.slave_store.add_to_platform_types("PlatformType1", change_id)
            self.slave_store.add_to_platforms(
                "Platform1", "Nat_Shared_1", "PlatformType1", "Private", change_id=change_id
            )

            gt1 = self.slave_store.db_classes.GeometryType(name="GeomType_Slave_1")
            gt2 = self.slave_store.db_classes.GeometryType(name="GeomType_Slave_2")
            gt3 = self.slave_store.db_classes.GeometryType(name="GeomType_Shared_1")
            self.slave_store.session.add_all([gt1, gt2, gt3])
            self.slave_store.session.commit()
            gst1 = self.slave_store.db_classes.GeometrySubType(
                name="GST_Slave_1", parent=gt3.geo_type_id
            )
            self.slave_store.session.add(gst1)
            self.slave_store.session.commit()

    def tearDown(self):
        if os.path.exists("master.sqlite"):
            os.remove("master.sqlite")

        if os.path.exists("slave.sqlite"):
            os.remove("slave.sqlite")

    def test_merge_all_reference_tables(self):
        merge_all_reference_tables(self.master_store, self.slave_store)

        # Check there are the right number of rows for each table

        results = self.master_store.session.query(self.master_store.db_classes.Nationality).all()
        assert len(results) == 6

        results = self.master_store.session.query(self.master_store.db_classes.CommentType).all()
        assert len(results) == 6

        results = self.master_store.session.query(self.master_store.db_classes.GeometryType).all()
        assert len(results) == 5

        results = self.master_store.session.query(
            self.master_store.db_classes.GeometrySubType
        ).all()
        assert len(results) == 2

        # Check a few selected objects to make sure they're correct

        # Is there a GeometrySubType in master called GST_Slave_1, and does
        # it point to the GeomType_Shared_1 type as its parent
        gst_result = (
            self.master_store.session.query(self.master_store.db_classes.GeometrySubType)
            .filter(self.master_store.db_classes.GeometrySubType.name == "GST_Slave_1")
            .all()
        )

        gt_result = (
            self.master_store.session.query(self.master_store.db_classes.GeometryType)
            .filter(self.master_store.db_classes.GeometryType.name == "GeomType_Shared_1")
            .all()
        )

        assert len(gst_result) == 1
        assert len(gt_result) == 1

        assert gst_result[0].parent == gt_result[0].geo_type_id

        # Is there a Platform called Platform1 which refers to Nat_Shared_1 as its nationality, in
        # the slave db and is this referring to the same GUID as Nat_Shared_1 in the master db

        # Get platform obj
        results = (
            self.slave_store.session.query(self.slave_store.db_classes.Platform)
            .filter(self.slave_store.db_classes.Platform.name == "Platform1")
            .all()
        )

        # Check it has the right nationality name in the slave db
        assert results[0].nationality_name == "Nat_Shared_1"

        # Get the nationality GUID
        nat_guid = results[0].nationality.nationality_id

        # Search for that in the master db and check we get one result with correct name
        results = (
            self.slave_store.session.query(self.slave_store.db_classes.Nationality)
            .filter(self.slave_store.db_classes.Nationality.nationality_id == nat_guid)
            .all()
        )

        assert len(results) == 1
        assert results[0].name == "Nat_Shared_1"


class TestSensorPlatformMerge(unittest.TestCase):
    def setUp(self):
        self.master_store = DataStore("", "", "", 0, db_name="master.sqlite", db_type="sqlite")
        self.slave_store = DataStore("", "", "", 0, db_name="slave.sqlite", db_type="sqlite")

        self.master_store.initialise()
        self.slave_store.initialise()

        with self.master_store.session_scope():
            change_id = self.master_store.add_to_changes(
                "TEST", datetime.utcnow(), "TEST"
            ).change_id

            self.master_store.add_to_sensor_types("SensorType_Master_1", change_id)
            self.master_store.add_to_sensor_types("SensorType_Master_2", change_id)
            self.master_store.add_to_sensor_types("SensorType_Shared_1", change_id)
            st_shared = self.master_store.add_to_sensor_types(
                "SensorType_Shared_2_GUIDSame", change_id
            )
            st_shared_guid = st_shared.sensor_type_id

            self.master_store.add_to_platform_types("PlatformType_Master_1", change_id)
            self.master_store.add_to_platform_types("PlatformType_Shared_1", change_id)
            pt_shared = self.master_store.add_to_platform_types(
                "PlatformType_Shared_2_GUIDSame", change_id
            )
            pt_shared_guid = pt_shared.platform_type_id

            nat_shared = self.master_store.add_to_nationalities("UK", change_id)
            nat_shared_guid = nat_shared.nationality_id

            priv_shared = self.master_store.add_to_privacies("Private", change_id)
            priv_shared_guid = priv_shared.privacy_id

            self.master_store.session.add_all([st_shared, pt_shared, nat_shared, priv_shared])
            self.master_store.session.commit()

            self.master_store.add_to_platforms(
                "Platform_Master_1", "UK", "PlatformType_Master_1", "Private", change_id=change_id
            )
            self.master_store.add_to_platforms(
                "Platform_Shared_1", "UK", "PlatformType_Shared_1", "Private", change_id=change_id
            )

            self.master_store.add_to_sensors(
                "Sensor_Master_1", "SensorType_Master_1", "Platform_Master_1", "Private", change_id
            )
            self.master_store.add_to_sensors(
                "Sensor_Master_2", "SensorType_Shared_1", "Platform_Master_1", "Private", change_id
            )
            self.master_store.add_to_sensors(
                "Sensor_Master_3", "SensorType_Master_2", "Platform_Shared_1", "Private", change_id
            )
            self.master_store.add_to_sensors(
                "Sensor_Shared_1", "SensorType_Shared_1", "Platform_Shared_1", "Private", change_id
            )
            sensor_shared = self.master_store.add_to_sensors(
                "Sensor_Shared_2_GUIDSame",
                "SensorType_Shared_1",
                "Platform_Shared_1",
                "Private",
                change_id,
            )
            sensor_shared_guid = sensor_shared.sensor_id

        with self.slave_store.session_scope():
            change_id = self.slave_store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id

            self.slave_store.add_to_sensor_types("SensorType_Slave_1", change_id)
            self.slave_store.add_to_sensor_types("SensorType_Slave_2", change_id)
            self.slave_store.add_to_sensor_types("SensorType_Shared_1", change_id)
            st_shared = self.slave_store.add_to_sensor_types(
                "SensorType_Shared_2_GUIDSame", change_id
            )
            st_shared.sensor_type_id = st_shared_guid

            self.slave_store.add_to_platform_types("PlatformType_Slave_1", change_id)
            self.slave_store.add_to_platform_types("PlatformType_Shared_1", change_id)
            pt_shared = self.slave_store.add_to_platform_types(
                "PlatformType_Shared_2_GUIDSame", change_id
            )
            pt_shared.platform_type_id = pt_shared_guid

            nat_shared = self.slave_store.add_to_nationalities("UK", change_id)
            nat_shared.nationality_id = nat_shared_guid

            priv_shared = self.slave_store.add_to_privacies("Private", change_id)
            priv_shared.privacy_id = priv_shared_guid

            self.slave_store.session.add_all([st_shared, pt_shared, nat_shared, priv_shared])
            self.slave_store.session.commit()

            self.slave_store.add_to_platforms(
                "Platform_Slave_1", "UK", "PlatformType_Slave_1", "Private", change_id=change_id
            )
            self.slave_store.add_to_platforms(
                "Platform_Shared_1", "UK", "PlatformType_Shared_1", "Private", change_id=change_id
            )

            self.slave_store.add_to_sensors(
                "Sensor_Slave_1", "SensorType_Slave_1", "Platform_Slave_1", "Private", change_id
            )
            self.slave_store.add_to_sensors(
                "Sensor_Slave_2", "SensorType_Shared_1", "Platform_Slave_1", "Private", change_id
            )
            self.slave_store.add_to_sensors(
                "Sensor_Slave_3", "SensorType_Slave_2", "Platform_Shared_1", "Private", change_id
            )
            self.slave_store.add_to_sensors(
                "Sensor_Shared_1", "SensorType_Shared_1", "Platform_Shared_1", "Private", change_id
            )
            sensor_shared = self.slave_store.add_to_sensors(
                "Sensor_Shared_2_GUIDSame",
                "SensorType_Shared_1",
                "Platform_Shared_1",
                "Private",
                change_id,
            )
            sensor_shared.sensor_id = sensor_shared_guid

            self.slave_store.session.add(sensor_shared)
            self.slave_store.session.commit()

    def tearDown(self):
        if os.path.exists("master.sqlite"):
            os.remove("master.sqlite")

        if os.path.exists("slave.sqlite"):
            os.remove("slave.sqlite")

    def test_sensor_platform_merge(self):
        with self.master_store.session_scope():
            merge_change_id = self.master_store.add_to_changes(
                user=getuser(),
                modified=datetime.utcnow(),
                reason=f"Merging from database {self.slave_store.db_name}",
            ).change_id

        # Must merge reference tables first, so we can ensure foreign key integrity
        merge_all_reference_tables(self.master_store, self.slave_store)

        # Do the actual merge of the metadata tables
        merge_all_metadata_tables(self.master_store, self.slave_store, merge_change_id)

        # Check there are the right number of entries in each table
        results = self.master_store.session.query(self.master_store.db_classes.SensorType).all()
        assert len(results) == 6

        results = self.master_store.session.query(self.master_store.db_classes.PlatformType).all()
        assert len(results) == 4

        results = self.master_store.session.query(self.master_store.db_classes.Nationality).all()
        assert len(results) == 1

        results = self.master_store.session.query(self.master_store.db_classes.Privacy).all()
        assert len(results) == 1

        results = self.master_store.session.query(self.master_store.db_classes.Platform).all()
        assert len(results) == 3

        results = self.master_store.session.query(self.master_store.db_classes.Sensor).all()
        assert len(results) == 8

        # Check values of metadata tables

        # Check we have a Platform called Platform_Slave_1 that references a Platform Type of PlatformType_Slave_1
        master_platform_results = (
            self.master_store.session.query(self.master_store.db_classes.Platform)
            .filter(self.master_store.db_classes.Platform.name == "Platform_Slave_1")
            .all()
        )

        slave_pt_results = (
            self.slave_store.session.query(self.slave_store.db_classes.PlatformType)
            .filter(self.slave_store.db_classes.PlatformType.name == "PlatformType_Slave_1")
            .all()
        )

        assert len(master_platform_results) == 1
        assert len(slave_pt_results) == 1

        assert master_platform_results[0].platform_type_name == "PlatformType_Slave_1"
        assert (
            master_platform_results[0].platform_type.platform_type_id
            == slave_pt_results[0].platform_type_id
        )

        # Check we have a Sensor called Sensor_Slave_1 in the master db now, with the right details
        master_sensor_results = (
            self.master_store.session.query(self.master_store.db_classes.Sensor)
            .filter(self.master_store.db_classes.Sensor.name == "Sensor_Slave_1")
            .all()
        )

        master_st_results = (
            self.master_store.session.query(self.master_store.db_classes.SensorType)
            .filter(self.master_store.db_classes.SensorType.name == "SensorType_Slave_1")
            .all()
        )

        slave_st_results = (
            self.slave_store.session.query(self.slave_store.db_classes.SensorType)
            .filter(self.slave_store.db_classes.SensorType.name == "SensorType_Slave_1")
            .all()
        )

        assert len(master_sensor_results) == 1

        assert master_sensor_results[0].host == master_platform_results[0].platform_id
        assert master_sensor_results[0].sensor_type_id == master_st_results[0].sensor_type_id
        assert master_sensor_results[0].sensor_type_id == slave_st_results[0].sensor_type_id

        # Check we have a Sensor called Sensor_Shared_1 in both dbs, and all fields match
        master_results = (
            self.master_store.session.query(self.master_store.db_classes.Sensor)
            .filter(self.master_store.db_classes.Sensor.name == "Sensor_Shared_1")
            .all()
        )

        slave_results = (
            self.slave_store.session.query(self.slave_store.db_classes.Sensor)
            .filter(self.slave_store.db_classes.Sensor.name == "Sensor_Shared_1")
            .all()
        )

        assert check_sqlalchemy_results_are_equal(master_results, slave_results)


class TestMergeDatafiles(unittest.TestCase):
    def setUp(self):
        self.master_store = DataStore("", "", "", 0, db_name="master.sqlite", db_type="sqlite")
        self.slave_store = DataStore("", "", "", 0, db_name="slave.sqlite", db_type="sqlite")

        self.master_store.initialise()
        self.slave_store.initialise()

        with self.master_store.session_scope():
            change_id = self.master_store.add_to_changes(
                "TEST", datetime.utcnow(), "TEST"
            ).change_id

            self.master_store.add_to_privacies("Private", change_id)
            self.master_store.add_to_datafile_types("DFT1", change_id)

            self.master_store.add_to_datafiles(
                "Private",
                "DFT1",
                reference="Master_DF_1",
                file_hash="Master_DF_1_Hash",
                file_size=1,
                change_id=change_id,
            )
            self.master_store.add_to_datafiles(
                "Private",
                "DFT1",
                reference="Master_DF_2",
                file_hash="Master_DF_2_Hash",
                file_size=1,
                change_id=change_id,
            )
            self.master_store.add_to_datafiles(
                "Private",
                "DFT1",
                reference="Shared_DF_1",
                file_hash="Shared_DF_1_Hash",
                file_size=1,
                change_id=change_id,
            )
            df_obj = self.master_store.add_to_datafiles(
                "Private",
                "DFT1",
                reference="Shared_DF_2_GUIDSame",
                file_hash="Shared_DF_2_GUIDSame_Hash",
                file_size=1,
                change_id=change_id,
            )
            shared_guid = df_obj.datafile_id

        with self.slave_store.session_scope():
            change_id = self.slave_store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id

            self.slave_store.add_to_privacies("Private", change_id)
            self.slave_store.add_to_datafile_types("DFT1", change_id)

            self.slave_store.add_to_datafiles(
                "Private",
                "DFT1",
                reference="Slave_DF_1",
                file_hash="Slave_DF_1_Hash",
                file_size=1,
                change_id=change_id,
            )
            self.slave_store.add_to_datafiles(
                "Private",
                "DFT1",
                reference="Slave_DF_2",
                file_hash="Slave_DF_2_Hash",
                file_size=1,
                change_id=change_id,
            )
            shared_df = self.slave_store.add_to_datafiles(
                "Private",
                "DFT1",
                reference="Shared_DF_1",
                file_hash="Shared_DF_1_Hash",
                file_size=1,
                change_id=change_id,
            )
            self.shared_guid = shared_df.datafile_id
            df_obj = self.slave_store.add_to_datafiles(
                "Private",
                "DFT1",
                reference="Shared_DF_2_GUIDSame",
                file_hash="Shared_DF_2_GUIDSame_Hash",
                file_size=1,
                change_id=change_id,
            )
            df_obj.datafile_id = shared_guid
            self.slave_store.session.add(df_obj)
            self.slave_store.session.commit()

    def tearDown(self):
        if os.path.exists("master.sqlite"):
            os.remove("master.sqlite")

        if os.path.exists("slave.sqlite"):
            os.remove("slave.sqlite")

    def test_merge_data_files(self):
        with self.master_store.session_scope():
            merge_change_id = self.master_store.add_to_changes(
                user=getuser(),
                modified=datetime.utcnow(),
                reason=f"Merging from database {self.slave_store.db_name}",
            ).change_id

        merge_all_reference_tables(self.master_store, self.slave_store)

        id_results = merge_metadata_table(
            "Datafile", self.master_store, self.slave_store, merge_change_id
        )

        # Check there are the right number of entries in the master database
        results = self.master_store.session.query(self.master_store.db_classes.Datafile).all()
        assert len(results) == 6

        # Check there are the right number of IDs in each section of the ID results
        assert len(id_results["already_there"]) == 1
        assert len(id_results["added"]) == 2
        assert len(id_results["modified"]["from"]) == 1

        # Check we have an entry called Slave_DF_1 in master now
        results = (
            self.master_store.session.query(self.master_store.db_classes.Datafile)
            .filter(self.master_store.db_classes.Datafile.reference == "Slave_DF_1")
            .all()
        )

        assert len(results) == 1
        assert results[0].datafile_id in id_results["added"]

        # Check that we mark the Shared_DF_2_GUIDSame entry as already there
        results = (
            self.master_store.session.query(self.master_store.db_classes.Datafile)
            .filter(self.master_store.db_classes.Datafile.reference == "Shared_DF_2_GUIDSame")
            .all()
        )

        assert len(results) == 1
        assert results[0].datafile_id in id_results["already_there"]

        # Check that the GUID for Shared_DF_1 matches in both databases, and is correctly in the
        # from and to sections of the list of modified IDs
        master_results = (
            self.master_store.session.query(self.master_store.db_classes.Datafile)
            .filter(self.master_store.db_classes.Datafile.reference == "Shared_DF_1")
            .all()
        )
        slave_results = (
            self.slave_store.session.query(self.slave_store.db_classes.Datafile)
            .filter(self.slave_store.db_classes.Datafile.reference == "Shared_DF_1")
            .all()
        )

        assert len(master_results) == 1
        assert len(slave_results) == 1

        assert check_sqlalchemy_results_are_equal(master_results, slave_results)

        assert self.shared_guid in id_results["modified"]["from"]
        assert master_results[0].datafile_id in id_results["modified"]["to"]


class TestMergeStateFromImport(unittest.TestCase):
    def setUp(self):
        """This gets us to the situation where the master db has an import of gpx_1_0.gpx
        and rep_test1.rep, and the slave db has an import of gpx_1_0.gpx and uk_track.rep."""

        self.master_store = DataStore("", "", "", 0, db_name="master.sqlite", db_type="sqlite")
        self.slave_store = DataStore("", "", "", 0, db_name="slave.sqlite", db_type="sqlite")

        self.master_store.initialise()
        self.slave_store.initialise()

        # Import two files into master
        processor = FileProcessor(archive=False)
        processor.load_importers_dynamically()
        processor.process(
            os.path.join(SAMPLE_DATA_PATH, "track_files", "gpx", "gpx_1_0.gpx"),
            self.master_store,
            False,
        )
        processor.process(
            os.path.join(SAMPLE_DATA_PATH, "track_files", "rep_data", "rep_test1.rep"),
            self.master_store,
            False,
        )

        with self.master_store.session_scope():
            results = (
                self.master_store.session.query(self.master_store.db_classes.State)
                .filter(self.master_store.db_classes.State.source_reference == "gpx_1_0.gpx")
                .all()
            )
            self.master_gpx_states = [
                sqlalchemy_obj_to_dict(item, remove_id=True) for item in results
            ]

        # Import two files into slave
        processor = FileProcessor(archive=False)
        processor.load_importers_dynamically()
        processor.process(
            os.path.join(SAMPLE_DATA_PATH, "track_files", "gpx", "gpx_1_0.gpx"),
            self.slave_store,
            False,
        )
        processor.process(
            os.path.join(SAMPLE_DATA_PATH, "track_files", "rep_data", "uk_track.rep"),
            self.slave_store,
            False,
        )

    def tearDown(self):
        if os.path.exists("master.sqlite"):
            os.remove("master.sqlite")

        if os.path.exists("slave.sqlite"):
            os.remove("slave.sqlite")

    def test_merge_state_from_import(self):
        merge_all_tables(self.master_store, self.slave_store)

        with self.master_store.session_scope():
            with self.slave_store.session_scope():
                # Check the datafiles table in master has the right number of rows
                results = self.master_store.session.query(
                    self.master_store.db_classes.Datafile
                ).all()
                assert len(results) == 3

                # Check the datafiles table in master has uk_track.rep in it
                results = (
                    self.master_store.session.query(self.master_store.db_classes.Datafile)
                    .filter(self.master_store.db_classes.Datafile.reference == "uk_track.rep")
                    .all()
                )
                assert len(results) == 1

                # Check all of the state entries from slave uk_track.rep are in master - with all of their columns having the same value
                master_results = (
                    self.master_store.session.query(self.master_store.db_classes.State)
                    .filter(self.master_store.db_classes.State.source_reference == "uk_track.rep")
                    .all()
                )
                slave_results = (
                    self.slave_store.session.query(self.slave_store.db_classes.State)
                    .filter(self.slave_store.db_classes.State.source_reference == "uk_track.rep")
                    .all()
                )

                assert check_sqlalchemy_results_are_equal(master_results, slave_results)

                # Check that the gpx_1_0.gpx entries haven't been duplicated

                # Specifically, check the original in master hasn't been touched
                results = (
                    self.master_store.session.query(self.master_store.db_classes.State)
                    .filter(self.master_store.db_classes.State.source_reference == "gpx_1_0.gpx")
                    .all()
                )
                new_master_gpx_states = [
                    sqlalchemy_obj_to_dict(item, remove_id=True) for item in results
                ]

                assert self.master_gpx_states == new_master_gpx_states

                # Check the slave and master copies match - except for their IDs which will be different
                slave_gpx_results = (
                    self.slave_store.session.query(self.slave_store.db_classes.State)
                    .filter(self.slave_store.db_classes.State.source_reference == "gpx_1_0.gpx")
                    .all()
                )
                slave_gpx_results = [
                    sqlalchemy_obj_to_dict(item, remove_id=True) for item in slave_gpx_results
                ]

                assert self.master_gpx_states == slave_gpx_results

                # Check there aren't extra copies by counting the number of entries associated with the reference gpx_1_0.gpx
                results = (
                    self.master_store.session.query(self.master_store.db_classes.State)
                    .filter(self.master_store.db_classes.State.source_reference == "gpx_1_0.gpx")
                    .all()
                )
                assert len(results) == len(self.master_gpx_states)


@pytest.mark.postgres
class TestMergeStateFromImport_Postgres(unittest.TestCase):
    def setUp(self):
        """This gets us to the situation where the master db has an import of gpx_1_0.gpx
        and rep_test1.rep, and the slave db has an import of gpx_1_0.gpx and uk_track.rep."""
        self.postgres = None

        try:
            self.postgres = Postgresql(
                database="test", host="localhost", user="postgres", password="postgres", port=55527,
            )
        except RuntimeError:
            print("PostgreSQL database couldn't be created! Test is skipping.")
            return

        self.master_store = DataStore(
            db_name="test",
            db_host="localhost",
            db_username="postgres",
            db_password="postgres",
            db_port=55527,
            db_type="postgres",
        )
        self.slave_store = DataStore("", "", "", 0, db_name="slave.sqlite", db_type="sqlite")

        self.master_store.initialise()
        self.slave_store.initialise()

        # Import two files into master
        processor = FileProcessor(archive=False)
        processor.load_importers_dynamically()
        processor.process(
            os.path.join(SAMPLE_DATA_PATH, "track_files", "gpx", "gpx_1_0.gpx"),
            self.master_store,
            False,
        )
        processor.process(
            os.path.join(SAMPLE_DATA_PATH, "track_files", "rep_data", "rep_test1.rep"),
            self.master_store,
            False,
        )

        with self.master_store.session_scope():
            results = (
                self.master_store.session.query(self.master_store.db_classes.State)
                .filter(self.master_store.db_classes.State.source_reference == "gpx_1_0.gpx")
                .all()
            )
            self.master_gpx_states = [
                sqlalchemy_obj_to_dict(item, remove_id=True) for item in results
            ]

        # Import two files into slave
        processor = FileProcessor(archive=False)
        processor.load_importers_dynamically()
        processor.process(
            os.path.join(SAMPLE_DATA_PATH, "track_files", "gpx", "gpx_1_0.gpx"),
            self.slave_store,
            False,
        )
        processor.process(
            os.path.join(SAMPLE_DATA_PATH, "track_files", "rep_data", "uk_track.rep"),
            self.slave_store,
            False,
        )

    def tearDown(self):
        try:
            self.postgres.stop()
        except AttributeError:
            return

        if os.path.exists("slave.sqlite"):
            os.remove("slave.sqlite")

    def test_merge_state_from_import(self):
        merge_all_tables(self.master_store, self.slave_store)

        with self.master_store.session_scope():
            with self.slave_store.session_scope():
                # Check the datafiles table in master has the right number of rows
                results = self.master_store.session.query(
                    self.master_store.db_classes.Datafile
                ).all()
                assert len(results) == 3

                # Check the datafiles table in master has uk_track.rep in it
                results = (
                    self.master_store.session.query(self.master_store.db_classes.Datafile)
                    .filter(self.master_store.db_classes.Datafile.reference == "uk_track.rep")
                    .all()
                )
                assert len(results) == 1

                # Check all of the state entries from slave uk_track.rep are in master - with all of their columns having the same value
                master_results = (
                    self.master_store.session.query(self.master_store.db_classes.State)
                    .filter(self.master_store.db_classes.State.source_reference == "uk_track.rep")
                    .all()
                )
                slave_results = (
                    self.slave_store.session.query(self.slave_store.db_classes.State)
                    .filter(self.slave_store.db_classes.State.source_reference == "uk_track.rep")
                    .all()
                )

                assert check_sqlalchemy_results_are_equal(master_results, slave_results)

                # Check that the gpx_1_0.gpx entries haven't been duplicated

                # Specifically, check the original in master hasn't been touched
                results = (
                    self.master_store.session.query(self.master_store.db_classes.State)
                    .filter(self.master_store.db_classes.State.source_reference == "gpx_1_0.gpx")
                    .all()
                )
                new_master_gpx_states = [
                    sqlalchemy_obj_to_dict(item, remove_id=True) for item in results
                ]

                assert self.master_gpx_states == new_master_gpx_states

                # Check the slave and master copies match - except for their IDs which will be different
                slave_gpx_results = (
                    self.slave_store.session.query(self.slave_store.db_classes.State)
                    .filter(self.slave_store.db_classes.State.source_reference == "gpx_1_0.gpx")
                    .all()
                )
                slave_gpx_results = [
                    sqlalchemy_obj_to_dict(item, remove_id=True) for item in slave_gpx_results
                ]

                assert self.master_gpx_states == slave_gpx_results

                # Check there aren't extra copies by counting the number of entries associated with the reference gpx_1_0.gpx
                results = (
                    self.master_store.session.query(self.master_store.db_classes.State)
                    .filter(self.master_store.db_classes.State.source_reference == "gpx_1_0.gpx")
                    .all()
                )
                assert len(results) == len(self.master_gpx_states)


class TestMergeStateFromImport_Indempotent_SameFile(unittest.TestCase):
    def setUp(self):
        """This gets us to the situation where the master db has an import of gpx_1_0.gpx
        and rep_test1.rep, and the slave db has an import of gpx_1_0.gpx and uk_track.rep."""

        self.master_store = DataStore("", "", "", 0, db_name="master.sqlite", db_type="sqlite")
        self.slave_store = DataStore("", "", "", 0, db_name="slave.sqlite", db_type="sqlite")

        self.master_store.initialise()
        self.slave_store.initialise()

        # Import two files into master
        processor = FileProcessor(archive=False)
        processor.load_importers_dynamically()
        processor.process(
            os.path.join(SAMPLE_DATA_PATH, "track_files", "gpx", "gpx_1_0.gpx"),
            self.master_store,
            False,
        )
        processor.process(
            os.path.join(SAMPLE_DATA_PATH, "track_files", "rep_data", "rep_test1.rep"),
            self.master_store,
            False,
        )

        with self.master_store.session_scope():
            results = (
                self.master_store.session.query(self.master_store.db_classes.State)
                .filter(self.master_store.db_classes.State.source_reference == "gpx_1_0.gpx")
                .all()
            )
            self.master_gpx_states = [
                sqlalchemy_obj_to_dict(item, remove_id=True) for item in results
            ]

        # Import two files into slave
        processor = FileProcessor(archive=False)
        processor.load_importers_dynamically()
        processor.process(
            os.path.join(SAMPLE_DATA_PATH, "track_files", "gpx", "gpx_1_0.gpx"),
            self.slave_store,
            False,
        )
        processor.process(
            os.path.join(SAMPLE_DATA_PATH, "track_files", "rep_data", "uk_track.rep"),
            self.slave_store,
            False,
        )

    def tearDown(self):
        if os.path.exists("master.sqlite"):
            os.remove("master.sqlite")

        if os.path.exists("slave.sqlite"):
            os.remove("slave.sqlite")

    def do_checks(self):
        with self.master_store.session_scope():
            with self.slave_store.session_scope():
                # Check the datafiles table in master has the right number of rows
                results = self.master_store.session.query(
                    self.master_store.db_classes.Datafile
                ).all()
                assert len(results) == 3

                # Check the datafiles table in master has uk_track.rep in it
                results = (
                    self.master_store.session.query(self.master_store.db_classes.Datafile)
                    .filter(self.master_store.db_classes.Datafile.reference == "uk_track.rep")
                    .all()
                )
                assert len(results) == 1

                # Check all of the state entries from slave uk_track.rep are in master - with all of their columns having the same value
                master_results = (
                    self.master_store.session.query(self.master_store.db_classes.State)
                    .filter(self.master_store.db_classes.State.source_reference == "uk_track.rep")
                    .all()
                )
                slave_results = (
                    self.slave_store.session.query(self.slave_store.db_classes.State)
                    .filter(self.slave_store.db_classes.State.source_reference == "uk_track.rep")
                    .all()
                )

                assert check_sqlalchemy_results_are_equal(master_results, slave_results)

                # Check that the gpx_1_0.gpx entries haven't been duplicated

                # Specifically, check the original in master hasn't been touched
                results = (
                    self.master_store.session.query(self.master_store.db_classes.State)
                    .filter(self.master_store.db_classes.State.source_reference == "gpx_1_0.gpx")
                    .all()
                )
                new_master_gpx_states = [
                    sqlalchemy_obj_to_dict(item, remove_id=True) for item in results
                ]

                assert self.master_gpx_states == new_master_gpx_states

                # Check the slave and master copies match - except for their IDs which will be different
                slave_gpx_results = (
                    self.slave_store.session.query(self.slave_store.db_classes.State)
                    .filter(self.slave_store.db_classes.State.source_reference == "gpx_1_0.gpx")
                    .all()
                )
                slave_gpx_results = [
                    sqlalchemy_obj_to_dict(item, remove_id=True) for item in slave_gpx_results
                ]

                assert self.master_gpx_states == slave_gpx_results

                # Check there aren't extra copies by counting the number of entries associated with the reference gpx_1_0.gpx
                results = (
                    self.master_store.session.query(self.master_store.db_classes.State)
                    .filter(self.master_store.db_classes.State.source_reference == "gpx_1_0.gpx")
                    .all()
                )
                assert len(results) == len(self.master_gpx_states)

    def test_merge_state_from_import_indempotent_with_altering(self):
        merge_all_tables(self.master_store, self.slave_store)

        self.do_checks()

        # Run again and check all the tests still pass
        merge_all_tables(self.master_store, self.slave_store)

        self.do_checks()


class TestMergeStateFromImport_Indempotent_DifferentFile(unittest.TestCase):
    def setUp(self):
        """This gets us to the situation where the master db has an import of gpx_1_0.gpx
        and rep_test1.rep, and the slave db has an import of gpx_1_0.gpx and uk_track.rep."""

        self.master_store = DataStore("", "", "", 0, db_name="master.sqlite", db_type="sqlite")
        self.slave_store = DataStore("", "", "", 0, db_name="slave.sqlite", db_type="sqlite")

        self.master_store.initialise()
        self.slave_store.initialise()

        # Import two files into master
        processor = FileProcessor(archive=False)
        processor.load_importers_dynamically()
        processor.process(
            os.path.join(SAMPLE_DATA_PATH, "track_files", "gpx", "gpx_1_0.gpx"),
            self.master_store,
            False,
        )
        processor.process(
            os.path.join(SAMPLE_DATA_PATH, "track_files", "rep_data", "rep_test1.rep"),
            self.master_store,
            False,
        )

        with self.master_store.session_scope():
            results = (
                self.master_store.session.query(self.master_store.db_classes.State)
                .filter(self.master_store.db_classes.State.source_reference == "gpx_1_0.gpx")
                .all()
            )
            self.master_gpx_states = [
                sqlalchemy_obj_to_dict(item, remove_id=True) for item in results
            ]

        # Import two files into slave
        processor = FileProcessor(archive=False)
        processor.load_importers_dynamically()
        processor.process(
            os.path.join(SAMPLE_DATA_PATH, "track_files", "gpx", "gpx_1_0.gpx"),
            self.slave_store,
            False,
        )
        processor.process(
            os.path.join(SAMPLE_DATA_PATH, "track_files", "rep_data", "uk_track.rep"),
            self.slave_store,
            False,
        )

        shutil.copyfile("slave.sqlite", "slave_orig.sqlite")

    def tearDown(self):
        if os.path.exists("master.sqlite"):
            os.remove("master.sqlite")

        if os.path.exists("slave.sqlite"):
            os.remove("slave.sqlite")

    def do_checks(self):
        with self.master_store.session_scope():
            with self.slave_store.session_scope():
                # Check the datafiles table in master has the right number of rows
                results = self.master_store.session.query(
                    self.master_store.db_classes.Datafile
                ).all()
                assert len(results) == 3

                # Check the datafiles table in master has uk_track.rep in it
                results = (
                    self.master_store.session.query(self.master_store.db_classes.Datafile)
                    .filter(self.master_store.db_classes.Datafile.reference == "uk_track.rep")
                    .all()
                )
                assert len(results) == 1

                # Check all of the state entries from slave uk_track.rep are in master - with all of their columns having the same value
                master_results = (
                    self.master_store.session.query(self.master_store.db_classes.State)
                    .filter(self.master_store.db_classes.State.source_reference == "uk_track.rep")
                    .all()
                )
                slave_results = (
                    self.slave_store.session.query(self.slave_store.db_classes.State)
                    .filter(self.slave_store.db_classes.State.source_reference == "uk_track.rep")
                    .all()
                )

                assert check_sqlalchemy_results_are_equal(master_results, slave_results)

                # Check that the gpx_1_0.gpx entries haven't been duplicated

                # Specifically, check the original in master hasn't been touched
                results = (
                    self.master_store.session.query(self.master_store.db_classes.State)
                    .filter(self.master_store.db_classes.State.source_reference == "gpx_1_0.gpx")
                    .all()
                )
                new_master_gpx_states = [
                    sqlalchemy_obj_to_dict(item, remove_id=True) for item in results
                ]

                assert self.master_gpx_states == new_master_gpx_states

                # Check the slave and master copies match - except for their IDs which will be different
                slave_gpx_results = (
                    self.slave_store.session.query(self.slave_store.db_classes.State)
                    .filter(self.slave_store.db_classes.State.source_reference == "gpx_1_0.gpx")
                    .all()
                )
                slave_gpx_results = [
                    sqlalchemy_obj_to_dict(item, remove_id=True) for item in slave_gpx_results
                ]

                assert self.master_gpx_states == slave_gpx_results

                # Check there aren't extra copies by counting the number of entries associated with the reference gpx_1_0.gpx
                results = (
                    self.master_store.session.query(self.master_store.db_classes.State)
                    .filter(self.master_store.db_classes.State.source_reference == "gpx_1_0.gpx")
                    .all()
                )
                assert len(results) == len(self.master_gpx_states)

    def test_merge_state_from_import_indempotent_with_altering(self):
        merge_all_tables(self.master_store, self.slave_store)

        self.do_checks()

        # Run again merging from the original sqlite file
        # that hasn't been altered by the merge process
        new_slave_store = DataStore("", "", "", 0, db_name="slave_orig.sqlite", db_type="sqlite")
        merge_all_tables(self.master_store, new_slave_store)

        self.do_checks()


class TestSynonymMergeWithRefTable(unittest.TestCase):
    def setUp(self):
        if os.path.exists("master.sqlite"):
            os.remove("master.sqlite")

        if os.path.exists("slave.sqlite"):
            os.remove("slave.sqlite")

        self.master_store = DataStore("", "", "", 0, db_name="master.sqlite", db_type="sqlite")
        self.slave_store = DataStore("", "", "", 0, db_name="slave.sqlite", db_type="sqlite")

        self.master_store.initialise()
        self.slave_store.initialise()

        with self.master_store.session_scope():
            change_id = self.master_store.add_to_changes(
                "TEST", datetime.utcnow(), "TEST"
            ).change_id
            self.master_store.add_to_sensor_types("ST_Master_1", change_id)
            self.master_store.add_to_sensor_types("ST_Master_2", change_id)
            self.master_store.add_to_sensor_types("ST_Shared_1", change_id)
            st_obj = self.master_store.add_to_sensor_types("ST_Shared_2GUIDMatch", change_id)
            st_obj_guid = st_obj.sensor_type_id

        with self.slave_store.session_scope():
            change_id = self.slave_store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id
            self.slave_store.add_to_sensor_types("ST_Slave_1", change_id)
            self.slave_store.add_to_sensor_types("ST_Slave_2", change_id)
            slave_shared_obj = self.slave_store.add_to_sensor_types("ST_Shared_1", change_id)
            self.slave_shared_id = slave_shared_obj.sensor_type_id
            st_obj_slave = self.slave_store.add_to_sensor_types("ST_Shared_2GUIDMatch", change_id)
            st_obj_slave.sensor_type_id = st_obj_guid
            self.slave_store.session.add(st_obj_slave)
            self.slave_store.session.commit()

            self.slave_store.add_to_platform_types("PlatformType1", change_id)
            self.slave_store.add_to_nationalities("UK", change_id)
            self.slave_store.add_to_privacies("Private", change_id)
            self.slave_store.add_to_platforms(
                "Platform1", "UK", "PlatformType1", "Private", change_id=change_id
            )
            self.slave_store.add_to_sensors(
                "Sensor1", "ST_Shared_1", "Platform1", "Private", change_id
            )

            self.slave_store.add_to_synonyms(
                "SensorTypes", "ST_Shared_1_Synonym", slave_shared_obj.sensor_type_id, change_id
            )

    def tearDown(self):
        if os.path.exists("master.sqlite"):
            os.remove("master.sqlite")

        if os.path.exists("slave.sqlite"):
            os.remove("slave.sqlite")

    def test_synonym_merge_reference_table(self):
        with self.master_store.session_scope():
            merge_change_id = self.master_store.add_to_changes(
                user=getuser(),
                modified=datetime.utcnow(),
                reason=f"Merging from database {self.slave_store.db_name}",
            ).change_id

        # Do the merge
        merge_all_reference_tables(self.master_store, self.slave_store)
        merge_metadata_table("Synonym", self.master_store, self.slave_store, merge_change_id)

        with self.master_store.session_scope():
            # Check the synonym entry from the slave is now in master
            slave_results = self.slave_store.session.query(
                self.slave_store.db_classes.Synonym
            ).all()
            master_results = self.master_store.session.query(
                self.master_store.db_classes.Synonym
            ).all()

            assert check_sqlalchemy_results_are_equal(master_results, slave_results)

            # Check the synonym entry in master points to a SensorType in master
            results = self.master_store.session.query(self.master_store.db_classes.Synonym).all()

            assert len(results) > 0

            results = (
                self.master_store.session.query(self.master_store.db_classes.SensorType)
                .filter(self.master_store.db_classes.SensorType.sensor_type_id == results[0].entity)
                .all()
            )

            assert len(results) > 0


class TestSynonymMergeWithMetadataTable(unittest.TestCase):
    def setUp(self):
        self.master_store = DataStore("", "", "", 0, db_name="master.sqlite", db_type="sqlite")
        self.slave_store = DataStore("", "", "", 0, db_name="slave.sqlite", db_type="sqlite")

        self.master_store.initialise()
        self.slave_store.initialise()

        with self.master_store.session_scope():
            change_id = self.master_store.add_to_changes(
                "TEST", datetime.utcnow(), "TEST"
            ).change_id

            self.master_store.add_to_sensor_types("SensorType_Master_1", change_id)
            self.master_store.add_to_sensor_types("SensorType_Master_2", change_id)
            self.master_store.add_to_sensor_types("SensorType_Shared_1", change_id)
            st_shared = self.master_store.add_to_sensor_types(
                "SensorType_Shared_2_GUIDSame", change_id
            )
            st_shared_guid = st_shared.sensor_type_id

            self.master_store.add_to_platform_types("PlatformType_Master_1", change_id)
            self.master_store.add_to_platform_types("PlatformType_Shared_1", change_id)
            pt_shared = self.master_store.add_to_platform_types(
                "PlatformType_Shared_2_GUIDSame", change_id
            )
            pt_shared_guid = pt_shared.platform_type_id

            nat_shared = self.master_store.add_to_nationalities("UK", change_id)
            nat_shared_guid = nat_shared.nationality_id

            priv_shared = self.master_store.add_to_privacies("Private", change_id)
            priv_shared_guid = priv_shared.privacy_id

            self.master_store.session.add_all([st_shared, pt_shared, nat_shared, priv_shared])
            self.master_store.session.commit()

            self.master_store.add_to_platforms(
                "Platform_Master_1", "UK", "PlatformType_Master_1", "Private", change_id=change_id
            )
            self.master_store.add_to_platforms(
                "Platform_Shared_1", "UK", "PlatformType_Shared_1", "Private", change_id=change_id
            )

            sensor_master_1 = self.master_store.add_to_sensors(
                "Sensor_Master_1", "SensorType_Master_1", "Platform_Master_1", "Private", change_id
            )
            self.master_store.add_to_sensors(
                "Sensor_Master_2", "SensorType_Shared_1", "Platform_Master_1", "Private", change_id
            )
            self.master_store.add_to_sensors(
                "Sensor_Master_3", "SensorType_Master_2", "Platform_Shared_1", "Private", change_id
            )
            self.master_store.add_to_sensors(
                "Sensor_Shared_1", "SensorType_Shared_1", "Platform_Shared_1", "Private", change_id
            )
            sensor_shared = self.master_store.add_to_sensors(
                "Sensor_Shared_2_GUIDSame",
                "SensorType_Shared_1",
                "Platform_Shared_1",
                "Private",
                change_id,
            )
            sensor_shared_guid = sensor_shared.sensor_id

            # Create synonym on master for Sensor_Master_1
            self.master_store.add_to_synonyms(
                "Sensors", "Sensor_Master_1_Synonym", sensor_master_1.sensor_id, change_id
            )

        with self.slave_store.session_scope():
            change_id = self.slave_store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id

            self.slave_store.add_to_sensor_types("SensorType_Slave_1", change_id)
            self.slave_store.add_to_sensor_types("SensorType_Slave_2", change_id)
            self.slave_store.add_to_sensor_types("SensorType_Shared_1", change_id)
            st_shared = self.slave_store.add_to_sensor_types(
                "SensorType_Shared_2_GUIDSame", change_id
            )
            st_shared.sensor_type_id = st_shared_guid

            self.slave_store.add_to_platform_types("PlatformType_Slave_1", change_id)
            self.slave_store.add_to_platform_types("PlatformType_Shared_1", change_id)
            pt_shared = self.slave_store.add_to_platform_types(
                "PlatformType_Shared_2_GUIDSame", change_id
            )
            pt_shared.platform_type_id = pt_shared_guid

            nat_shared = self.slave_store.add_to_nationalities("UK", change_id)
            nat_shared.nationality_id = nat_shared_guid

            priv_shared = self.slave_store.add_to_privacies("Private", change_id)
            priv_shared.privacy_id = priv_shared_guid

            self.slave_store.session.add_all([st_shared, pt_shared, nat_shared, priv_shared])
            self.slave_store.session.commit()

            self.slave_store.add_to_platforms(
                "Platform_Slave_1", "UK", "PlatformType_Slave_1", "Private", change_id=change_id
            )
            self.slave_store.add_to_platforms(
                "Platform_Shared_1", "UK", "PlatformType_Shared_1", "Private", change_id=change_id
            )

            self.slave_store.add_to_sensors(
                "Sensor_Slave_1", "SensorType_Slave_1", "Platform_Slave_1", "Private", change_id
            )
            self.slave_store.add_to_sensors(
                "Sensor_Slave_2", "SensorType_Shared_1", "Platform_Slave_1", "Private", change_id
            )
            self.slave_store.add_to_sensors(
                "Sensor_Slave_3", "SensorType_Slave_2", "Platform_Shared_1", "Private", change_id
            )
            sensor_shared_1 = self.slave_store.add_to_sensors(
                "Sensor_Shared_1", "SensorType_Shared_1", "Platform_Shared_1", "Private", change_id
            )
            sensor_shared = self.slave_store.add_to_sensors(
                "Sensor_Shared_2_GUIDSame",
                "SensorType_Shared_1",
                "Platform_Shared_1",
                "Private",
                change_id,
            )
            sensor_shared.sensor_id = sensor_shared_guid

            self.slave_store.session.add(sensor_shared)
            self.slave_store.session.commit()

            self.slave_store.add_to_synonyms(
                "Sensors", "Sensor_Shared_1_Synonym", sensor_shared_1.sensor_id, change_id
            )

    def tearDown(self):
        if os.path.exists("master.sqlite"):
            os.remove("master.sqlite")

        if os.path.exists("slave.sqlite"):
            os.remove("slave.sqlite")

    def test_synonym_merge_metadata_table(self):
        merge_all_tables(self.master_store, self.slave_store)

        with self.master_store.session_scope():
            # Check the synonym entry from the slave is now in master
            slave_results = self.slave_store.session.query(
                self.slave_store.db_classes.Synonym
            ).all()

            master_results = (
                self.master_store.session.query(self.master_store.db_classes.Synonym)
                .filter(
                    self.master_store.db_classes.Synonym.synonym_id == slave_results[0].synonym_id
                )
                .all()
            )

            assert len(master_results) > 0

            # Check the synonym entry in master points to a SensorType in master
            synonym_results = self.master_store.session.query(
                self.master_store.db_classes.Synonym
            ).all()
            entities = [result.entity for result in synonym_results]
            assert len(synonym_results) > 0

            for entity in entities:
                sensor_results = (
                    self.master_store.session.query(self.master_store.db_classes.Sensor)
                    .filter(self.master_store.db_classes.Sensor.sensor_id == entity)
                    .all()
                )
                assert len(sensor_results) > 0


class TestMergeLogsAndChanges(unittest.TestCase):
    def setUp(self):
        self.master_store = DataStore("", "", "", 0, db_name="master.sqlite", db_type="sqlite")
        self.slave_store = DataStore("", "", "", 0, db_name="slave.sqlite", db_type="sqlite")

        self.master_store.initialise()
        self.slave_store.initialise()

        # Import two files into master
        processor = FileProcessor(archive=False)
        processor.load_importers_dynamically()
        processor.process(
            os.path.join(SAMPLE_DATA_PATH, "track_files", "gpx", "gpx_1_0.gpx"),
            self.master_store,
            False,
        )
        processor.process(
            os.path.join(SAMPLE_DATA_PATH, "track_files", "rep_data", "rep_test1.rep"),
            self.master_store,
            False,
        )

        # Import two files into slave
        processor = FileProcessor(archive=False)
        processor.load_importers_dynamically()
        processor.process(
            os.path.join(SAMPLE_DATA_PATH, "track_files", "gpx", "gpx_1_0.gpx"),
            self.slave_store,
            False,
        )
        processor.process(
            os.path.join(SAMPLE_DATA_PATH, "track_files", "rep_data", "uk_track.rep"),
            self.slave_store,
            False,
        )

    def tearDown(self):
        if os.path.exists("master.sqlite"):
            os.remove("master.sqlite")

        if os.path.exists("slave.sqlite"):
            os.remove("slave.sqlite")

    def test_merge_logs_and_changes(self):
        merge_all_tables(self.master_store, self.slave_store)

        with self.master_store.session_scope():
            with self.slave_store.session_scope():
                # Check there are only four entries in the Changes table (three from the merge, one extra for the
                # change created for the merging)
                results = self.master_store.session.query(self.master_store.db_classes.Change).all()

                assert len(results) == 4

                # Check that all entries in the master Log table match up with an entry in the table
                # referenced in the 'table' attribute of the Log entry
                results = self.master_store.session.query(self.master_store.db_classes.Log).all()

                for result in results:
                    class_name = table_name_to_class_name(result.table)

                    referenced_table = getattr(self.master_store.db_classes, class_name)
                    pri_key_field = get_primary_key_for_table(referenced_table)
                    referenced_table_pri_key = getattr(referenced_table, pri_key_field)
                    id_to_match = result.id
                    ref_table_results = (
                        self.master_store.session.query(referenced_table)
                        .filter(referenced_table_pri_key == id_to_match)
                        .all()
                    )

                    assert len(ref_table_results) == 1


class TestMergeUpdatePlatform(unittest.TestCase):
    def setUp(self):
        self.master_store = DataStore("", "", "", 0, db_name="master.sqlite", db_type="sqlite")
        self.slave_store = DataStore("", "", "", 0, db_name="slave.sqlite", db_type="sqlite")

        self.master_store.initialise()
        self.slave_store.initialise()

        with self.master_store.session_scope():
            change_id = self.master_store.add_to_changes(
                "TEST", datetime.utcnow(), "TEST"
            ).change_id

            self.master_store.add_to_platform_types("PlatformType_Master_1", change_id)
            self.master_store.add_to_platform_types("PlatformType_Shared_1", change_id)
            pt_shared = self.master_store.add_to_platform_types(
                "PlatformType_Shared_2_GUIDSame", change_id
            )
            pt_shared_guid = pt_shared.platform_type_id

            nat_shared = self.master_store.add_to_nationalities("UK", change_id)
            nat_shared_guid = nat_shared.nationality_id

            priv_shared = self.master_store.add_to_privacies("Private", change_id)
            priv_shared_guid = priv_shared.privacy_id

            self.master_store.session.add_all([pt_shared, nat_shared, priv_shared])
            self.master_store.session.commit()

            self.master_store.add_to_platforms(
                "Platform_Master_1", "UK", "PlatformType_Master_1", "Private", change_id=change_id
            )
            self.master_store.add_to_platforms(
                "Platform_Shared_1", "UK", "PlatformType_Shared_1", "Private", change_id=change_id
            )
            self.master_store.add_to_platforms(
                "Platform_Shared_2",
                "UK",
                "PlatformType_Shared_1",
                "Private",
                trigraph="PL1",
                change_id=change_id,
            )

        with self.slave_store.session_scope():
            change_id = self.slave_store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id

            self.slave_store.add_to_platform_types("PlatformType_Slave_1", change_id)
            self.slave_store.add_to_platform_types("PlatformType_Shared_1", change_id)
            pt_shared = self.slave_store.add_to_platform_types(
                "PlatformType_Shared_2_GUIDSame", change_id
            )
            pt_shared.platform_type_id = pt_shared_guid

            nat_shared = self.slave_store.add_to_nationalities("UK", change_id)
            nat_shared.nationality_id = nat_shared_guid

            priv_shared = self.slave_store.add_to_privacies("Private", change_id)
            priv_shared.privacy_id = priv_shared_guid

            self.slave_store.session.add_all([pt_shared, nat_shared, priv_shared])
            self.slave_store.session.commit()

            self.slave_store.add_to_platforms(
                "Platform_Slave_1", "UK", "PlatformType_Slave_1", "Private", change_id=change_id
            )
            self.slave_store.add_to_platforms(
                "Platform_Shared_1",
                "UK",
                "PlatformType_Shared_1",
                "Private",
                trigraph="PLT",
                change_id=change_id,
            )
            # This has the same details as the one in master, except a different trigraph. Should still match,
            # but the trigraph in master shouldn't be updated
            self.slave_store.add_to_platforms(
                "Platform_Shared_2",
                "UK",
                "PlatformType_Shared_1",
                "Private",
                trigraph="PL2",
                change_id=change_id,
            )

    def tearDown(self):
        if os.path.exists("master.sqlite"):
            os.remove("master.sqlite")

        if os.path.exists("slave.sqlite"):
            os.remove("slave.sqlite")

    def test_merge_update_platform(self):
        merge_all_tables(self.master_store, self.slave_store)

        # Check that the trigraph that was additional data for Platform_Shared_1 has copied across
        results = (
            self.master_store.session.query(self.master_store.db_classes.Platform)
            .filter(self.master_store.db_classes.Platform.name == "Platform_Shared_1")
            .all()
        )

        assert len(results) == 1
        assert results[0].trigraph == "PLT"

        # Check that only one platform called Platform_Shared_2 exists, and that the trigraph is still
        # what it was originally set to in master
        results = (
            self.master_store.session.query(self.master_store.db_classes.Platform)
            .filter(self.master_store.db_classes.Platform.name == "Platform_Shared_2")
            .all()
        )

        assert len(results) == 1

        assert results[0].trigraph == "PL1"
        master_guid = results[0].platform_id

        # Check that the GUIDs match between Platform_Shared_2 in slave and master
        results = (
            self.slave_store.session.query(self.slave_store.db_classes.Platform)
            .filter(self.slave_store.db_classes.Platform.name == "Platform_Shared_2")
            .all()
        )

        assert master_guid == results[0].platform_id

        # Check a new change was added
        results = (
            self.master_store.session.query(self.master_store.db_classes.Change)
            .filter(
                self.master_store.db_classes.Change.reason == "Merging from database slave.sqlite"
            )
            .all()
        )

        assert len(results) == 1

        # Check a log entry was added for updating the trigraph field
        results = (
            self.master_store.session.query(self.master_store.db_classes.Log)
            .filter(self.master_store.db_classes.Log.new_value == "PLT")
            .all()
        )

        assert len(results) == 1


class TestExportAlterAndMerge(unittest.TestCase):
    @patch("pepys_admin.snapshot_cli.input", return_value="slave_exported.sqlite")
    @patch("pepys_admin.snapshot_cli.iterfzf", return_value=["PRIVACY-1"])
    def setUp(self, patched_input, patched_iterfzf):
        if os.path.exists("master.sqlite"):
            os.remove("master.sqlite")

        if os.path.exists("slave_exported.sqlite"):
            os.remove("slave_exported.sqlite")

        # Create a master database
        self.master_store = DataStore("", "", "", 0, db_name="master.sqlite", db_type="sqlite")
        self.master_store.initialise()

        # Do some imports into master
        # We import these files: gpx_1_0.gpx, rep_test1.rep
        processor = FileProcessor(archive=False)
        processor.load_importers_dynamically()
        processor.process(
            os.path.join(SAMPLE_DATA_PATH, "track_files", "gpx", "gpx_1_0.gpx"),
            self.master_store,
            False,
        )
        processor.process(
            os.path.join(SAMPLE_DATA_PATH, "track_files", "rep_data", "rep_test1.rep"),
            self.master_store,
            False,
        )

        # Export master to slave_exported.sqlite
        self.shell = SnapshotShell(self.master_store)
        self.shell.do_export_reference_data_and_metadata()

        # Create a data_store pointing to the new slave database
        self.slave_store = DataStore(
            "", "", "", 0, db_name="slave_exported.sqlite", db_type="sqlite"
        )

        # Do some more imports into master
        # We import these files: gpx_1_0_MultipleTracks.gpx
        processor.process(
            os.path.join(SAMPLE_DATA_PATH, "track_files", "gpx", "gpx_1_0_MultipleTracks.gpx"),
            self.master_store,
            False,
        )

        # Do some imports into slave
        # We import these files: rep_test1.rep
        # (rep_test1.rep file is the same as was imported into master earlier - this won't be in this db already
        # as measurements are not exported)
        processor.process(
            os.path.join(SAMPLE_DATA_PATH, "track_files", "rep_data", "rep_test1.rep"),
            self.slave_store,
            False,
        )

        # Do some more imports into slave - now with a new default resolver, so we get different default values
        # We import these files:  uk_track.rep
        new_default_resolver = DefaultResolver()
        new_default_resolver.default_platform_name = "PLATFORM-1-SLAVE"
        new_default_resolver.default_trigraph = "PL1-SLAVE"
        new_default_resolver.default_quadgraph = "PLT1-SLAVE"
        new_default_resolver.default_identifier = "123-SLAVE"
        new_default_resolver.default_platform_type = "Warship-SLAVE"
        new_default_resolver.default_nationality = "UK-SLAVE"
        new_default_resolver.default_sensor_name = "SENSOR-1-SLAVE"
        new_default_resolver.default_sensor_type = "Position-SLAVE"
        new_default_resolver.default_privacy = "PRIVACY-1-SLAVE"
        new_default_resolver.default_datafile_name = "DATAFILE-1-SLAVE"
        new_default_resolver.default_datafile_type = "DATAFILE-TYPE-1-SLAVE"

        self.slave_store = DataStore(
            "",
            "",
            "",
            0,
            db_name="slave_exported.sqlite",
            db_type="sqlite",
            missing_data_resolver=new_default_resolver,
        )

        # processor.process(
        #     os.path.join(SAMPLE_DATA_PATH, "track_files", "rep_data", "uk_track.rep"),
        #     self.slave_store,
        #     False,
        # )

        # Do some manual creation of objects in master
        # Specifically:
        #  - a master-specific PlatformType, and a shared-by-name PlatformType
        #  - a master-specific Platform and a shared-by-name Platform
        #  - a master-specific Synonym and a shared-by-name Synonym

        # Do some manual creation of objects in slave
        # Specifically
        #  - a slave-specific PlatformType, and a shared-by-name PlatformType (from above)
        #  - a slave-specific Platform and a shared-by-name Platform (from above)
        #  - a slave-specific Synonym and a shared-by-name Synonym (from above)

    def tearDown(self):
        # if os.path.exists("master.sqlite"):
        #     os.remove("master.sqlite")

        # if os.path.exists("slave.sqlite"):
        #     os.remove("slave.sqlite")
        pass

    def test_export_alter_merge(self):
        pass
