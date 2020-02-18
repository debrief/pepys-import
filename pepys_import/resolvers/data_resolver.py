from abc import ABC, abstractmethod


class DataResolver(ABC):
    @abstractmethod
    def resolve_platform(
        self, data_store, platform_name, platform_type, nationality, privacy
    ):
        """
        Implementation method should return any data necessary to create a platform.
        Currently: platform_name, platform_type, nationality.
        Probably host when that is needed
        """

    @abstractmethod
    def resolve_sensor(self, data_store, sensor_name, privacy):
        """
        Implementation method should return any data necessary to create a sensor.
        Currently: sensor_name, sensor_type
        """

    @abstractmethod
    def resolve_privacy(self, data_store):
        """
        Implementation method should return any data necessary to create a privacy.
        Currently: privacy_name
        """
