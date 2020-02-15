from abc import ABC, abstractmethod


class DataResolver(ABC):
    @abstractmethod
    def resolve_platform(
        self, data_store, platform_name, platform_type_str, nationality_str, privacy_str
    ):
        # Implementation method should return any data necessary to create a
        # platform
        # Currently: platformName, platformType, nationality. Probably
        # hostPlatform when that is needed
        pass

    @abstractmethod
    def resolve_sensor(self, data_store, sensor_name):
        # Implementation method should return any data necessary to create a
        # sensor
        # Currently: sensorName, sensorType
        pass

    @abstractmethod
    def resolve_privacy(self, data_store, table_type_id, table_name):
        # Implementation method should return any data necessary to create a
        # privacy
        # Currently: tabletypeId, privacyName
        pass
