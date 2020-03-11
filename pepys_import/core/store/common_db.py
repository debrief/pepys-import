class SensorMixin:
    @classmethod
    def find_sensor(cls, data_store, sensor_name, platform_id):
        """
        This method tries to find a Sensor entity with the given sensor_name. If it
        finds, it returns the entity. If it is not found, it searches synonyms.

        :param data_store: A :class:`DataStore` object
        :type data_store: DataStore
        :param sensor_name: Name of :class:`Sensor`
        :type sensor_name: String
        :param platform_id:  Primary key of the Platform that Sensor belongs to
        :type platform_id: int
        :return:
        """
        sensor = (
            data_store.session.query(data_store.db_classes.Sensor)
            .filter(data_store.db_classes.Sensor.name == sensor_name)
            .filter(data_store.db_classes.Sensor.host == platform_id)
            .first()
        )
        if sensor:
            return sensor

        # Sensor is not found, try to find a synonym
        return data_store.synonym_search(
            name=sensor_name,
            table=data_store.db_classes.Sensor,
            pk_field=data_store.db_classes.Sensor.sensor_id,
        )

    @classmethod
    def add_to_sensors(cls, data_store, name, sensor_type, host):
        session = data_store.session
        sensor_type = data_store.db_classes.SensorType().search_sensor_type(
            session, sensor_type
        )
        host = data_store.db_classes.Platform().search_platform(session, host)

        sensor_obj = data_store.db_classes.Sensor(
            name=name, sensor_type_id=sensor_type.sensor_type_id, host=host.platform_id,
        )
        session.add(sensor_obj)
        session.flush()

        return sensor_obj
