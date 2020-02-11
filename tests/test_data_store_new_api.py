import unittest
import os

from datetime import datetime
from pepys_import.core.store.data_store import DataStore
from unittest import TestCase

FILE_PATH = os.path.dirname(__file__)
TEST_DATA_PATH = os.path.join(FILE_PATH, "sample_data", "csv_files")


class DataStoreTestCase(TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()
        with self.store.session_scope() as session:
            self.nationality = self.store.add_to_nationalities("test_nationality").name
            self.platform_type = self.store.add_to_platform_types(
                "test_platform_type"
            ).name
            self.privacy = self.store.add_to_privacies("test_privacy").name

    def tearDown(self):
        pass

    def test_new_datafile_added_successfully(self):
        """Test whether a new datafile is created successfully or not"""

        with self.store.session_scope() as session:
            datafiles = self.store.session.query(self.store.db_classes.Datafiles).all()

        # there must be no entry at the beginning
        self.assertEqual(len(datafiles), 0)

        with self.store.session_scope() as session:
            self.store.get_datafile("test_file.csv", "csv")

        # there must be one entry
        with self.store.session_scope() as session:
            datafiles = self.store.session.query(self.store.db_classes.Datafiles).all()
            self.assertEqual(len(datafiles), 1)
            self.assertEqual(datafiles[0].reference, "test_file.csv")

    def test_present_datafile_not_added(self):
        """Test whether present datafile is not created"""

        with self.store.session_scope() as session:
            datafiles = self.store.session.query(self.store.db_classes.Datafiles).all()

        # there must be no entry at the beginning
        self.assertEqual(len(datafiles), 0)

        with self.store.session_scope() as session:
            self.store.get_datafile("test_file.csv", "csv")
            self.store.get_datafile("test_file.csv", "csv")

            # there must be one entry
            datafiles = self.store.session.query(self.store.db_classes.Datafiles).all()
            self.assertEqual(len(datafiles), 1)
            self.assertEqual(datafiles[0].reference, "test_file.csv")

    @unittest.skip("Skip until missing data resolver is implemented.")
    def test_missing_data_resolver_works_for_datafile(self):
        pass

    def test_new_platform_added_successfully(self):
        """Test whether a new platform is created successfully or not"""

        with self.store.session_scope() as session:
            platforms = self.store.session.query(self.store.db_classes.Platforms).all()

        # there must be no entry at the beginning
        self.assertEqual(len(platforms), 0)

        with self.store.session_scope() as session:
            self.store.get_platform(
                "Test Platform",
                nationality=self.nationality,
                platform_type=self.platform_type,
                privacy=self.privacy,
            )

        # there must be one entry
        with self.store.session_scope() as session:
            platforms = self.store.session.query(self.store.db_classes.Platforms).all()

            self.assertEqual(len(platforms), 1)
            self.assertEqual(platforms[0].name, "Test Platform")

    def test_present_platform_not_added(self):
        """Test whether present platform is not created"""

        with self.store.session_scope() as session:
            platforms = self.store.session.query(self.store.db_classes.Platforms).all()

        # there must be no entry at the beginning
        self.assertEqual(len(platforms), 0)

        with self.store.session_scope() as session:
            self.store.get_platform(
                "Test Platform",
                nationality=self.nationality,
                platform_type=self.platform_type,
                privacy=self.privacy,
            )
            self.store.get_platform(
                "Test Platform",
                nationality=self.nationality,
                platform_type=self.platform_type,
                privacy=self.privacy,
            )

        # there must be one entry
        with self.store.session_scope() as session:
            platforms = self.store.session.query(self.store.db_classes.Platforms).all()

            self.assertEqual(len(platforms), 1)
            self.assertEqual(platforms[0].name, "Test Platform")

    @unittest.skip("Skip until missing data resolver is implemented.")
    def test_missing_data_resolver_works_for_platform(self):
        pass


class DataStoreStatusTestCase(TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()
        self.store.populate_reference(TEST_DATA_PATH)
        self.store.populate_metadata(TEST_DATA_PATH)
        self.store.populate_measurement(TEST_DATA_PATH)

    def tearDown(self):
        pass

    def test_get_status_of_measurement(self):
        """Test whether summary contents correct for measurement tables"""

        table_summary_object = self.store.get_status(report_measurement=True)
        report = table_summary_object.report()

        self.assertNotEqual(report, "")
        self.assertIn("States", report)
        self.assertIn("Contacts", report)
        self.assertIn("Activations", report)

    def test_get_status_of_metadata(self):
        """Test whether summary contents correct for metadata tables"""

        table_summary_object = self.store.get_status(report_metadata=True)
        report = table_summary_object.report()

        self.assertNotEqual(report, "")
        self.assertIn("Sensors", report)
        self.assertIn("Platforms", report)
        self.assertIn("Datafiles", report)

    def test_get_status_of_reference(self):
        """Test whether summary contents correct for reference tables"""

        table_summary_object = self.store.get_status(report_reference=True)
        report = table_summary_object.report()

        self.assertNotEqual(report, "")
        self.assertIn("Nationalities", report)
        self.assertIn("Privacies", report)
        self.assertIn("PlatformTypes", report)


class SensorTestCase(TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()
        with self.store.session_scope() as session:
            self.nationality = self.store.add_to_nationalities("test_nationality").name
            self.platform_type = self.store.add_to_platform_types(
                "test_platform_type"
            ).name
            self.sensor_type = self.store.add_to_sensor_types("test_sensor_type").name
            self.privacy = self.store.add_to_privacies("test_privacy").name

            self.platform = self.store.get_platform(
                "Test Platform",
                nationality=self.nationality,
                platform_type=self.platform_type,
                privacy=self.privacy,
            )

    def tearDown(self):
        pass

    def test_new_sensor_added_successfully(self):
        """Test whether a new sensor is created"""
        with self.store.session_scope() as session:
            sensors = self.store.session.query(self.store.db_classes.Sensors).all()

            # there must be no entry at the beginning
            self.assertEqual(len(sensors), 0)

            self.platform.get_sensor(
                self.store.session, sensors, "gps", self.sensor_type
            )

        # there must be one entry
        with self.store.session_scope() as session:
            sensors = self.store.session.query(self.store.db_classes.Sensors).all()
            self.assertEqual(len(sensors), 1)
            self.assertEqual(sensors[0].name, "gps")

    def test_present_sensor_not_added(self):
        """Test whether present sensor is not created"""
        with self.store.session_scope() as session:
            sensors = self.store.session.query(self.store.db_classes.Sensors).all()

            # there must be no entry at the beginning
            self.assertEqual(len(sensors), 0)

            self.platform.get_sensor(
                self.store.session, sensors, "gps", self.sensor_type
            )

            # query Sensors table again and try to add the same entity
            sensors = self.store.session.query(self.store.db_classes.Sensors).all()
            self.platform.get_sensor(
                self.store.session, sensors, "gps", self.sensor_type
            )

            # there must be one entry
            sensors = self.store.session.query(self.store.db_classes.Sensors).all()

        self.assertEqual(len(sensors), 1)

    @unittest.skip("Skip until missing data resolver is implemented.")
    def test_missing_data_resolver_works_for_sensor(self):
        pass


class MeasurementsTestCase(TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()
        with self.store.session_scope() as session:
            self.nationality = self.store.add_to_nationalities("test_nationality").name
            self.platform_type = self.store.add_to_platform_types(
                "test_platform_type"
            ).name
            self.sensor_type = self.store.add_to_sensor_types("test_sensor_type").name
            self.privacy = self.store.add_to_privacies("test_privacy").name

            self.platform = self.store.get_platform(
                "Test Platform",
                nationality=self.nationality,
                platform_type=self.platform_type,
                privacy=self.privacy,
            )
            sensors = self.store.session.query(self.store.db_classes.Sensors).all()
            self.sensor = self.platform.get_sensor(
                self.store.session, sensors, "gps", self.sensor_type
            )
            self.comment_type = self.store.add_to_comment_types("test_type")
            self.file = self.store.get_datafile("test_file", "csv")
            self.current_time = datetime.utcnow()

            self.store.session.expunge(self.sensor)
            self.store.session.expunge(self.platform)
            self.store.session.expunge(self.file)
            self.store.session.expunge(self.comment_type)

    def tearDown(self):
        pass

    def test_new_state_created_successfully(self):
        """Test whether a new state is created"""
        with self.store.session_scope() as session:
            states = self.store.session.query(self.store.db_classes.States).all()

            # there must be no entry at the beginning
            self.assertEqual(len(states), 0)

            state = self.file.create_state(self.sensor, self.current_time)

            # there must be no entry because it's kept in-memory
            states = self.store.session.query(self.store.db_classes.States).all()
            self.assertEqual(len(states), 0)

            self.assertEqual(state.time, self.current_time)

            if self.file.validate():
                state.submit(self.store.session)
                states = self.store.session.query(self.store.db_classes.States).all()
            self.assertEqual(len(states), 1)

    @unittest.skip("Skip until missing data resolver is implemented.")
    def test_missing_data_resolver_works_for_state(self):
        pass

    def test_new_contact_created_successfully(self):
        """Test whether a new contact is created"""

        with self.store.session_scope() as session:
            contacts = self.store.session.query(self.store.db_classes.Contacts).all()

            # there must be no entry at the beginning
            self.assertEqual(len(contacts), 0)

            contact = self.file.create_contact(self.sensor, self.current_time)

            # there must be no entry because it's kept in-memory
            contacts = self.store.session.query(self.store.db_classes.Contacts).all()
            self.assertEqual(len(contacts), 0)

            # Fill null constraint field
            contact.set_name("TEST")
            if self.file.validate():
                contact.submit(self.store.session)
                contacts = self.store.session.query(
                    self.store.db_classes.Contacts
                ).all()
                self.assertEqual(len(contacts), 1)

    @unittest.skip("Skip until missing data resolver is implemented.")
    def test_missing_data_resolver_works_for_contact(self):
        pass

    def test_new_comment_created_successfully(self):
        """Test whether a new comment is created"""

        with self.store.session_scope() as session:
            comments = self.store.session.query(self.store.db_classes.Comments).all()

            # there must be no entry at the beginning
            self.assertEqual(len(comments), 0)

            comment = self.file.create_comment(
                self.sensor, self.current_time, "Comment", self.comment_type,
            )

            # there must be no entry because it's kept in-memory
            comments = self.store.session.query(self.store.db_classes.Comments).all()
            self.assertEqual(len(comments), 0)

            # Fill null constraint field
            comment.set_source(self.platform)
            if self.file.validate():
                comment.submit(self.store.session)
                comments = self.store.session.query(
                    self.store.db_classes.Comments
                ).all()
                self.assertEqual(len(comments), 1)

    @unittest.skip("Skip until missing data resolver is implemented.")
    def test_missing_data_resolver_works_for_comment(self):
        pass


if __name__ == "__main__":
    unittest.main()
