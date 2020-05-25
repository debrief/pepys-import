import os
import unittest
from datetime import datetime

from pepys_admin.merge import (
    merge_all_metadata_tables,
    merge_all_reference_tables,
    merge_reference_table,
)
from pepys_admin.utils import check_sqlalchemy_results_are_equal
from pepys_import.core.store.data_store import DataStore


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
            self.slave_store.add_to_sensor_types("ST_Shared_1", change_id)
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
        merge_reference_table("SensorType", self.master_store, self.slave_store)

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
            self.master_store.add_to_platform_types("PT_Master_1", change_id)
            self.master_store.add_to_platform_types("PT_Master_2", change_id)
            self.master_store.add_to_platform_types("PT_Shared_1", change_id)
            st_obj = self.master_store.add_to_platform_types("PT_Shared_2GUIDMatch", change_id)
            st_obj_guid = st_obj.platform_type_id

        with self.slave_store.session_scope():
            change_id = self.slave_store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id
            self.slave_store.add_to_platform_types("PT_Slave_1", change_id)
            self.slave_store.add_to_platform_types("PT_Slave_2", change_id)
            self.slave_store.add_to_platform_types("PT_Shared_1", change_id)
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
        merge_reference_table("PlatformType", self.master_store, self.slave_store)

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
        # os.remove("master.db")
        # os.remove("slave.db")
        pass

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
        """Creates the master and slave databases and contents required for the test.

        At the end of this set up we will have We have two unique PlatformTypes on master, two unique
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
        # os.remove("master.db")
        # os.remove("slave.db")
        pass

    def test_sensor_platform_merge(self):
        # Must merge reference tables first, so we can ensure foreign key integrity
        merge_all_reference_tables(self.master_store, self.slave_store)

        # Do the actual merge of the metadata tables
        merge_all_metadata_tables(self.master_store, self.slave_store)

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
