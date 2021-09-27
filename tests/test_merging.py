import os
import shutil
import unittest
from contextlib import redirect_stdout
from datetime import datetime
from getpass import getuser
from io import StringIO
from unittest.mock import patch

import pytest
from geoalchemy2.shape import to_shape
from testing.postgresql import Postgresql

from pepys_admin.merge import MergeDatabases
from pepys_admin.snapshot_cli import SnapshotShell
from pepys_admin.utils import check_sqlalchemy_results_are_equal, sqlalchemy_obj_to_dict
from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor
from pepys_import.resolvers.default_resolver import DefaultResolver
from pepys_import.utils.sqlalchemy_utils import get_primary_key_for_table
from pepys_import.utils.table_name_utils import table_name_to_class_name

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
            self.slave_store.add_to_privacies("Private", level=0, change_id=change_id)
            platform = self.slave_store.add_to_platforms(
                "Platform1", "123", "UK", "PlatformType1", "Private", change_id=change_id
            )
            self.slave_store.add_to_sensors(
                name="Sensor1",
                sensor_type="ST_Shared_1",
                host_id=platform.platform_id,
                host_name=None,
                host_identifier=None,
                host_nationality=None,
                privacy="Private",
                change_id=change_id,
            )

        self.merge_class = MergeDatabases(self.master_store, self.slave_store)

    def tearDown(self):
        if os.path.exists("master.sqlite"):
            os.remove("master.sqlite")

        if os.path.exists("slave.sqlite"):
            os.remove("slave.sqlite")

    def test_sensor_type_merge(self):
        # Do the merge
        id_results = self.merge_class.merge_reference_table(
            "SensorType",
        )

        master_table = self.master_store.db_classes.SensorType
        slave_table = self.slave_store.db_classes.SensorType

        with self.master_store.session_scope():
            with self.slave_store.session_scope():
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

                added_ids = [d["id"] for d in id_results["added"]]

                assert slave_results[0].sensor_type_id in added_ids
                assert slave_results[1].sensor_type_id in added_ids

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

                assert id_results["already_there"][0]["id"] == slave_results[0].sensor_type_id

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

                assert id_results["modified"][0]["from"] == self.slave_shared_id
                assert id_results["modified"][0]["to"] == new_guid

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
            self.slave_store.add_to_privacies("Private", level=0, change_id=change_id)
            self.slave_store.add_to_platforms(
                "Platform1", "123", "UK", "PT_Shared_1", "Private", change_id=change_id
            )

        self.merge_class = MergeDatabases(self.master_store, self.slave_store)

    def tearDown(self):
        if os.path.exists("master.sqlite"):
            os.remove("master.sqlite")

        if os.path.exists("slave.sqlite"):
            os.remove("slave.sqlite")

    def test_platform_type_merge(self):
        # Do the merge
        id_results = self.merge_class.merge_reference_table(
            "PlatformType",
        )

        master_table = self.master_store.db_classes.PlatformType
        slave_table = self.slave_store.db_classes.PlatformType

        with self.master_store.session_scope():
            with self.slave_store.session_scope():
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

                added_ids = [d["id"] for d in id_results["added"]]
                assert slave_results[0].platform_type_id in added_ids
                assert slave_results[1].platform_type_id in added_ids

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

                assert id_results["already_there"][0]["id"] == slave_results[0].platform_type_id

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

                assert id_results["modified"][0]["from"] == self.slave_shared_id
                assert id_results["modified"][0]["to"] == new_guid

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
            self.slave_store.add_to_privacies("Private", level=0, change_id=change_id)
            self.slave_store.add_to_platform_types("PlatformType1", change_id)
            self.slave_store.add_to_platforms(
                "Platform1", "123", "Nat_Shared_1", "PlatformType1", "Private", change_id=change_id
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

        self.merge_class = MergeDatabases(self.master_store, self.slave_store)

    def tearDown(self):
        if os.path.exists("master.sqlite"):
            os.remove("master.sqlite")

        if os.path.exists("slave.sqlite"):
            os.remove("slave.sqlite")

    def test_merge_all_reference_tables(self):
        self.merge_class.merge_all_reference_tables()

        with self.master_store.session_scope():
            with self.slave_store.session_scope():
                # Check there are the right number of rows for each table

                results = self.master_store.session.query(
                    self.master_store.db_classes.Nationality
                ).all()
                assert len(results) == 6

                results = self.master_store.session.query(
                    self.master_store.db_classes.CommentType
                ).all()
                assert len(results) == 6

                results = self.master_store.session.query(
                    self.master_store.db_classes.GeometryType
                ).all()
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

            priv_shared = self.master_store.add_to_privacies(
                "Private", level=0, change_id=change_id
            )
            priv_shared_guid = priv_shared.privacy_id

            self.master_store.session.add_all([st_shared, pt_shared, nat_shared, priv_shared])
            self.master_store.session.commit()

            plat_master_1 = self.master_store.add_to_platforms(
                "Platform_Master_1",
                "123",
                "UK",
                "PlatformType_Master_1",
                "Private",
                change_id=change_id,
            )
            plat_shared_1 = self.master_store.add_to_platforms(
                "Platform_Shared_1",
                "234",
                "UK",
                "PlatformType_Shared_1",
                "Private",
                change_id=change_id,
            )

            self.master_store.add_to_sensors(
                name="Sensor_Master_1",
                sensor_type="SensorType_Master_1",
                host_id=plat_master_1.platform_id,
                host_name=None,
                host_identifier=None,
                host_nationality=None,
                privacy="Private",
                change_id=change_id,
            )
            self.master_store.add_to_sensors(
                name="Sensor_Master_2",
                sensor_type="SensorType_Shared_1",
                host_id=plat_master_1.platform_id,
                host_name=None,
                host_identifier=None,
                host_nationality=None,
                privacy="Private",
                change_id=change_id,
            )
            self.master_store.add_to_sensors(
                name="Sensor_Master_3",
                sensor_type="SensorType_Master_2",
                host_id=plat_shared_1.platform_id,
                host_name=None,
                host_identifier=None,
                host_nationality=None,
                privacy="Private",
                change_id=change_id,
            )
            self.master_store.add_to_sensors(
                name="Sensor_Shared_1",
                sensor_type="SensorType_Shared_1",
                host_id=plat_shared_1.platform_id,
                host_name=None,
                host_identifier=None,
                host_nationality=None,
                privacy="Private",
                change_id=change_id,
            )
            sensor_shared = self.master_store.add_to_sensors(
                name="Sensor_Shared_2_GUIDSame",
                sensor_type="SensorType_Shared_1",
                host_id=plat_shared_1.platform_id,
                host_name=None,
                host_identifier=None,
                host_nationality=None,
                privacy="Private",
                change_id=change_id,
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

            priv_shared = self.slave_store.add_to_privacies("Private", level=0, change_id=change_id)
            priv_shared.privacy_id = priv_shared_guid

            self.slave_store.session.add_all([st_shared, pt_shared, nat_shared, priv_shared])
            self.slave_store.session.commit()

            plat_slave_1 = self.slave_store.add_to_platforms(
                "Platform_Slave_1",
                "123",
                "UK",
                "PlatformType_Slave_1",
                "Private",
                change_id=change_id,
            )
            plat_shared_1 = self.slave_store.add_to_platforms(
                "Platform_Shared_1",
                "234",
                "UK",
                "PlatformType_Shared_1",
                "Private",
                change_id=change_id,
            )

            self.slave_store.add_to_sensors(
                name="Sensor_Slave_1",
                sensor_type="SensorType_Slave_1",
                host_id=plat_slave_1.platform_id,
                host_name=None,
                host_identifier=None,
                host_nationality=None,
                privacy="Private",
                change_id=change_id,
            )
            self.slave_store.add_to_sensors(
                name="Sensor_Slave_2",
                sensor_type="SensorType_Shared_1",
                host_id=plat_slave_1.platform_id,
                host_name=None,
                host_identifier=None,
                host_nationality=None,
                privacy="Private",
                change_id=change_id,
            )
            self.slave_store.add_to_sensors(
                name="Sensor_Slave_3",
                sensor_type="SensorType_Slave_2",
                host_id=plat_shared_1.platform_id,
                host_name=None,
                host_identifier=None,
                host_nationality=None,
                privacy="Private",
                change_id=change_id,
            )
            self.slave_store.add_to_sensors(
                name="Sensor_Shared_1",
                sensor_type="SensorType_Shared_1",
                host_id=plat_shared_1.platform_id,
                host_name=None,
                host_identifier=None,
                host_nationality=None,
                privacy="Private",
                change_id=change_id,
            )
            sensor_shared = self.slave_store.add_to_sensors(
                name="Sensor_Shared_2_GUIDSame",
                sensor_type="SensorType_Shared_1",
                host_id=plat_shared_1.platform_id,
                host_name=None,
                host_identifier=None,
                host_nationality=None,
                privacy="Private",
                change_id=change_id,
            )
            sensor_shared.sensor_id = sensor_shared_guid

            self.slave_store.session.add(sensor_shared)
            self.slave_store.session.commit()

        self.merge_class = MergeDatabases(self.master_store, self.slave_store)

    def tearDown(self):
        if os.path.exists("master.sqlite"):
            os.remove("master.sqlite")

        if os.path.exists("slave.sqlite"):
            os.remove("slave.sqlite")

    def test_sensor_platform_merge(self):
        with self.master_store.session_scope():
            self.master_store.add_to_changes(
                user=getuser(),
                modified=datetime.utcnow(),
                reason=f"Merging from database {self.slave_store.db_name}",
            ).change_id

        # Must merge reference tables first, so we can ensure foreign key integrity
        self.merge_class.merge_all_reference_tables()

        # Do the actual merge of the metadata tables
        self.merge_class.merge_all_metadata_tables()

        with self.master_store.session_scope():
            with self.slave_store.session_scope():
                # Check there are the right number of entries in each table
                results = self.master_store.session.query(
                    self.master_store.db_classes.SensorType
                ).all()
                assert len(results) == 6

                results = self.master_store.session.query(
                    self.master_store.db_classes.PlatformType
                ).all()
                assert len(results) == 4

                results = self.master_store.session.query(
                    self.master_store.db_classes.Nationality
                ).all()
                assert len(results) == 1

                results = self.master_store.session.query(
                    self.master_store.db_classes.Privacy
                ).all()
                assert len(results) == 1

                results = self.master_store.session.query(
                    self.master_store.db_classes.Platform
                ).all()
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
                assert (
                    master_sensor_results[0].sensor_type_id == master_st_results[0].sensor_type_id
                )
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

            self.master_store.add_to_privacies("Private", level=0, change_id=change_id)
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

            self.slave_store.add_to_privacies("Private", level=0, change_id=change_id)
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

        self.merge_class = MergeDatabases(self.master_store, self.slave_store)

    def tearDown(self):
        if os.path.exists("master.sqlite"):
            os.remove("master.sqlite")

        if os.path.exists("slave.sqlite"):
            os.remove("slave.sqlite")

    def test_merge_data_files(self):
        with self.master_store.session_scope():
            self.master_store.add_to_changes(
                user=getuser(),
                modified=datetime.utcnow(),
                reason=f"Merging from database {self.slave_store.db_name}",
            ).change_id

        self.merge_class.merge_all_reference_tables()

        id_results = self.merge_class.merge_metadata_table("Datafile")

        with self.master_store.session_scope():
            with self.slave_store.session_scope():
                # Check there are the right number of entries in the master database
                results = self.master_store.session.query(
                    self.master_store.db_classes.Datafile
                ).all()
                assert len(results) == 6

                # Check there are the right number of IDs in each section of the ID results
                assert len(id_results["already_there"]) == 1
                assert len(id_results["added"]) == 2
                assert len(id_results["modified"]) == 1

                # Check we have an entry called Slave_DF_1 in master now
                results = (
                    self.master_store.session.query(self.master_store.db_classes.Datafile)
                    .filter(self.master_store.db_classes.Datafile.reference == "Slave_DF_1")
                    .all()
                )

                assert len(results) == 1
                ids_added = [d["id"] for d in id_results["added"]]
                assert results[0].datafile_id in ids_added

                # Check that we mark the Shared_DF_2_GUIDSame entry as already there
                results = (
                    self.master_store.session.query(self.master_store.db_classes.Datafile)
                    .filter(
                        self.master_store.db_classes.Datafile.reference == "Shared_DF_2_GUIDSame"
                    )
                    .all()
                )

                assert len(results) == 1
                ids_already_there = [d["id"] for d in id_results["already_there"]]
                assert results[0].datafile_id in ids_already_there

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

                assert id_results["modified"][0]["from"] == self.shared_guid
                assert id_results["modified"][0]["to"] == master_results[0].datafile_id


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

        self.merge_class = MergeDatabases(self.master_store, self.slave_store)

    def tearDown(self):
        if os.path.exists("master.sqlite"):
            os.remove("master.sqlite")

        if os.path.exists("slave.sqlite"):
            os.remove("slave.sqlite")

    def test_merge_state_from_import(self):
        self.merge_class.merge_all_tables()

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
                database="test",
                host="localhost",
                user="postgres",
                password="postgres",
                port=55527,
            )
        except RuntimeError:
            raise Exception("Testing Postgres server could not be started/accessed")

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
                .order_by(self.master_store.db_classes.State.time)
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

        self.merge_class = MergeDatabases(self.master_store, self.slave_store)

    def tearDown(self):
        try:
            self.postgres.stop()
        except AttributeError:
            return

        if os.path.exists("slave.sqlite"):
            os.remove("slave.sqlite")

    def test_merge_state_from_import(self):
        self.merge_class.merge_all_tables()

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
                    .order_by(self.master_store.db_classes.State.time)
                    .all()
                )
                slave_results = (
                    self.slave_store.session.query(self.slave_store.db_classes.State)
                    .filter(self.slave_store.db_classes.State.source_reference == "uk_track.rep")
                    .order_by(self.slave_store.db_classes.State.time)
                    .all()
                )

                assert check_sqlalchemy_results_are_equal(master_results, slave_results)

                # Check that the gpx_1_0.gpx entries haven't been duplicated

                # Specifically, check the original in master hasn't been touched
                results = (
                    self.master_store.session.query(self.master_store.db_classes.State)
                    .filter(self.master_store.db_classes.State.source_reference == "gpx_1_0.gpx")
                    .order_by(self.master_store.db_classes.State.time)
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
                    .order_by(self.slave_store.db_classes.State.time)
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


class TestMergeStateFromImport_Idempotent_SameFile(unittest.TestCase):
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

        self.merge_class = MergeDatabases(self.master_store, self.slave_store)

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
        self.merge_class.merge_all_tables()

        self.do_checks()

        # Run again and check all the tests still pass
        self.merge_class.merge_all_tables()

        self.do_checks()


class TestMergeStateFromImport_Idempotent_DifferentFile(unittest.TestCase):
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

        self.merge_class = MergeDatabases(self.master_store, self.slave_store)

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
        self.merge_class.merge_all_tables()

        self.do_checks()

        # Run again merging from the original sqlite file
        # that hasn't been altered by the merge process
        DataStore("", "", "", 0, db_name="slave_orig.sqlite", db_type="sqlite")
        self.merge_class.merge_all_tables()

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
            self.slave_store.add_to_privacies("Private", level=0, change_id=change_id)
            plat1 = self.slave_store.add_to_platforms(
                "Platform1", "123", "UK", "PlatformType1", "Private", change_id=change_id
            )
            self.slave_store.add_to_sensors(
                name="Sensor1",
                sensor_type="ST_Shared_1",
                host_id=plat1.platform_id,
                host_name=None,
                host_nationality=None,
                host_identifier=None,
                privacy="Private",
                change_id=change_id,
            )

            self.slave_store.add_to_synonyms(
                "SensorTypes", "ST_Shared_1_Synonym", slave_shared_obj.sensor_type_id, change_id
            )

        self.merge_class = MergeDatabases(self.master_store, self.slave_store)

    def tearDown(self):
        if os.path.exists("master.sqlite"):
            os.remove("master.sqlite")

        if os.path.exists("slave.sqlite"):
            os.remove("slave.sqlite")

    def test_synonym_merge_reference_table(self):
        with self.master_store.session_scope():
            self.master_store.add_to_changes(
                user=getuser(),
                modified=datetime.utcnow(),
                reason=f"Merging from database {self.slave_store.db_name}",
            ).change_id

        # Do the merge
        self.merge_class.merge_all_reference_tables()
        self.merge_class.merge_metadata_table("Synonym")

        with self.master_store.session_scope():
            with self.slave_store.session_scope():
                # Check the synonym entry from the slave is now in master
                slave_results = self.slave_store.session.query(
                    self.slave_store.db_classes.Synonym
                ).all()
                master_results = self.master_store.session.query(
                    self.master_store.db_classes.Synonym
                ).all()

                assert check_sqlalchemy_results_are_equal(master_results, slave_results)

                # Check the synonym entry in master points to a SensorType in master
                results = self.master_store.session.query(
                    self.master_store.db_classes.Synonym
                ).all()

                assert len(results) > 0

                results = (
                    self.master_store.session.query(self.master_store.db_classes.SensorType)
                    .filter(
                        self.master_store.db_classes.SensorType.sensor_type_id == results[0].entity
                    )
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

            self.master_store.add_to_platform_types("PlatformType_Master_1", change_id)
            self.master_store.add_to_platform_types("PlatformType_Shared_1", change_id)
            pt_shared = self.master_store.add_to_platform_types(
                "PlatformType_Shared_2_GUIDSame", change_id
            )
            pt_shared_guid = pt_shared.platform_type_id

            nat_shared = self.master_store.add_to_nationalities("UK", change_id)
            nat_shared_guid = nat_shared.nationality_id

            priv_shared = self.master_store.add_to_privacies(
                "Private", level=0, change_id=change_id
            )
            priv_shared_guid = priv_shared.privacy_id

            self.master_store.session.add_all([pt_shared, nat_shared, priv_shared])
            self.master_store.session.commit()

            plat_master_1 = self.master_store.add_to_platforms(
                "Platform_Master_1",
                "123",
                "UK",
                "PlatformType_Master_1",
                "Private",
                change_id=change_id,
            )
            self.master_store.add_to_platforms(
                "Platform_Master_2",
                "234",
                "UK",
                "PlatformType_Master_1",
                "Private",
                change_id=change_id,
            )
            self.master_store.add_to_platforms(
                "Platform_Master_3",
                "345",
                "UK",
                "PlatformType_Master_1",
                "Private",
                change_id=change_id,
            )
            self.master_store.add_to_platforms(
                "Platform_Shared_1",
                "456",
                "UK",
                "PlatformType_Shared_1",
                "Private",
                change_id=change_id,
            )

            platform_shared = self.master_store.add_to_platforms(
                "Platform_Shared_2_GUIDSame",
                "567",
                "UK",
                "PlatformType_Shared_1",
                "Private",
                change_id=change_id,
            )
            platform_shared_guid = platform_shared.platform_id
            self.master_store.session.add(platform_shared)
            self.master_store.session.flush()

            # Create synonym on master for Sensor_Master_1
            self.master_store.add_to_synonyms(
                "Platforms", "Platform_Master_1_Synonym", plat_master_1.platform_id, change_id
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

            priv_shared = self.slave_store.add_to_privacies("Private", level=0, change_id=change_id)
            priv_shared.privacy_id = priv_shared_guid

            self.slave_store.session.add_all([pt_shared, nat_shared, priv_shared])
            self.slave_store.session.commit()

            self.slave_store.add_to_platforms(
                "Platform_Slave_1",
                "123",
                "UK",
                "PlatformType_Slave_1",
                "Private",
                change_id=change_id,
            )
            self.slave_store.add_to_platforms(
                "Platform_Slave_2",
                "234",
                "UK",
                "PlatformType_Slave_1",
                "Private",
                change_id=change_id,
            )
            self.slave_store.add_to_platforms(
                "Platform_Slave_3",
                "345",
                "UK",
                "PlatformType_Slave_1",
                "Private",
                change_id=change_id,
            )
            platform_shared_1 = self.slave_store.add_to_platforms(
                "Platform_Shared_1",
                "456",
                "UK",
                "PlatformType_Shared_1",
                "Private",
                change_id=change_id,
            )

            platform_shared_slave = self.slave_store.add_to_platforms(
                "Platform_Shared_2_GUIDSame",
                "567",
                "UK",
                "PlatformType_Shared_1",
                "Private",
                change_id=change_id,
            )
            platform_shared_slave.platform_id = platform_shared_guid

            self.slave_store.session.add(platform_shared_slave)
            self.slave_store.session.commit()

            self.slave_store.add_to_synonyms(
                "Platforms", "Platform_Shared1_Synonym", platform_shared_1.platform_id, change_id
            )

        self.merge_class = MergeDatabases(self.master_store, self.slave_store)

    def tearDown(self):
        if os.path.exists("master.sqlite"):
            os.remove("master.sqlite")

        if os.path.exists("slave.sqlite"):
            os.remove("slave.sqlite")

    def test_synonym_merge_metadata_table(self):
        self.merge_class.merge_all_tables()

        with self.master_store.session_scope():
            with self.slave_store.session_scope():
                # Check the synonym entry from the slave is now in master
                slave_results = self.slave_store.session.query(
                    self.slave_store.db_classes.Synonym
                ).all()

                master_results = (
                    self.master_store.session.query(self.master_store.db_classes.Synonym)
                    .filter(
                        self.master_store.db_classes.Synonym.synonym_id
                        == slave_results[0].synonym_id
                    )
                    .all()
                )

                assert len(master_results) > 0

                # Check the synonym entry in master points to a Platform in master
                synonym_results = self.master_store.session.query(
                    self.master_store.db_classes.Synonym
                ).all()
                entities = [result.entity for result in synonym_results]
                assert len(synonym_results) > 0

                for entity in entities:
                    sensor_results = (
                        self.master_store.session.query(self.master_store.db_classes.Platform)
                        .filter(self.master_store.db_classes.Platform.platform_id == entity)
                        .all()
                    )
                    assert len(sensor_results) > 0


class TestMergeLogsAndChanges(unittest.TestCase):
    def setUp(self):
        if os.path.exists("master.sqlite"):
            os.remove("master.sqlite")

        if os.path.exists("slave.sqlite"):
            os.remove("slave.sqlite")

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

        self.merge_class = MergeDatabases(self.master_store, self.slave_store)

    def tearDown(self):
        if os.path.exists("master.sqlite"):
            os.remove("master.sqlite")

        if os.path.exists("slave.sqlite"):
            os.remove("slave.sqlite")

    def test_merge_logs_and_changes(self):
        self.merge_class.merge_all_tables()

        with self.master_store.session_scope():
            with self.slave_store.session_scope():
                # Check there are five entries in the Changes table.
                # This is one from each of the imports (including the slave import - as objects from that import were merged,
                # so it's import to know where they came from for auditing), plus one for the merge itself
                results = self.master_store.session.query(self.master_store.db_classes.Change).all()

                assert len(results) == 5

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


class TestMergeUpdatePlatformPrivacy(unittest.TestCase):
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

            priv_shared = self.master_store.add_to_privacies(
                "Private", level=0, change_id=change_id
            )
            priv_shared_guid = priv_shared.privacy_id

            self.master_store.session.add_all([pt_shared, nat_shared, priv_shared])
            self.master_store.session.commit()

            self.master_store.add_to_platforms(
                "Platform_Master_1",
                "123",
                "UK",
                "PlatformType_Master_1",
                "Private",
                change_id=change_id,
            )
            self.master_store.add_to_platforms(
                "Platform_Shared_1",
                "234",
                "UK",
                "PlatformType_Shared_1",
                "Private",
                trigraph=None,
                change_id=change_id,
            )
            self.master_store.add_to_platforms(
                "Platform_Shared_2",
                "345",
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

            priv_shared = self.slave_store.add_to_privacies("Private", level=0, change_id=change_id)
            priv_shared.privacy_id = priv_shared_guid
            self.slave_store.add_to_privacies("Very Private", level=20, change_id=change_id)

            self.slave_store.session.add_all([pt_shared, nat_shared, priv_shared])
            self.slave_store.session.commit()

            self.slave_store.add_to_platforms(
                "Platform_Slave_1",
                "123",
                "UK",
                "PlatformType_Slave_1",
                "Private",
                change_id=change_id,
            )
            self.slave_store.add_to_platforms(
                "Platform_Shared_1",
                "234",
                "UK",
                "PlatformType_Shared_1",
                "Very Private",
                trigraph="PLT",
                change_id=change_id,
            )
            # This has the same details as the one in master, except a different trigraph. Should still match,
            # but the trigraph in master shouldn't be updated
            self.slave_store.add_to_platforms(
                "Platform_Shared_2",
                "345",
                "UK",
                "PlatformType_Shared_1",
                "Private",
                trigraph="PL2",
                change_id=change_id,
            )

        self.merge_class = MergeDatabases(self.master_store, self.slave_store)

    def tearDown(self):
        if os.path.exists("master.sqlite"):
            os.remove("master.sqlite")

        if os.path.exists("slave.sqlite"):
            os.remove("slave.sqlite")

    def test_merge_update_platform(self):
        self.merge_class.merge_all_tables()

        with self.master_store.session_scope():
            with self.slave_store.session_scope():
                # Check that the trigraph that was additional data for Platform_Shared_1 has copied across
                results = (
                    self.master_store.session.query(self.master_store.db_classes.Platform)
                    .filter(self.master_store.db_classes.Platform.name == "Platform_Shared_1")
                    .all()
                )

                assert len(results) == 1
                assert results[0].trigraph == "PLT"

                # Check that the Privacy for Platform_Shared_1 is now Very Private with level=20
                assert results[0].privacy.name == "Very Private"
                assert results[0].privacy.level == 20

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
                        self.master_store.db_classes.Change.reason
                        == "Merging from database slave.sqlite"
                    )
                    .all()
                )

                assert len(results) == 1

                # Check a log entry was added for updating the trigraph field
                results = (
                    self.master_store.session.query(self.master_store.db_classes.Log)
                    .filter(self.master_store.db_classes.Log.field == "trigraph")
                    .all()
                )

                assert len(results) == 1


class TestExportAlterAndMerge(unittest.TestCase):
    @patch("pepys_admin.snapshot_cli.ptk_prompt", return_value="slave_exported.sqlite")
    @patch("pepys_admin.snapshot_cli.iterfzf", return_value=["Public"])
    def setUp(self, patched_input, patched_iterfzf):
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
        new_default_resolver.default_trigraph = "SL1"
        new_default_resolver.default_quadgraph = "SLT1"
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

        processor.process(
            os.path.join(SAMPLE_DATA_PATH, "track_files", "rep_data", "uk_track.rep"),
            self.slave_store,
            False,
        )

        # Do some manual creation of objects in master
        # Specifically:
        #  - a master-specific PlatformType, and a shared-by-name PlatformType
        #  - a master-specific Platform and a shared-by-name Platform
        #  - a master-specific and shared-by-name Synonym

        # Create a change ID first
        with self.master_store.session_scope():
            change_id = self.master_store.add_to_changes(
                "TEST", datetime.utcnow(), "TEST"
            ).change_id
            self.master_store.add_to_platform_types("Master_PT_1", change_id=change_id)
            self.master_store.add_to_platform_types("Shared_PT_1", change_id=change_id)

            m_plat_1 = self.master_store.add_to_platforms(
                "Master_Platform_1", "123", "UK", "Warship", "Public", change_id=change_id
            )
            shared_plat_1 = self.master_store.add_to_platforms(
                "Shared_Platform_1", "234", "UK", "Warship", "Public", change_id=change_id
            )

            self.master_store.add_to_synonyms(
                "Platforms", "Master_Platform_1_Synonym", m_plat_1.platform_id, change_id=change_id
            )
            self.master_store.add_to_synonyms(
                "Platforms",
                "Shared_Platform_1_Synonym",
                shared_plat_1.platform_id,
                change_id=change_id,
            )

        # Do some manual creation of objects in slave
        # Specifically
        #  - a slave-specific PlatformType, and a shared-by-name PlatformType (from above)
        #  - a slave-specific Platform and a shared-by-name Platform (from above)
        #  - a slave-specific Synonym and a shared-by-name Synonym (from above)

        # Create a change ID first
        with self.slave_store.session_scope():
            change_id = self.slave_store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id

            self.slave_store.add_to_platform_types("Slave_PT_1", change_id=change_id)
            self.slave_store.add_to_platform_types("Shared_PT_1", change_id=change_id)

            s_plat_1 = self.slave_store.add_to_platforms(
                "Slave_Platform_1", "123", "UK", "Warship", "Public", change_id=change_id
            )
            shared_plat_1 = self.slave_store.add_to_platforms(
                "Shared_Platform_1",
                "234",
                "UK",
                "Warship",
                "Public",
                trigraph="P12",
                change_id=change_id,
            )

            self.slave_store.add_to_synonyms(
                "Platforms", "Slave_Platform_1_Synonym", s_plat_1.platform_id, change_id=change_id
            )
            self.slave_store.add_to_synonyms(
                "Platforms",
                "Shared_Platform_1_Synonym",
                shared_plat_1.platform_id,
                change_id=change_id,
            )

    def tearDown(self):
        if os.path.exists("master.sqlite"):
            os.remove("master.sqlite")

        if os.path.exists("slave_exported.sqlite"):
            os.remove("slave_exported.sqlite")

    def test_export_alter_merge(self):
        self.master_store = None
        self.slave_store = None

        self.slave_store = DataStore(
            "", "", "", 0, db_name="slave_exported.sqlite", db_type="sqlite"
        )

        self.master_store = DataStore("", "", "", 0, db_name="master.sqlite", db_type="sqlite")

        self.merge_class = MergeDatabases(self.master_store, self.slave_store)

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            # Do the merge
            self.merge_class.merge_all_tables()
        output = temp_output.getvalue()

        print(output)

        # Check statistics
        assert "| Nationality        |                 1 |       1 |          0 |" in output
        assert "| PlatformType       |                 1 |       2 |          0 |" in output
        assert "| Datafiles          |                 0 |       1 |          0 |" in output
        assert "| Platform           |                 4 |       2 |          1 |" in output
        assert "| Sensor             |                 5 |       1 |          0 |" in output
        assert "| State       |     402 |" in output
        assert "| Contact     |       0 |" in output

        # Check entries added list
        assert "  - uk_track.rep" in output
        assert "  - UK-SLAVE" in output
        assert "  - SPLENDID" in output
        assert "  - Warship-SLAVE" in output
        assert "  - PRIVACY-1-SLAVE" in output
        assert "  - Slave_Platform_1_Synonym" in output

        with self.master_store.session_scope():
            with self.slave_store.session_scope():
                # Check we have four datafiles in master
                datafiles = self.master_store.session.query(
                    self.master_store.db_classes.Datafile
                ).all()

                assert len(datafiles) == 4

                # Check one of these datafiles is called uk_track.rep
                references = [d.reference for d in datafiles]

                assert "uk_track.rep" in references

                # Check we have 425 rows in States
                states_count = self.master_store.session.query(
                    self.master_store.db_classes.State
                ).count()

                assert states_count == 425

                # Check we have objects with the slave's new default resolver values

                # Platform
                platform_results = (
                    self.master_store.session.query(self.master_store.db_classes.Platform)
                    .filter(self.master_store.db_classes.Platform.identifier == "123-SLAVE")
                    .all()
                )

                assert len(platform_results) == 1

                # Privacy
                privacy_results = (
                    self.master_store.session.query(self.master_store.db_classes.Privacy)
                    .filter(self.master_store.db_classes.Privacy.name == "PRIVACY-1-SLAVE")
                    .all()
                )

                assert len(privacy_results) == 1

                # Check we have merged PlatformTypes correctly
                pt_results = self.master_store.session.query(
                    self.master_store.db_classes.PlatformType
                ).all()

                pt_names = [pt.name for pt in pt_results]

                assert len(pt_names) == 5

                assert "Master_PT_1" in pt_names
                assert "Shared_PT_1" in pt_names
                assert "Slave_PT_1" in pt_names

                # Check we have merged Platforms correctly
                platform_results = self.master_store.session.query(
                    self.master_store.db_classes.Platform
                ).all()

                platform_names = [p.name for p in platform_results]

                assert len(platform_names) == 9

                assert "Master_Platform_1" in platform_names
                assert "Slave_Platform_1" in platform_names
                assert "Shared_Platform_1" in platform_names

                # Check we have merged Synonyms properly
                synonym_results = self.master_store.session.query(
                    self.master_store.db_classes.Synonym
                ).all()

                assert len(synonym_results) == 3

                # All Synonyms should link to an entry in the Platforms table
                for synonym_result in synonym_results:
                    platforms = (
                        self.master_store.session.query(self.master_store.db_classes.Platform)
                        .filter(
                            self.master_store.db_classes.Platform.platform_id
                            == synonym_result.entity
                        )
                        .all()
                    )

                    assert len(platforms) == 1


@pytest.mark.postgres
class TestExportAlterAndMerge_Postgres(unittest.TestCase):
    @patch("pepys_admin.snapshot_cli.ptk_prompt", return_value="slave_exported.sqlite")
    @patch("pepys_admin.snapshot_cli.iterfzf", return_value=["Public"])
    def setUp(self, patched_input, patched_iterfzf):
        self.postgres = None

        try:
            self.postgres = Postgresql(
                database="test",
                host="localhost",
                user="postgres",
                password="postgres",
                port=55527,
            )
        except RuntimeError:
            raise Exception("Testing Postgres server could not be started/accessed")

        self.master_store = DataStore(
            db_name="test",
            db_host="localhost",
            db_username="postgres",
            db_password="postgres",
            db_port=55527,
            db_type="postgres",
        )

        # Init master store
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
        new_default_resolver.default_trigraph = "SL1"
        new_default_resolver.default_quadgraph = "SLT1"
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

        processor.process(
            os.path.join(SAMPLE_DATA_PATH, "track_files", "rep_data", "uk_track.rep"),
            self.slave_store,
            False,
        )

        # Do some manual creation of objects in master
        # Specifically:
        #  - a master-specific PlatformType, and a shared-by-name PlatformType
        #  - a master-specific Platform and a shared-by-name Platform
        #  - a master-specific and shared-by-name Synonym

        # Create a change ID first
        with self.master_store.session_scope():
            change_id = self.master_store.add_to_changes(
                "TEST", datetime.utcnow(), "TEST"
            ).change_id
            self.master_store.add_to_platform_types("Master_PT_1", change_id=change_id)
            self.master_store.add_to_platform_types("Shared_PT_1", change_id=change_id)

            m_plat_1 = self.master_store.add_to_platforms(
                "Master_Platform_1", "123", "UK", "Warship", "Public", change_id=change_id
            )
            shared_plat_1 = self.master_store.add_to_platforms(
                "Shared_Platform_1", "234", "UK", "Warship", "Public", change_id=change_id
            )

            self.master_store.add_to_synonyms(
                "Platforms", "Master_Platform_1_Synonym", m_plat_1.platform_id, change_id=change_id
            )
            self.master_store.add_to_synonyms(
                "Platforms",
                "Shared_Platform_1_Synonym",
                shared_plat_1.platform_id,
                change_id=change_id,
            )

        # Do some manual creation of objects in slave
        # Specifically
        #  - a slave-specific PlatformType, and a shared-by-name PlatformType (from above)
        #  - a slave-specific Platform and a shared-by-name Platform (from above)
        #  - a slave-specific Synonym and a shared-by-name Synonym (from above)

        # Create a change ID first
        with self.slave_store.session_scope():
            change_id = self.slave_store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id

            self.slave_store.add_to_platform_types("Slave_PT_1", change_id=change_id)
            self.slave_store.add_to_platform_types("Shared_PT_1", change_id=change_id)

            s_plat_1 = self.slave_store.add_to_platforms(
                "Slave_Platform_1", "123", "UK", "Warship", "Public", change_id=change_id
            )
            shared_plat_1 = self.slave_store.add_to_platforms(
                "Shared_Platform_1", "234", "UK", "Warship", "Public", change_id=change_id
            )

            self.slave_store.add_to_synonyms(
                "Platforms", "Slave_Platform_1_Synonym", s_plat_1.platform_id, change_id=change_id
            )
            self.slave_store.add_to_synonyms(
                "Platforms",
                "Shared_Platform_1_Synonym",
                shared_plat_1.platform_id,
                change_id=change_id,
            )

    def tearDown(self):
        if os.path.exists("master.sqlite"):
            os.remove("master.sqlite")

        if os.path.exists("slave_exported.sqlite"):
            os.remove("slave_exported.sqlite")

    def test_export_alter_merge(self):
        # A bug that was hard to replicate seemed to be affected by whether you had closed
        # the data_store (or maybe just the session on the data_store?) between operations
        # So, for example, opening Pepys Admin, creating the schema, then doing a merge worked fine
        # (as the data_store/session was already open), but closing Pepys Admin after creating the schema
        # re-opening it, and doing the merge failed - as the data_store wasn't properly initialised somehow?
        # This wasn't caught in this test originally, as we re-used the master_store and slave_store from the
        # setUp method.
        # Now, we explicitly 'unset' the master and slave stores, and then recreate them (with the same parameters
        # as in setUp), and now the test represents real life more accurately (and fails correctly, before we fixed
        # the bug)
        self.master_store = None
        self.slave_store = None

        self.slave_store = DataStore(
            "", "", "", 0, db_name="slave_exported.sqlite", db_type="sqlite"
        )

        self.master_store = DataStore(
            db_name="test",
            db_host="localhost",
            db_username="postgres",
            db_password="postgres",
            db_port=55527,
            db_type="postgres",
        )

        self.merge_class = MergeDatabases(self.master_store, self.slave_store)

        # Do the merge
        self.merge_class.merge_all_tables()

        with self.master_store.session_scope():
            with self.slave_store.session_scope():
                # Check we have four datafiles in master
                datafiles = self.master_store.session.query(
                    self.master_store.db_classes.Datafile
                ).all()

                assert len(datafiles) == 4

                # Check one of these datafiles is called uk_track.rep
                references = [d.reference for d in datafiles]

                assert "uk_track.rep" in references

                # Check we have 425 rows in States
                states_count = self.master_store.session.query(
                    self.master_store.db_classes.State
                ).count()

                assert states_count == 425

                # Check we have objects with the slave's new default resolver values

                # Platform
                platform_results = (
                    self.master_store.session.query(self.master_store.db_classes.Platform)
                    .filter(self.master_store.db_classes.Platform.identifier == "123-SLAVE")
                    .all()
                )

                assert len(platform_results) == 1

                # Privacy
                privacy_results = (
                    self.master_store.session.query(self.master_store.db_classes.Privacy)
                    .filter(self.master_store.db_classes.Privacy.name == "PRIVACY-1-SLAVE")
                    .all()
                )

                assert len(privacy_results) == 1

                # Check we have merged PlatformTypes correctly
                pt_results = self.master_store.session.query(
                    self.master_store.db_classes.PlatformType
                ).all()

                pt_names = [pt.name for pt in pt_results]

                assert len(pt_names) == 5

                assert "Master_PT_1" in pt_names
                assert "Shared_PT_1" in pt_names
                assert "Slave_PT_1" in pt_names

                # Check we have merged Platforms correctly
                platform_results = self.master_store.session.query(
                    self.master_store.db_classes.Platform
                ).all()

                platform_names = [p.name for p in platform_results]

                assert len(platform_names) == 9

                assert "Master_Platform_1" in platform_names
                assert "Slave_Platform_1" in platform_names
                assert "Shared_Platform_1" in platform_names

                # Check we have merged Synonyms properly
                synonym_results = self.master_store.session.query(
                    self.master_store.db_classes.Synonym
                ).all()

                assert len(synonym_results) == 3

                # All Synonyms should link to an entry in the Platforms table
                for synonym_result in synonym_results:
                    platforms = (
                        self.master_store.session.query(self.master_store.db_classes.Platform)
                        .filter(
                            self.master_store.db_classes.Platform.platform_id
                            == synonym_result.entity
                        )
                        .all()
                    )

                    assert len(platforms) == 1


class TestExportDoNothingAndMerge(unittest.TestCase):
    @patch("pepys_admin.snapshot_cli.ptk_prompt", return_value="slave_exported.sqlite")
    @patch("pepys_admin.snapshot_cli.iterfzf", return_value=["Public"])
    def setUp(self, patched_input, patched_iterfzf):
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

        self.merge_class = MergeDatabases(self.master_store, self.slave_store)

    def tearDown(self):
        if os.path.exists("master.sqlite"):
            os.remove("master.sqlite")

        if os.path.exists("slave_exported.sqlite"):
            os.remove("slave_exported.sqlite")

    def test_export_do_nothing_and_merge(self):
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            # Do the merge
            self.merge_class.merge_all_tables()
        output = temp_output.getvalue()

        print(output)

        # As we didn't do anything to the exported snapshot before merging it, there should be no new things to copy
        # so everything will be found as 'already there', and nothing will be in the 'added' or 'modified' columns

        # Check statistics
        assert "| CommentType        |                 2 |       0 |          0 |" in output
        assert "| DatafileType       |                 2 |       0 |          0 |" in output
        assert "| Nationality        |                 1 |       0 |          0 |" in output
        assert "| PlatformType       |                 1 |       0 |          0 |" in output
        assert "| Privacy            |                 1 |       0 |          0 |" in output
        assert "| SensorType         |                 2 |       0 |          0 |" in output
        assert "| Platform           |                 4 |       0 |          0 |" in output
        assert "| Sensor             |                 5 |       0 |          0 |" in output
        assert "| State       |       0 |" in output

        # Check entries added list
        assert "No entries added" in output


class TestGeometryMerge(unittest.TestCase):
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

        with self.slave_store.session_scope():
            change_id = self.slave_store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id
            self.slave_store.add_to_privacies("Public", level=0, change_id=change_id)
            self.slave_store.add_to_datafile_types("TestDFT", change_id=change_id)
            geom_type_obj = self.slave_store.add_to_geometry_types(
                "TestGeomType", change_id=change_id
            )
            geom_sub_type_id = self.slave_store.add_to_geometry_sub_types(
                "TestGeomSubType", parent_name=geom_type_obj.name, change_id=change_id
            ).geo_sub_type_id
            datafile = self.slave_store.add_to_datafiles(
                "Public",
                "TestDFT",
                reference="TestDatafile",
                file_hash="HASH",
                file_size=100,
                change_id=change_id,
            )
            datafile.measurements["TestParser"] = {}
            datafile.create_geometry(
                self.slave_store,
                "SRID=4326;POINT (-1.5 50.5)",
                geom_type_obj.geo_type_id,
                geom_sub_type_id,
                "TestParser",
            )
            datafile.create_geometry(
                self.slave_store,
                "SRID=4326;LINESTRING (-1 0, -2 0, -3 1)",
                geom_type_obj.geo_type_id,
                geom_sub_type_id,
                "TestParser",
            )
            datafile.commit(self.slave_store, change_id=change_id)

        self.merge_class = MergeDatabases(self.master_store, self.slave_store)

    def tearDown(self):
        # if os.path.exists("master.sqlite"):
        #     os.remove("master.sqlite")

        # if os.path.exists("slave.sqlite"):
        #     os.remove("slave.sqlite")
        pass

    def test_geometry_merge(self):
        # Do the merge
        self.merge_class.merge_all_tables()

        with self.master_store.session_scope():
            master_geoms = self.master_store.session.query(
                self.master_store.db_classes.Geometry1
            ).all()

            assert len(master_geoms) == 2

            assert master_geoms[0].geometry is not None
            assert master_geoms[1].geometry is not None

            shapely_geom = to_shape(master_geoms[0].geometry)
            assert shapely_geom.wkt == "POINT (-1.5 50.5)"

            shapely_geom = to_shape(master_geoms[1].geometry)
            assert shapely_geom.wkt == "LINESTRING (-1 0, -2 0, -3 1)"


if __name__ == "__main__":
    unittest.main()
