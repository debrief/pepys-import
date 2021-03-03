from datetime import datetime, timedelta
from unittest import TestCase

from pepys_import.core.store import constants
from pepys_import.core.store.data_store import DataStore


class FindDependentObjectsTestCase(TestCase):
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
            self.file = self.store.get_datafile(
                "test_file", "csv", 0, "HASHED", self.change_id, self.privacy
            )
            self.file_id = self.file.datafile_id
            self.file.measurements[self.parser_name] = dict()
            self.file_2 = self.store.get_datafile(
                "test_file_2", "csv", 100, "HASHED", self.change_id, self.privacy
            )
            self.file_2_id = self.file_2.datafile_id
            self.platform = self.store.get_platform(
                platform_name="Test Platform",
                nationality=self.nationality,
                platform_type=self.platform_type,
                privacy=self.privacy,
                change_id=self.change_id,
            )
            self.platform_id = self.platform.platform_id
            self.sensor = self.platform.get_sensor(
                self.store, "gps", self.sensor_type, change_id=self.change_id, privacy=self.privacy
            )
            self.sensor_id = self.sensor.sensor_id
            self.state = self.file.create_state(
                self.store,
                self.platform,
                self.sensor,
                self.current_time,
                parser_name=self.parser_name,
            )
            self.state_2 = self.file.create_state(
                self.store,
                self.platform,
                self.sensor,
                self.current_time + timedelta(seconds=5),
                parser_name=self.parser_name,
            )
            if self.file.validate():
                self.file.commit(self.store, self.change_id)

    def test_find_dependent_objects_privacy(self):
        with self.store.session_scope():
            result = self.store.find_dependent_objects(constants.PRIVACY, [self.privacy_id])
            assert "Privacies" in result and result["Privacies"] == 1  # self.privacy
            assert "Datafiles" in result and result["Datafiles"] == 2  # self.file and self.file_2
            assert "Platforms" in result and result["Platforms"] == 1  # self.platform
            assert "Sensors" in result and result["Sensors"] == 1  # self.sensor
            assert "States" in result and result["States"] == 2  # self.state and self.state_2

    def test_find_dependent_objects_platform(self):
        with self.store.session_scope():
            result = self.store.find_dependent_objects(constants.PLATFORM, [self.platform_id])
            assert "Platforms" in result and result["Platforms"] == 1  # self.platform
            assert "Sensors" in result and result["Sensors"] == 1  # self.sensor
            assert "States" in result and result["States"] == 2  # self.state and self.state_2

    def test_find_dependent_objects_sensor(self):
        with self.store.session_scope():
            result = self.store.find_dependent_objects(constants.SENSOR, [self.sensor_id])
            assert "Sensors" in result and result["Sensors"] == 1  # self.sensor
            assert "States" in result and result["States"] == 2  # self.state and self.state_2

    def test_find_dependent_objects_datafile(self):
        with self.store.session_scope():
            result = self.store.find_dependent_objects(constants.DATAFILE, [self.file_id])
            assert "Datafiles" in result and result["Datafiles"] == 1  # self.file
            assert "States" in result and result["States"] == 2  # self.state and self.state_2

        with self.store.session_scope():
            result = self.store.find_dependent_objects(constants.DATAFILE, [self.file_2_id])
            assert "Datafiles" in result and result["Datafiles"] == 1  # self.file_2
            assert "States" not in result


class DeleteObjectsTestCase(TestCase):
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
            self.file = self.store.get_datafile(
                "test_file", "csv", 0, "HASHED", self.change_id, self.privacy
            )
            self.file_id = self.file.datafile_id
            self.file.measurements[self.parser_name] = dict()
            self.file_2 = self.store.get_datafile(
                "test_file_2", "csv", 100, "HASHED", self.change_id, self.privacy
            )
            self.file_2_id = self.file_2.datafile_id
            self.platform = self.store.get_platform(
                platform_name="Test Platform",
                nationality=self.nationality,
                platform_type=self.platform_type,
                privacy=self.privacy,
                change_id=self.change_id,
            )
            self.platform_id = self.platform.platform_id
            self.sensor = self.platform.get_sensor(
                self.store, "gps", self.sensor_type, change_id=self.change_id, privacy=self.privacy
            )
            self.sensor_id = self.sensor.sensor_id
            self.state = self.file.create_state(
                self.store,
                self.platform,
                self.sensor,
                self.current_time,
                parser_name=self.parser_name,
            )
            self.state_2 = self.file.create_state(
                self.store,
                self.platform,
                self.sensor,
                self.current_time + timedelta(seconds=5),
                parser_name=self.parser_name,
            )
            if self.file.validate():
                self.file.commit(self.store, self.change_id)

    def test_delete_objects_privacy(self):
        Privacy = self.store.db_classes.Privacy
        with self.store.session_scope():
            result = self.store.find_dependent_objects(constants.PRIVACY, [self.privacy_id])
            assert "Privacies" in result and result["Privacies"] == 1  # self.privacy
            assert "Datafiles" in result and result["Datafiles"] == 2  # self.file and self.file_2
            assert "Platforms" in result and result["Platforms"] == 1  # self.platform
            assert "Sensors" in result and result["Sensors"] == 1  # self.sensor
            assert "States" in result and result["States"] == 2  # self.state and self.state_2

            self.store.delete_objects(constants.PRIVACY, [self.privacy_id])
            result = self.store.find_dependent_objects(constants.PRIVACY, [self.privacy_id])
            assert result == {}
            assert (
                not self.store.session.query(Privacy)
                .filter(Privacy.privacy_id == self.privacy_id)
                .scalar()
            )

    def test_delete_objects_platform(self):
        Platform = self.store.db_classes.Platform
        with self.store.session_scope():
            result = self.store.find_dependent_objects(constants.PLATFORM, [self.platform_id])
            assert "Platforms" in result and result["Platforms"] == 1  # self.platform
            assert "Sensors" in result and result["Sensors"] == 1  # self.sensor
            assert "States" in result and result["States"] == 2  # self.state and self.state_2

            self.store.delete_objects(constants.PLATFORM, [self.platform_id])
            result = self.store.find_dependent_objects(constants.PLATFORM, [self.platform_id])
            assert result == {}
            assert (
                not self.store.session.query(Platform)
                .filter(Platform.platform_id == self.platform_id)
                .scalar()
            )

    def test_delete_objects_sensor(self):
        Sensor = self.store.db_classes.Sensor
        with self.store.session_scope():
            result = self.store.find_dependent_objects(constants.SENSOR, [self.sensor_id])
            assert "Sensors" in result and result["Sensors"] == 1  # self.sensor
            assert "States" in result and result["States"] == 2  # self.state and self.state_2

            self.store.delete_objects(constants.SENSOR, [self.sensor_id])
            result = self.store.find_dependent_objects(constants.SENSOR, [self.sensor_id])
            assert result == {}
            assert (
                not self.store.session.query(Sensor)
                .filter(Sensor.sensor_id == self.sensor_id)
                .scalar()
            )

    def test_delete_objects_datafile(self):
        Datafile = self.store.db_classes.Datafile
        with self.store.session_scope():
            result = self.store.find_dependent_objects(constants.DATAFILE, [self.file_id])
            assert "Datafiles" in result and result["Datafiles"] == 1  # self.file
            assert "States" in result and result["States"] == 2  # self.state and self.state_2

            self.store.delete_objects(constants.DATAFILE, [self.file_id])
            result = self.store.find_dependent_objects(constants.DATAFILE, [self.file_id])
            assert result == {}
            assert (
                not self.store.session.query(Datafile)
                .filter(Datafile.datafile_id == self.file_id)
                .scalar()
            )

        with self.store.session_scope():
            result = self.store.find_dependent_objects(constants.DATAFILE, [self.file_2_id])
            assert "Datafiles" in result and result["Datafiles"] == 1  # self.file_2
            assert "States" not in result

            self.store.delete_objects(constants.DATAFILE, [self.file_2_id])
            result = self.store.find_dependent_objects(constants.DATAFILE, [self.file_2_id])
            assert result == {}
            assert (
                not self.store.session.query(Datafile)
                .filter(Datafile.datafile_id == self.file_2_id)
                .scalar()
            )
