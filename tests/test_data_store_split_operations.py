from datetime import datetime, timedelta
from unittest import TestCase

from geoalchemy2 import WKTElement
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

    def test_split_platform_with_sensors(self):
        Platform = self.store.db_classes.Platform
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
            assert len(dependent_objects_before_merge) == 2  # 2 Sensors
            assert sensor.host == platform.platform_id
            assert sensor_2.host == platform.platform_id

            self.store.split_platform(platform.platform_id)

            # There should be 2 platforms, per each datafile
            platforms_after_merge = (
                self.store.session.query(Platform).filter(Platform.name == platform.name).all()
            )
            assert len(platforms_after_merge) == 2
            for p in platforms_after_merge:
                dependent_objects_after_merge = list(dependent_objects(p))
                assert len(dependent_objects_after_merge) == 1  # 1 Sensor

                if sensor.host == p.platform_id:  # first datafile
                    assert sensor.host == p.platform_id
                else:
                    assert sensor_2.host == p.platform_id

            # Assert that split platform deleted
            assert (
                not self.store.session.query(Platform)
                .filter(Platform.platform_id == platform.platform_id)
                .scalar()
            )

    def test_split_platform_with_direct_foreign_key_relationships(self):
        Platform = self.store.db_classes.Platform
        LogsHolding = self.store.db_classes.LogsHolding
        Geometry1 = self.store.db_classes.Geometry1
        Media = self.store.db_classes.Media
        with self.store.session_scope():
            platform = self.store.get_platform(
                platform_name="Test Platform",
                nationality=self.nationality,
                platform_type=self.platform_type,
                privacy=self.privacy,
                change_id=self.change_id,
            )
            comment = self.file.create_comment(
                self.store,
                platform,
                self.current_time,
                "Comment",
                self.comment_type,
                parser_name=self.parser_name,
            )
            comment_2 = self.file_2.create_comment(
                self.store,
                platform,
                self.current_time + timedelta(seconds=10),
                "Comment from datafile-2",
                self.comment_type,
                parser_name=self.parser_name,
            )
            if self.file.validate():
                self.file.commit(self.store, self.change_id)
            if self.file_2.validate():
                self.file_2.commit(self.store, self.change_id)
            # task = self.store.db_classes.Task(
            #     name="TEST Task",
            #     start=self.current_time,
            #     end=self.current_time,
            #     privacy_id=self.privacy_id,
            # )
            commodity = self.store.db_classes.CommodityType(name="Test Commodity")
            unit_type = self.store.db_classes.UnitType(name="Test Unit")
            geo_type = self.store.db_classes.GeometryType(name="Test GeoType")
            media_type = self.store.db_classes.MediaType(name="Test Media")
            self.store.session.add_all(
                [
                    # task,
                    commodity,
                    unit_type,
                    geo_type,
                    media_type,
                ]
            )
            self.store.session.flush()

            # participant = Participant(
            #     platform_id=platform.platform_id,
            #     task_id=task.task_id,
            #     privacy_id=self.privacy_id,
            # )
            logs_holding = LogsHolding(
                time=self.current_time,
                commodity_id=commodity.commodity_type_id,
                quantity=1.0,
                unit_type_id=unit_type.unit_type_id,
                platform_id=platform.platform_id,
                comment="TEXT",
                source_id=self.file.datafile_id,
            )
            logs_holding_2 = LogsHolding(
                time=self.current_time,
                commodity_id=commodity.commodity_type_id,
                quantity=1.0,
                unit_type_id=unit_type.unit_type_id,
                platform_id=platform.platform_id,
                comment="TEXT",
                source_id=self.file_2.datafile_id,
            )
            geo_sub_type = self.store.db_classes.GeometrySubType(
                name="Test GeoSubType", parent=geo_type.geo_type_id
            )
            self.store.session.add(geo_sub_type)
            self.store.session.flush()
            geometry = Geometry1(
                subject_platform_id=platform.platform_id,
                _geometry=WKTElement("POINT(123456 123456)", srid=4326),
                geo_type_id=geo_type.geo_type_id,
                geo_sub_type_id=geo_sub_type.geo_sub_type_id,
                source_id=self.file.datafile_id,
            )
            geometry_2 = Geometry1(
                sensor_platform_id=platform.platform_id,
                _geometry=WKTElement("POINT(123456 123456)", srid=4326),
                geo_type_id=geo_type.geo_type_id,
                geo_sub_type_id=geo_sub_type.geo_sub_type_id,
                source_id=self.file_2.datafile_id,
            )
            media = Media(
                platform_id=platform.platform_id,
                media_type_id=media_type.media_type_id,
                url="http://123456789",
                source_id=self.file.datafile_id,
                _location=WKTElement("POINT(123456 123456)", srid=4326),
                _elevation=1.0,
            )
            media_2 = Media(
                subject_id=platform.platform_id,
                media_type_id=media_type.media_type_id,
                url="http://123",
                source_id=self.file_2.datafile_id,
                _location=WKTElement("POINT(123456 123456)", srid=4326),
                _elevation=1.0,
            )
            self.store.session.add_all(
                [
                    # participant,
                    logs_holding,
                    logs_holding_2,
                    geometry,
                    geometry_2,
                    media,
                    media_2,
                ]
            )
            self.store.session.flush()

            # Assert that there is only 1 platform with the given name
            platforms_before_merge = (
                self.store.session.query(Platform).filter(Platform.name == platform.name).all()
            )
            dependent_objects_before_merge = list(dependent_objects(platforms_before_merge[0]))
            assert len(platforms_before_merge) == 1
            # 2 Geometry, 2 LogsHoldings, 2 Media, 2 Comment
            assert len(dependent_objects_before_merge) == 8

            self.store.split_platform(platform.platform_id)

            # There should be 2 platforms, per each datafile
            platforms_after_merge = (
                self.store.session.query(Platform).filter(Platform.name == platform.name).all()
            )
            assert len(platforms_after_merge) == 2
            for p in platforms_after_merge:
                dependent_objects_after_merge = list(dependent_objects(p))
                # 1 Geometry, 1 LogsHoldings, 1 Media, 1 Comment
                assert len(dependent_objects_after_merge) == 4

                if comment.platform_id == p.platform_id:  # first datafile
                    comment.platform_id = p.platform_id
                    logs_holding.platform_id = p.platform_id
                    media.platform_id = p.platform_id
                    geometry.subject_platform_id = p.platform_id
                else:
                    comment_2.platform_id = p.platform_id
                    logs_holding_2.platform_id = p.platform_id
                    media_2.subject_id = p.platform_id
                    geometry_2.sensor_platform_id = p.platform_id

            # Assert that split platform deleted
            assert (
                not self.store.session.query(Platform)
                .filter(Platform.platform_id == platform.platform_id)
                .scalar()
            )
