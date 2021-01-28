from datetime import datetime
from unittest import TestCase

from pepys_admin.maintenance.widgets.filter_widget_utils import filter_widget_output_to_query
from pepys_import.core.store.data_store import DataStore


class TestConversions(TestCase):
    def setUp(self) -> None:
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()
        self.parser_name = "Test Importer"
        self.current_time = datetime.utcnow()

        with self.store.session_scope():
            self.change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id
            self.nationality = self.store.add_to_nationalities("France", self.change_id).name
            self.nationality_2 = self.store.add_to_nationalities(
                "United Kingdom", self.change_id
            ).name
            self.platform_type = self.store.add_to_platform_types(
                "Platform Type", self.change_id
            ).name
            self.platform_type_2 = self.store.add_to_platform_types(
                "Platform Type 2", self.change_id
            ).name
            self.sensor_type = self.store.add_to_sensor_types(
                "test_sensor_type", self.change_id
            ).name
            self.comment_type = self.store.add_to_comment_types("test_type", self.change_id)
            self.privacy = self.store.add_to_privacies("test_privacy", 0, self.change_id)
            self.privacy_id = self.privacy.privacy_id
            self.file = self.store.get_datafile("test_file", "csv", 0, "HASHED", self.change_id)
            self.file.measurements[self.parser_name] = dict()

            self.platform = self.store.get_platform(
                platform_name="Test Platform",
                nationality=self.nationality,
                platform_type=self.platform_type,
                privacy=self.privacy.name,
                change_id=self.change_id,
            )
            self.sensor = self.platform.get_sensor(
                self.store, "gps", self.sensor_type, change_id=self.change_id
            ).sensor_id
            self.platform_2 = self.store.get_platform(
                platform_name="Test Platform 2",
                nationality=self.nationality_2,
                platform_type=self.platform_type_2,
                privacy=self.privacy.name,
                change_id=self.change_id,
            )

            self.store.session.expunge(self.file)
            self.store.session.expunge(self.comment_type)
            self.store.session.expunge(self.platform)
            self.store.session.expunge(self.platform_2)

    def test_one_query(self):
        with self.store.session_scope():
            Platform = self.store.db_classes.Platform
            query_list = [["name", "=", self.platform.name]]
            filter_query = filter_widget_output_to_query(query_list, "Platforms", self.store)
            result = self.store.session.query(Platform).filter(filter_query).all()
            assert len(result) == 1
            assert result[0].platform_id == self.platform.platform_id

    def test_two_with_and(self):
        with self.store.session_scope():
            Platform = self.store.db_classes.Platform
            query_list = [
                ["name", "=", self.platform.name],
                ["AND"],
                ["name", "=", self.platform_2.name],
            ]
            filter_query = filter_widget_output_to_query(query_list, "Platforms", self.store)
            result = self.store.session.query(Platform).filter(filter_query).all()
            assert len(result) == 0

    def test_queries_with_or(self):
        with self.store.session_scope():
            Platform = self.store.db_classes.Platform
            query_list = [
                ["name", "=", self.platform.name],
                ["OR"],
                ["name", "=", self.platform_2.name],
            ]
            filter_query = filter_widget_output_to_query(query_list, "Platforms", self.store)
            result = self.store.session.query(Platform).filter(filter_query).all()
            assert len(result) == 2
            assert result[0].platform_id == self.platform.platform_id
            assert result[1].platform_id == self.platform_2.platform_id

    def test_like_query(self):
        with self.store.session_scope():
            Platform = self.store.db_classes.Platform
            query_list = [
                ["name", "LIKE", "Test"]
            ]  # Should filter both "Test Platform" and "Test Platform 2"
            filter_query = filter_widget_output_to_query(query_list, "Platforms", self.store)
            result = self.store.session.query(Platform).filter(filter_query).all()
            assert len(result) == 2
            assert result[0].platform_id == self.platform.platform_id
            assert result[1].platform_id == self.platform_2.platform_id

    def test_not_equal_query(self):
        with self.store.session_scope():
            Platform = self.store.db_classes.Platform
            query_list = [["name", "!=", self.platform.name]]
            filter_query = filter_widget_output_to_query(query_list, "Platforms", self.store)
            result = self.store.session.query(Platform).filter(filter_query).all()
            assert len(result) == 1
            assert result[0].name != self.platform.name
            assert result[0].platform_id == self.platform_2.platform_id
