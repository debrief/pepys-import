from datetime import datetime
from unittest import TestCase
from uuid import UUID

import pytest
from geoalchemy2 import WKTElement
from sqlalchemy import or_

from pepys_import.core.store.data_store import DataStore


class MergePlatformsTestCase(TestCase):
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
            self.privacy = self.store.add_to_privacies("test_privacy", 0, self.change_id).name
            self.file = self.store.get_datafile("test_file", "csv", 0, "HASHED", self.change_id)
            self.file.measurements[self.parser_name] = dict()

            self.store.session.expunge(self.file)
            self.store.session.expunge(self.comment_type)

    def test_merge_platforms_with_same_sensor_names(self):
        """Create two platforms, each platform will have a sensor named gps.
        Check whether measurements moved to target platform"""
        State = self.store.db_classes.State
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
            ).sensor_id

            platform_2 = self.store.get_platform(
                platform_name="Test Platform 2",
                nationality=self.nationality,
                platform_type=self.platform_type,
                privacy=self.privacy,
                change_id=self.change_id,
            )
            sensor_2 = platform_2.get_sensor(
                self.store, "gps", self.sensor_type, change_id=self.change_id
            )
            self.file.create_state(
                self.store,
                platform_2,
                sensor_2,
                self.current_time,
                parser_name=self.parser_name,
            )
            self.file.create_state(
                self.store,
                platform_2,
                sensor_2,
                self.current_time,
                parser_name=self.parser_name,
            )
            self.file.create_contact(
                self.store,
                platform_2,
                sensor_2,
                self.current_time,
                parser_name=self.parser_name,
            )
            self.file.create_contact(
                self.store,
                platform_2,
                sensor_2,
                self.current_time,
                parser_name=self.parser_name,
            )
            if self.file.validate():
                self.file.commit(self.store, self.change_id)

            # Assert that target platform doesn't have any states or contacts
            sensors_before_merge = (
                self.store.session.query(Sensor).filter(Sensor.host == platform.platform_id).all()
            )
            states_before_merge = (
                self.store.session.query(State).filter(State.sensor_id == sensor).all()
            )
            contacts_before_merge = (
                self.store.session.query(State).filter(State.sensor_id == sensor).all()
            )
            assert len(sensors_before_merge) == 1
            assert len(states_before_merge) == 0
            assert len(contacts_before_merge) == 0

            self.store.merge_platforms([platform_2.platform_id], platform.platform_id)

            # There should be still one sensor, but that sensor should have two States and two Contacts
            sensors_after_merge = (
                self.store.session.query(Sensor).filter(Sensor.host == platform.platform_id).all()
            )
            states_after_merge = (
                self.store.session.query(State).filter(State.sensor_id == sensor).all()
            )
            contacts_after_merge = (
                self.store.session.query(State).filter(State.sensor_id == sensor).all()
            )
            assert len(sensors_after_merge) == 1
            assert len(states_after_merge) == 2
            assert len(contacts_after_merge) == 2

            # Assert that sensor_2 doesn't have any measurements because they are moved
            states_after_merge = (
                self.store.session.query(State).filter(State.sensor_id == sensor_2.sensor_id).all()
            )
            contacts_after_merge = (
                self.store.session.query(State).filter(State.sensor_id == sensor_2.sensor_id).all()
            )
            assert len(states_after_merge) == 0
            assert len(contacts_after_merge) == 0

    def test_merge_platforms_with_different_sensor_names(self):
        """Create two platforms, each platform will have a sensor named TEST-SENSOR.
        Check whether measurements moved to target platform"""
        State = self.store.db_classes.State
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
            ).sensor_id

            platform_2 = self.store.get_platform(
                platform_name="Test Platform 2",
                nationality=self.nationality,
                platform_type=self.platform_type,
                privacy=self.privacy,
                change_id=self.change_id,
            )
            sensor_2 = platform_2.get_sensor(
                self.store, "gps_2", self.sensor_type, change_id=self.change_id
            )
            self.file.create_state(
                self.store,
                platform_2,
                sensor_2,
                self.current_time,
                parser_name=self.parser_name,
            )
            self.file.create_state(
                self.store,
                platform_2,
                sensor_2,
                self.current_time,
                parser_name=self.parser_name,
            )
            self.file.create_contact(
                self.store,
                platform_2,
                sensor_2,
                self.current_time,
                parser_name=self.parser_name,
            )
            self.file.create_contact(
                self.store,
                platform_2,
                sensor_2,
                self.current_time,
                parser_name=self.parser_name,
            )
            if self.file.validate():
                self.file.commit(self.store, self.change_id)

            # Assert that target platform doesn't have any states or contacts
            sensors_before_merge = (
                self.store.session.query(Sensor).filter(Sensor.host == platform.platform_id).all()
            )
            states_before_merge = (
                self.store.session.query(State).filter(State.sensor_id == sensor).all()
            )
            contacts_before_merge = (
                self.store.session.query(State).filter(State.sensor_id == sensor).all()
            )
            assert len(sensors_before_merge) == 1
            assert len(states_before_merge) == 0
            assert len(contacts_before_merge) == 0

            self.store.merge_platforms([platform_2.platform_id], platform.platform_id)

            # There should be two sensors now, and new sensor should have two States and two Contacts
            sensors_after_merge = (
                self.store.session.query(Sensor).filter(Sensor.host == platform.platform_id).all()
            )
            states_after_merge = (
                self.store.session.query(State).filter(State.sensor_id == sensor_2.sensor_id).all()
            )
            contacts_after_merge = (
                self.store.session.query(State).filter(State.sensor_id == sensor_2.sensor_id).all()
            )
            assert len(sensors_after_merge) == 2
            assert len(states_after_merge) == 2
            assert len(contacts_after_merge) == 2

            # Assert that sensor_2 moved to Platform
            assert sensors_after_merge[1] == sensor_2

    def test_merge_platforms_with_only_comments(self):
        """Create three platforms, each platform will have a sensor named TEST-SENSOR.
        Check whether measurements moved to target platform"""
        Comment = self.store.db_classes.Comment
        with self.store.session_scope():
            platform = self.store.get_platform(
                platform_name="Test Platform",
                nationality=self.nationality,
                platform_type=self.platform_type,
                privacy=self.privacy,
                change_id=self.change_id,
            )
            platform_2 = self.store.get_platform(
                platform_name="Test Platform 2",
                nationality=self.nationality,
                platform_type=self.platform_type,
                privacy=self.privacy,
                change_id=self.change_id,
            )
            platform_3 = self.store.get_platform(
                platform_name="Test Platform 3",
                nationality=self.nationality,
                platform_type=self.platform_type,
                privacy=self.privacy,
                change_id=self.change_id,
            )
            self.file.create_comment(
                self.store,
                platform_2,
                self.current_time,
                "Comment from Platform-2",
                self.comment_type,
                parser_name=self.parser_name,
            )
            self.file.create_comment(
                self.store,
                platform_3,
                self.current_time,
                "Comment from Platform-3",
                self.comment_type,
                parser_name=self.parser_name,
            )
            if self.file.validate():
                self.file.commit(self.store, self.change_id)

            # Assert that target platform doesn't have any Comments
            comments_before_merge = (
                self.store.session.query(Comment)
                .filter(Comment.platform_id == platform.platform_id)
                .all()
            )
            assert len(comments_before_merge) == 0
            # Assert that Platform 2 and Platform 3 have one Comment object
            comments_before_merge = (
                self.store.session.query(Comment)
                .filter(Comment.platform_id == platform_2.platform_id)
                .all()
            )
            assert len(comments_before_merge) == 1
            comments_before_merge = (
                self.store.session.query(Comment)
                .filter(Comment.platform_id == platform_3.platform_id)
                .all()
            )
            assert len(comments_before_merge) == 1

            self.store.merge_platforms(
                [platform_2.platform_id, platform_3.platform_id], platform.platform_id
            )

            # There should be two Comments in the target platform
            comments_after_merge = (
                self.store.session.query(Comment)
                .filter(Comment.platform_id == platform.platform_id)
                .all()
            )
            assert len(comments_after_merge) == 2
            # Assert that Platform 2 and Platform 3 don't have Comment objects
            comments_after_merge = (
                self.store.session.query(Comment)
                .filter(Comment.platform_id == platform_2.platform_id)
                .all()
            )
            assert len(comments_after_merge) == 0
            comments_after_merge = (
                self.store.session.query(Comment)
                .filter(Comment.platform_id == platform_3.platform_id)
                .all()
            )
            assert len(comments_after_merge) == 0

    def test_merge_platforms_invalid_master_platform(self):
        uuid = UUID("12345678123456781234567812345678")
        with self.store.session_scope(), pytest.raises(ValueError) as error:
            self.store.merge_platforms([], uuid)
        assert f"No platform found with the given master_id: '{uuid}'" in error.value.args[0]

    def test_merge_platforms_with_platform_objects_given(self):
        State = self.store.db_classes.State
        Sensor = self.store.db_classes.Sensor
        Comment = self.store.db_classes.Comment
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
            ).sensor_id

            platform_2 = self.store.get_platform(
                platform_name="Test Platform 2",
                nationality=self.nationality,
                platform_type=self.platform_type,
                privacy=self.privacy,
                change_id=self.change_id,
            )
            platform_3 = self.store.get_platform(
                platform_name="Test Platform 3",
                nationality=self.nationality,
                platform_type=self.platform_type,
                privacy=self.privacy,
                change_id=self.change_id,
            )
            sensor_2 = platform_2.get_sensor(
                self.store, "gps_2", self.sensor_type, change_id=self.change_id
            )
            self.file.create_state(
                self.store,
                platform_2,
                sensor_2,
                self.current_time,
                parser_name=self.parser_name,
            )
            self.file.create_state(
                self.store,
                platform_2,
                sensor_2,
                self.current_time,
                parser_name=self.parser_name,
            )
            self.file.create_contact(
                self.store,
                platform_2,
                sensor_2,
                self.current_time,
                parser_name=self.parser_name,
            )
            self.file.create_contact(
                self.store,
                platform_2,
                sensor_2,
                self.current_time,
                parser_name=self.parser_name,
            )
            self.file.create_comment(
                self.store,
                platform_3,
                self.current_time,
                "Comment from Platform-3",
                self.comment_type,
                parser_name=self.parser_name,
            )
            if self.file.validate():
                self.file.commit(self.store, self.change_id)

            # Assert that target platform doesn't have any states or contacts
            sensors_before_merge = (
                self.store.session.query(Sensor).filter(Sensor.host == platform.platform_id).all()
            )
            states_before_merge = (
                self.store.session.query(State).filter(State.sensor_id == sensor).all()
            )
            contacts_before_merge = (
                self.store.session.query(State).filter(State.sensor_id == sensor).all()
            )
            comments_before_merge = (
                self.store.session.query(Comment)
                .filter(Comment.platform_id == platform.platform_id)
                .all()
            )
            assert len(sensors_before_merge) == 1
            assert len(states_before_merge) == 0
            assert len(contacts_before_merge) == 0
            assert len(comments_before_merge) == 0

            # Give platform objects
            self.store.merge_platforms([platform_2, platform_3], platform)

            # There should be two sensors now, and new sensor should have two States and two Contacts
            sensors_after_merge = (
                self.store.session.query(Sensor).filter(Sensor.host == platform.platform_id).all()
            )
            states_after_merge = (
                self.store.session.query(State).filter(State.sensor_id == sensor_2.sensor_id).all()
            )
            contacts_after_merge = (
                self.store.session.query(State).filter(State.sensor_id == sensor_2.sensor_id).all()
            )
            comments_after_merge = (
                self.store.session.query(Comment)
                .filter(Comment.platform_id == platform.platform_id)
                .all()
            )
            assert len(sensors_after_merge) == 2
            assert len(states_after_merge) == 2
            assert len(contacts_after_merge) == 2
            assert len(comments_after_merge) == 1

            # Assert that sensor_2 moved to Platform
            assert sensors_after_merge[1] == sensor_2


class UpdatePlatformIDsTestCase(TestCase):
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
                nationality=self.nationality,
                platform_type=self.platform_type,
                privacy=self.privacy.name,
                change_id=self.change_id,
            )

            self.store.session.expunge(self.file)
            self.store.session.expunge(self.comment_type)
            self.store.session.expunge(self.platform)
            self.store.session.expunge(self.platform_2)

    def test_update_platform_ids(self):
        Comment = self.store.db_classes.Comment
        Participant = self.store.db_classes.Participant
        LogsHolding = self.store.db_classes.LogsHolding
        Geometry1 = self.store.db_classes.Geometry1
        Media = self.store.db_classes.Media

        # Create one object in each table using Platform 2
        with self.store.session_scope():
            self.file.create_comment(
                self.store,
                self.platform_2,
                self.current_time,
                "Comment from Platform-2",
                self.comment_type,
                parser_name=self.parser_name,
            )
            if self.file.validate():
                self.file.commit(self.store, self.change_id)
            task = self.store.db_classes.Task(
                name="TEST Task",
                start=self.current_time,
                end=self.current_time,
                privacy_id=self.privacy_id,
            )
            commodity = self.store.db_classes.CommodityType(name="Test Commodity")
            unit_type = self.store.db_classes.UnitType(name="Test Unit")
            geo_type = self.store.db_classes.GeometryType(name="Test GeoType")
            media_type = self.store.db_classes.MediaType(name="Test Media")
            self.store.session.add_all(
                [
                    task,
                    commodity,
                    unit_type,
                    geo_type,
                    media_type,
                ]
            )
            self.store.session.flush()

            participant = Participant(
                platform_id=self.platform_2.platform_id,
                task_id=task.task_id,
                privacy_id=self.privacy_id,
            )
            logs_holding = LogsHolding(
                time=self.current_time,
                commodity_id=commodity.commodity_type_id,
                quantity=1.0,
                unit_type_id=unit_type.unit_type_id,
                platform_id=self.platform_2.platform_id,
                comment="TEXT",
                source_id=self.file.datafile_id,
            )
            geo_sub_type = self.store.db_classes.GeometrySubType(
                name="Test GeoSubType", parent=geo_type.geo_type_id
            )
            self.store.session.add(geo_sub_type)
            self.store.session.flush()
            geometry = Geometry1(
                subject_platform_id=self.platform_2.platform_id,
                _geometry=WKTElement("POINT(123456 123456)", srid=4326),
                geo_type_id=geo_type.geo_type_id,
                geo_sub_type_id=geo_sub_type.geo_sub_type_id,
                source_id=self.file.datafile_id,
            )
            geometry_2 = Geometry1(
                sensor_platform_id=self.platform_2.platform_id,
                _geometry=WKTElement("POINT(123456 123456)", srid=4326),
                geo_type_id=geo_type.geo_type_id,
                geo_sub_type_id=geo_sub_type.geo_sub_type_id,
                source_id=self.file.datafile_id,
            )
            media = Media(
                platform_id=self.platform_2.platform_id,
                media_type_id=media_type.media_type_id,
                url="http://123456789",
                source_id=self.file.datafile_id,
                _location=WKTElement("POINT(123456 123456)", srid=4326),
                _elevation=1.0,
                sensor_id=self.sensor,
            )
            media_2 = Media(
                subject_id=self.platform_2.platform_id,
                media_type_id=media_type.media_type_id,
                url="http://123",
                source_id=self.file.datafile_id,
                _location=WKTElement("POINT(123456 123456)", srid=4326),
                _elevation=1.0,
                sensor_id=self.sensor,
            )
            self.store.session.add_all(
                [
                    participant,
                    logs_holding,
                    geometry,
                    geometry_2,
                    media,
                    media_2,
                ]
            )
            self.store.session.flush()

            comments_before_update = (
                self.store.session.query(Comment)
                .filter(Comment.platform_id == self.platform.platform_id)
                .all()
            )
            participants_before_update = (
                self.store.session.query(Participant)
                .filter(Participant.platform_id == self.platform.platform_id)
                .all()
            )
            logs_holdings_before_update = (
                self.store.session.query(LogsHolding)
                .filter(LogsHolding.platform_id == self.platform.platform_id)
                .all()
            )
            geometry_before_update = (
                self.store.session.query(Geometry1)
                .filter(
                    or_(
                        Geometry1.subject_platform_id == self.platform.platform_id,
                        Geometry1.sensor_platform_id == self.platform.platform_id,
                    )
                )
                .all()
            )
            media_before_update = (
                self.store.session.query(Media)
                .filter(
                    or_(
                        Media.platform_id == self.platform.platform_id,
                        Media.subject_id == self.platform.platform_id,
                    )
                )
                .all()
            )
            assert len(comments_before_update) == 0
            assert len(participants_before_update) == 0
            assert len(logs_holdings_before_update) == 0
            assert len(geometry_before_update) == 0
            assert len(media_before_update) == 0

        # Update platform of objects
        with self.store.session_scope():
            self.store.update_platform_ids(self.platform_2.platform_id, self.platform.platform_id)

            comments_after_update = (
                self.store.session.query(Comment)
                .filter(Comment.platform_id == self.platform.platform_id)
                .all()
            )
            participants_after_update = (
                self.store.session.query(Participant)
                .filter(Participant.platform_id == self.platform.platform_id)
                .all()
            )
            logs_holdings_after_update = (
                self.store.session.query(LogsHolding)
                .filter(LogsHolding.platform_id == self.platform.platform_id)
                .all()
            )
            geometry_after_update = (
                self.store.session.query(Geometry1)
                .filter(
                    or_(
                        Geometry1.subject_platform_id == self.platform.platform_id,
                        Geometry1.sensor_platform_id == self.platform.platform_id,
                    )
                )
                .all()
            )
            media_after_update = (
                self.store.session.query(Media)
                .filter(
                    or_(
                        Media.platform_id == self.platform.platform_id,
                        Media.subject_id == self.platform.platform_id,
                    )
                )
                .all()
            )
            assert len(comments_after_update) == 1
            assert len(participants_after_update) == 1
            assert len(logs_holdings_after_update) == 1
            assert len(geometry_after_update) == 2
            assert len(media_after_update) == 2
