from abc import ABC, abstractmethod


class DataResolver(ABC):
    @abstractmethod
    def resolve_platform(
        self, data_store, platform_name, platform_type, nationality, privacy
    ):
        """
        Implementation method should return any data necessary to create a platform.
        Currently: platform_name, platform_type, nationality, privacy.

        :param data_store:
        :param platform_name:
        :param platform_type:
        :param nationality:
        :param privacy:
        :return:
        """

    @abstractmethod
    def resolve_sensor(self, data_store, sensor_name, sensor_type, privacy):
        """
        Implementation method should return any data necessary to create a sensor.
        Currently: sensor_name, sensor_type.

        :param data_store:
        :param sensor_name:
        :param sensor_type:
        :param privacy:
        :return:
        """

    @abstractmethod
    def resolve_privacy(self, data_store):
        """
        Implementation method should return any data necessary to create a privacy.
        Currently: name

        :param data_store:
        :return:
        """

    @abstractmethod
    def resolve_datafile(self, data_store, datafile_type, privacy):
        """
        Implementation method should return any data necessary to create a datafile.
        Currently: datafile_type, privacy
        :param data_store:
        :param datafile_type:
        :param privacy:
        :return:
        """
