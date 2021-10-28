from abc import ABC, abstractmethod


class DataResolver(ABC):
    @abstractmethod
    def resolve_platform(
        self,
        data_store,
        platform_name,
        identifier,
        platform_type,
        nationality,
        privacy,
        change_id,
        quadgraph=None,
    ):
        """
        Implementation method should return any data necessary to create a platform.
        Currently: platform_name, platform_type, nationality, privacy.

        :param data_store: A :class:`DataStore` object
        :type data_store: DataStore
        :param platform_name: Name of :class:`Platform`
        :type platform_name: String
        :param nationality: Name of :class:`Nationality`
        :type nationality: String
        :param platform_type: Name of :class:`PlatformType`
        :type platform_type: String
        :param privacy: Name of :class:`Privacy`
        :type privacy: String
        :param change_id: ID of the :class:`Change` object
        :type change_id: UUID
        :param quadgraph: The quadgraph that the platform is known by
        :type quadgraph: String
        :return:
        """

    @abstractmethod
    def resolve_sensor(self, data_store, sensor_name, sensor_type, host_id, privacy, change_id):
        """
        Implementation method should return any data necessary to create a sensor.
        Currently: sensor_name, sensor_type.

        :param data_store: A :class:`DataStore` object
        :type data_store: DataStore
        :param sensor_name: Name of :class:`Sensor`
        :type sensor_name: String
        :param sensor_type: Type of :class:`Sensor`
        :type sensor_type: String
        :param host_id: Host Platform's UUID
        :type host_id: UUID
        :param privacy: Name of :class:`Privacy`
        :type privacy: String
        :param change_id: ID of the :class:`Change` object
        :type change_id: UUID
        :return:
        """

    @abstractmethod
    def resolve_datafile(self, data_store, datafile_name, datafile_type, privacy, change_id):
        """
        Implementation method should return any data necessary to create a datafile.
        Currently: datafile_type, privacy

        :param data_store: A :class:`DataStore` object
        :type data_store: DataStore
        :param datafile_name:  Name of :class`Datafile`
        :type datafile_name: String
        :param datafile_type: Type of :class`Datafile`
        :type datafile_type: String
        :param privacy: Name of :class:`Privacy`
        :type privacy: String
        :param change_id: ID of the :class:`Change` object
        :type change_id: UUID
        :return:
        """

    @abstractmethod
    def resolve_missing_info(self, question, default_value):
        """Implementation method should return the data for the given property name
        as asked for in the question

        :param property_name: The name of the property asked for
        :param question: The question to resolve
        :param default_value: The default value to use if unresolved
        :return: The missing information requested
        """
