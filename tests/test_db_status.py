import contextlib
import unittest

from pepys_import.core.store.data_store import DataStore
from pepys_import.core.store.db_status import DBStatus, TableTypes
from unittest import TestCase
from io import StringIO


class DBStatusTestCase(TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()
        self.table_types = [
            TableTypes.METADATA,
            TableTypes.MEASUREMENT,
            TableTypes.REFERENCE,
        ]
        self.db_status = DBStatus(self.store, self.table_types)

    def tearDown(self):
        pass

    def test_get_status(self):
        """Test whether status is successfully returned"""
        with self.store.session_scope() as session:
            status = self.db_status.get_status()
        self.assertIn("Sensors", status.keys())
        self.assertIn("SensorTypes", status.keys())
        self.assertIn("States", status.keys())

    @unittest.expectedFailure
    def test_print_when_status_is_none(self):
        """Test whether status is successfully printed"""
        self.db_status.print_status()

    def test_print_status(self):
        """Test whether status is successfully printed"""
        temp_stdout = StringIO()
        with self.store.session_scope() as session:
            self.db_status.get_status()
            with contextlib.redirect_stdout(temp_stdout):
                self.db_status.print_status()
        output = temp_stdout.getvalue().strip()
        self.assertIn("Sensors", output)
        self.assertIn("SensorTypes", output)
        self.assertIn("States", output)

    def test_calculate_diff(self):
        """
        Test whether the difference between two database snapshots are successfully
        calculated
        """
        with self.store.session_scope() as session:
            prev_status = self.db_status.get_status()
            self.store.add_to_privacies("1")
            self.store.add_to_privacies("2")
            self.db_status.get_status()
            diff = self.db_status.calculate_diff("Privacies", prev_status)

        self.assertEqual(diff, 2)


if __name__ == "__main__":
    unittest.main()
