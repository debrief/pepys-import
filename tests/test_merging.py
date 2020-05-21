import os
import unittest
from datetime import datetime

from pepys_admin.merge import merge_reference_table
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
        # os.remove("master.db")
        # os.remove("slave.db")
        pass

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
