from abc import ABC, abstractmethod


class DataResolver(ABC):
    @abstractmethod
    def resolve_platform(
        self, data_store, platform_name, platform_type, nationality, privacy
    ):
        """
        Implementation method should return any data necessary to create a platform.
        Currently: platform_name, platform_type, nationality, privacy.

        :param data_store: A :class:`DataStore` object
        :type data_store: DataStore
        :param platform_name: Name of :class:`Platform`
        :type platform_name: String
        :param nationality: Name of :class:`Nationality`
        :type nationality: Nationality
        :param platform_type: Name of :class:`PlatformType`
        :type platform_type: PlatformType
        :param privacy: Name of :class:`Privacy`
        :type privacy: Privacy
        :return:
        """

    @abstractmethod
    def resolve_sensor(self, data_store, sensor_name, sensor_type, privacy):
        """
        Implementation method should return any data necessary to create a sensor.
        Currently: sensor_name, sensor_type.

        :param data_store: A :class:`DataStore` object
        :type data_store: DataStore
        :param sensor_name: Name of :class:`Sensor`
        :type sensor_name: String
        :param sensor_type: Type of :class:`Sensor`
        :type sensor_type: SensorType
        :param privacy: Name of :class:`Privacy`
        :type privacy: Privacy
        :return:
        """

    @abstractmethod
    def resolve_privacy(self, data_store):
        """
        Implementation method should return any data necessary to create a privacy.
        Currently: name

        :param data_store: A :class:`DataStore` object
        :type data_store: DataStore
        :return:
        """

    @abstractmethod
    def resolve_datafile(self, data_store, datafile_name, datafile_type, privacy):
        """
        Implementation method should return any data necessary to create a datafile.
        Currently: datafile_type, privacy

        :param data_store: A :class:`DataStore` object
        :type data_store: DataStore
        :param datafile_name:  Name of :class`Datafile`
        :type datafile_name: String
        :param datafile_type: Type of :class`Datafile`
        :type datafile_type: DatafileType
        :param privacy: Name of :class:`Privacy`
        :type privacy: Privacy
        :return:
        """
