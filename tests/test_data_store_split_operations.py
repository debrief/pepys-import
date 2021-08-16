from datetime import datetime, timedelta
from unittest import TestCase

from sqlalchemy_utils import dependent_objects

from pepys_import.core.store.data_store import DataStore


class SplitPlatformTestCase(TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()
        self.parser_name = "Test Importer"
        self.current_time = datetime.utcnow()

        with self.store.session_scope():
            self.change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id
            self.nationality = self.store.add_to_nationalities(
                "test_nationality", self.change_id
            ).name
            self.platform_type = self.store.add_to_platform_types(
                "test_platform_type", self.change_id
            ).name
            self.sensor_type = self.store.add_to_sensor_types(
                "test_sensor_type", self.change_id
            ).name
            self.comment_type = self.store.add_to_comment_types("test_type", self.change_id)
            self.privacy = self.store.add_to_privacies("test_privacy", 0, self.change_id)
            self.privacy_id = self.privacy.privacy_id
            self.privacy = self.privacy.name
            self.file = self.store.get_datafile("test_file", "csv", 0, "HASHED", self.change_id)
            self.file.measurements[self.parser_name] = dict()
            self.file_2 = self.store.get_datafile(
                "test_file_2", "csv", 100, "HASHED", self.change_id
            )
            self.file_2.measurements[self.parser_name] = dict()

            self.store.session.expunge(self.file)
            self.store.session.expunge(self.file_2)
            self.store.session.expunge(self.comment_type)

    def test_split_platform_with_different_sensors(self):
        Comment = self.store.db_classes.Comment
        Platform = self.store.db_classes.Platform
        Sensor = self.store.db_classes.Sensor
        with self.store.session_scope():
            platform = self.store.get_platform(
                platform_name="Test Platform",
                nationality=self.nationality,
                platform_type=self.platform_type,
                privacy=self.privacy,
                change_id=self.change_id,
            )
            sensor = platform.get_sensor(
                self.store, "gps", self.sensor_type, change_id=self.change_id
            )
            sensor_2 = platform.get_sensor(
                self.store, "gps_2", self.sensor_type, change_id=self.change_id
            )
            self.file.create_state(
                self.store,
                platform,
                sensor,
                self.current_time,
                parser_name=self.parser_name,
            )
            self.file.create_state(
                self.store,
                platform,
                sensor,
                self.current_time + timedelta(seconds=5),
                parser_name=self.parser_name,
            )
            self.file.create_comment(
                self.store,
                platform,
                self.current_time,
                "Comment",
                self.comment_type,
                parser_name=self.parser_name,
            )
            self.file_2.create_contact(
                self.store,
                platform,
                sensor_2,
                self.current_time + timedelta(seconds=10),
                parser_name=self.parser_name,
            )
            self.file_2.create_contact(
                self.store,
                platform,
                sensor_2,
                self.current_time + timedelta(seconds=15),
                parser_name=self.parser_name,
            )
            self.file_2.create_comment(
                self.store,
                platform,
                self.current_time,
                "Comment from Datafile-2",
                self.comment_type,
                parser_name=self.parser_name,
            )
            if self.file.validate():
                self.file.commit(self.store, self.change_id)
            if self.file_2.validate():
                self.file_2.commit(self.store, self.change_id)

            # Assert that there is only 1 platform with the given name
            platforms_before_merge = (
                self.store.session.query(Platform).filter(Platform.name == platform.name).all()
            )
            dependent_objects_before_merge = list(dependent_objects(platforms_before_merge[0]))
            assert len(platforms_before_merge) == 1
            assert len(dependent_objects_before_merge) == 4  # 2 Sensors, 2 Comments
            assert sensor.host == platform.platform_id
            assert sensor_2.host == platform.platform_id
            assert (
                len(
                    self.store.session.query(Comment)
                    .filter(Comment.platform_id == platform.platform_id)
                    .all()
                )
                == 2
            )
            self.store.split_platform(platform.platform_id)

            # There should be 2 platforms, per each datafile
            platforms_after_merge = (
                self.store.session.query(Platform).filter(Platform.name == platform.name).all()
            )
            assert len(platforms_after_merge) == 2
            for p in platforms_after_merge:
                dependent_objects_after_merge = list(dependent_objects(p))
                assert len(dependent_objects_after_merge) == 2  # 1 Sensor, 1 Comment
                assert (
                    len(
                        self.store.session.query(Comment)
                        .filter(Comment.platform_id == p.platform_id)
                        .all()
                    )
                    == 1
                )

                new_sensor = (
                    self.store.session.query(Sensor).filter(Sensor.host == p.platform_id).scalar()
                )
                assert new_sensor is not None

            # Assert that split platform and sensors deleted
            assert (
                not self.store.session.query(Platform)
                .filter(Platform.platform_id == platform.platform_id)
                .scalar()
            )
            assert (
                not self.store.session.query(Sensor)
                .filter(Sensor.sensor_id == sensor.sensor_id)
                .scalar()
            )
            assert (
                not self.store.session.query(Sensor)
                .filter(Sensor.sensor_id == sensor_2.sensor_id)
                .scalar()
            )

    def test_split_platform_with_one_sensor(self):
        Platform = self.store.db_classes.Platform
        Sensor = self.store.db_classes.Sensor
        with self.store.session_scope():
            platform = self.store.get_platform(
                platform_name="Test Platform",
                nationality=self.nationality,
                platform_type=self.platform_type,
                privacy=self.privacy,
                change_id=self.change_id,
            )
            sensor = platform.get_sensor(
                self.store, "gps", self.sensor_type, change_id=self.change_id
            )
            self.file.create_state(
                self.store,
                platform,
                sensor,
                self.current_time,
                parser_name=self.parser_name,
            )
            self.file_2.create_state(
                self.store,
                platform,
                sensor,
                self.current_time + timedelta(seconds=5),
                parser_name=self.parser_name,
            )
            if self.file.validate():
                self.file.commit(self.store, self.change_id)
            if self.file_2.validate():
                self.file_2.commit(self.store, self.change_id)

            # Assert that there is only 1 platform with the given name
            platforms_before_merge = (
                self.store.session.query(Platform).filter(Platform.name == platform.name).all()
            )
            dependent_objects_before_merge = list(dependent_objects(platforms_before_merge[0]))
            assert len(platforms_before_merge) == 1
            assert len(dependent_objects_before_merge) == 1  # 1 Sensor
            assert sensor.host == platform.platform_id

            self.store.split_platform(platform.platform_id)

            # There should be 2 platforms, per each datafile
            platforms_after_merge = (
                self.store.session.query(Platform).filter(Platform.name == platform.name).all()
            )
            assert len(platforms_after_merge) == 2
            for p in platforms_after_merge:
                dependent_objects_after_merge = list(dependent_objects(p))
                assert len(dependent_objects_after_merge) == 1  # 1 Sensor

                new_sensor = (
                    self.store.session.query(Sensor).filter(Sensor.host == p.platform_id).scalar()
                )
                assert new_sensor is not None

                measurement_objects = list(dependent_objects(new_sensor))
                assert len(measurement_objects) == 1  # 1 State

            # Assert that split platform and sensors deleted
            assert (
                not self.store.session.query(Platform)
                .filter(Platform.platform_id == platform.platform_id)
                .scalar()
            )
            assert (
                not self.store.session.query(Sensor)
                .filter(Sensor.sensor_id == sensor.sensor_id)
                .scalar()
            )
