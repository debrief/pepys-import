import unittest
from datetime import datetime
from unittest import TestCase

from pepys_import.core.store.data_store import DataStore
from pepys_import.core.store.table_summary import TableSummary, TableSummarySet


class TableSummarySetTestCase(TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()
        with self.store.session_scope():
            self.change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id
            self.store.add_to_privacies("TEST-1", 0, self.change_id)
            self.store.add_to_privacies("TEST-2", 0, self.change_id)

    def tearDown(self):
        pass

    def test_table_summary_returns_correct_values(self):
        """Test whether Table Summary class returns correct values or not"""

        with self.store.session_scope():
            summary = TableSummary(self.store.session, self.store.db_classes.Privacy)

            # Two entities created, created_date can't be null
            self.assertEqual(summary.number_of_rows, 2)
            self.assertNotEqual(summary.created_date, "-")

            # There is no entity in State table
            summary = TableSummary(self.store.session, self.store.db_classes.State)
            self.assertEqual(summary.number_of_rows, 0)
            self.assertEqual(summary.created_date, "-")


class TableSummaryTestCase(TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()
        with self.store.session_scope():
            self.change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id
            self.store.add_to_privacies("TEST-1", 0, self.change_id)
            self.store.add_to_nationalities("NAT-1", self.change_id)
            self.store.add_to_nationalities("NAT-2", self.change_id)
            privacy_sum = TableSummary(self.store.session, self.store.db_classes.Privacy)
            nationality_sum = TableSummary(self.store.session, self.store.db_classes.Nationality)
        self.summaries = [privacy_sum, nationality_sum]

    def tearDown(self):
        pass

    def test_report_works(self):
        """Test whether report method returns correct string or not"""
        table_summary_set = TableSummarySet(self.summaries)
        report = table_summary_set.report()
        self.assertIn("Privacies", report)
        self.assertIn("1", report)
        self.assertIn("Nationalities", report)
        self.assertIn("2", report)

    def test_show_delta_of_rows_added_works_correctly(self):
        """Test whether show_delta_of_rows_added method returns correct values or not"""
        first_table_summary_set = TableSummarySet(self.summaries)

        with self.store.session_scope():
            self.store.add_to_privacies("TEST-2", 0, self.change_id)
            self.store.add_to_privacies("TEST-3", 0, self.change_id)
            privacy_sum = TableSummary(self.store.session, self.store.db_classes.Privacy)
            nationality_sum = TableSummary(self.store.session, self.store.db_classes.Nationality)
        second_summary = [privacy_sum, nationality_sum]
        second_table_summary_set = TableSummarySet(second_summary)
        result = second_table_summary_set.show_delta_of_rows_added(first_table_summary_set)

        # Privacy table has 2 new rows, no changes for Nationality table
        assert "| Privacies    |                2 |" in result

    def test_show_delta_of_rows_added_metadata_works_correctly(self):
        """Test whether show_delta_of_rows_added metadata method returns correct values or not"""

        with self.store.session_scope():
            platform_sum = TableSummary(self.store.session, self.store.db_classes.Platform)
            sensor_sum = TableSummary(self.store.session, self.store.db_classes.Sensor)
            first_table_summary_set = TableSummarySet([platform_sum, sensor_sum])

            self.store.add_to_platform_types("PlatformType1", self.change_id)
            self.store.add_to_sensor_types("GPS", self.change_id)
            self.store.add_to_platforms(
                "Platform1", "123", "NAT-1", "PlatformType1", "TEST-1", change_id=self.change_id
            )
            platform = self.store.add_to_platforms(
                "Platform2", "234", "NAT-1", "PlatformType1", "TEST-1", change_id=self.change_id
            )
            self.store.add_to_sensors(
                name="TestSensor",
                sensor_type="GPS",
                host_id=platform.platform_id,
                host_name=None,
                host_nationality=None,
                host_identifier=None,
                privacy="TEST-1",
                change_id=self.change_id,
            )
            platform_sum = TableSummary(self.store.session, self.store.db_classes.Platform)
            sensor_sum = TableSummary(self.store.session, self.store.db_classes.Sensor)
        second_summary = [platform_sum, sensor_sum]
        second_table_summary_set = TableSummarySet(second_summary)
        result = second_table_summary_set.show_delta_of_rows_added_metadata(first_table_summary_set)

        # Platforms table has 2 new entities and Sensors table has 1 new entities
        assert "| Platforms    | Platform1,Platform2 |" in result
        assert "| Sensors      | TestSensor          |" in result

    def test_show_delta_of_rows_added_metadata_works_correctly_for_more_than_6_names(self):
        """Test whether show_delta_of_rows_added metadata method returns normal report
        if there are more than 6 entities for Platform or Sensor"""

        with self.store.session_scope():
            platform_sum = TableSummary(self.store.session, self.store.db_classes.Platform)
            sensor_sum = TableSummary(self.store.session, self.store.db_classes.Sensor)
            first_table_summary_set = TableSummarySet([platform_sum, sensor_sum])

            self.store.add_to_platform_types("PlatformType1", self.change_id)
            self.store.add_to_sensor_types("GPS", self.change_id)
            self.store.add_to_platforms(
                "Platform1", "123", "NAT-1", "PlatformType1", "TEST-1", change_id=self.change_id
            )
            self.store.add_to_platforms(
                "Platform2", "234", "NAT-1", "PlatformType1", "TEST-1", change_id=self.change_id
            )
            self.store.add_to_platforms(
                "Platform3", "123", "NAT-1", "PlatformType1", "TEST-1", change_id=self.change_id
            )
            self.store.add_to_platforms(
                "Platform4", "234", "NAT-1", "PlatformType1", "TEST-1", change_id=self.change_id
            )
            self.store.add_to_platforms(
                "Platform5", "123", "NAT-1", "PlatformType1", "TEST-1", change_id=self.change_id
            )
            self.store.add_to_platforms(
                "Platform6", "123", "NAT-1", "PlatformType1", "TEST-1", change_id=self.change_id
            )
            platform = self.store.add_to_platforms(
                "Platform7", "234", "NAT-1", "PlatformType1", "TEST-1", change_id=self.change_id
            )
            self.store.add_to_sensors(
                name="TestSensor",
                sensor_type="GPS",
                host_id=platform.platform_id,
                host_name=None,
                host_nationality=None,
                host_identifier=None,
                privacy="TEST-1",
                change_id=self.change_id,
            )
            platform_sum = TableSummary(self.store.session, self.store.db_classes.Platform)
            sensor_sum = TableSummary(self.store.session, self.store.db_classes.Sensor)
        second_summary = [platform_sum, sensor_sum]
        second_table_summary_set = TableSummarySet(second_summary)
        result = second_table_summary_set.show_delta_of_rows_added_metadata(first_table_summary_set)

        # Platforms table has 7 new entities and Sensors table has 1 new entities
        assert "| Platforms    |                7 |" in result
        assert "| Sensors      |                1 |" in result


if __name__ == "__main__":
    unittest.main()
