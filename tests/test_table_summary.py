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
        """Test whether Table Summary class returns correct values or not """

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


if __name__ == "__main__":
    unittest.main()
