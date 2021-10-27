from .data_resolver import DataResolver


class DefaultResolver(DataResolver):
    # Hardcoded default values
    default_platform_name = "PLATFORM-1"
    default_trigraph = "PL1"
    default_quadgraph = "PLT1"
    default_identifier = "123"
    default_platform_type = "Warship"
    default_nationality = "UK"
    default_sensor_name = "SENSOR-1"
    default_sensor_type = "Position"
    default_privacy = "Public"
    default_privacy_level = 10
    default_datafile_name = "DATAFILE-1"
    default_datafile_type = "DATAFILE-TYPE-1"

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
        # needs to establish defaults for platform_name, platform_type, nationality and privacy
        if quadgraph and not platform_name:
            platform_name = f"PLATFORM-{quadgraph}"
        elif not platform_name:
            platform_name = self.default_platform_name

        if not identifier:
            identifier = self.default_identifier

        if platform_type:
            platform_type = data_store.add_to_platform_types(platform_type, change_id)
        else:
            platform_type = data_store.add_to_platform_types(self.default_platform_type, change_id)

        if nationality:
            nationality = data_store.add_to_nationalities(nationality, change_id)
        else:
            nationality = data_store.add_to_nationalities(self.default_nationality, change_id)

        if privacy:
            privacy = data_store.add_to_privacies(privacy, self.default_privacy_level, change_id)
        else:
            privacy = data_store.add_to_privacies(
                self.default_privacy, self.default_privacy_level, change_id
            )

        # Look to see if we already have a platform created with these details, and if so, return it
        results_from_db = (
            data_store.session.query(data_store.db_classes.Platform)
            .filter(data_store.db_classes.Platform.name == platform_name)
            .filter(data_store.db_classes.Platform.identifier == identifier)
            .filter(data_store.db_classes.Platform.nationality_id == nationality.nationality_id)
            .all()
        )

        if len(results_from_db) == 0:
            # Nothing in DB already, so return details to create new entry
            return (
                platform_name,
                self.default_trigraph,
                quadgraph if quadgraph is not None else self.default_quadgraph,
                identifier,
                platform_type,
                nationality,
                privacy,
            )
        elif len(results_from_db) == 1:
            # One platform matching these criteria, so return it
            return results_from_db[0]
        else:
            # Should never reach here - there should only be one platform object with a specific name
            # for a specific nationality, platform type etc
            assert False  # pragma: no cover

    def resolve_sensor(self, data_store, sensor_name, sensor_type, host_id, privacy, change_id):
        # If we aren't given a sensor name, then use a default sensor name
        if not sensor_name:
            sensor_name = self.default_sensor_name

        if sensor_type:
            sensor_type = data_store.add_to_sensor_types(sensor_type, change_id)
        else:
            sensor_type = data_store.add_to_sensor_types(self.default_sensor_type, change_id)

        if privacy:
            privacy = data_store.add_to_privacies(privacy, self.default_privacy_level, change_id)
        else:
            privacy = data_store.add_to_privacies(
                self.default_privacy, self.default_privacy_level, change_id
            )

        # Look to see if we already have a sensor created for this platform, with this sensor type etc

        results_from_db = (
            data_store.session.query(data_store.db_classes.Sensor)
            .filter(data_store.db_classes.Sensor.host == host_id)
            .filter(data_store.db_classes.Sensor.name == sensor_name)
            .filter(data_store.db_classes.Sensor.sensor_type_id == sensor_type.sensor_type_id)
            .all()
        )

        if len(results_from_db) == 0:
            # Nothing in DB already, so return details to create new entry
            return sensor_name, sensor_type, privacy
        elif len(results_from_db) == 1:
            # One sensor matching these criteria, so return it
            return results_from_db[0]
        else:
            # Should never reach here - there should only be one sensor object with a specific name for a
            # specific platform
            assert False  # pragma: no cover

    def resolve_privacy(self, data_store, change_id, data_type=None):
        """
        Implementation method should return any data necessary to create a privacy.
        Currently: name

        :param data_store: A :class:`DataStore` object
        :type data_store: DataStore
        :param change_id: ID of the :class:`Change` object
        :type change_id: UUID
        :param data_type: Type of the data: datafile, platform or sensor
        :type data_type: String
        :return:
        """

        # needs to establish defaults for privacy
        privacy = data_store.search_privacy(self.default_privacy)
        if not privacy:
            privacy = data_store.add_to_privacies(
                self.default_privacy, self.default_privacy_level, change_id
            )

        return privacy

    def resolve_datafile(self, data_store, datafile_name, datafile_type, privacy, change_id):
        # needs to establish defaults for datafile name, datafile type, and privacy
        if not datafile_name:
            datafile_name = self.default_datafile_name

        if datafile_type:
            datafile_type = data_store.add_to_datafile_types(datafile_type, change_id)
        else:
            datafile_type = data_store.add_to_datafile_types(self.default_datafile_type, change_id)

        if privacy:
            privacy = data_store.add_to_privacies(privacy, self.default_privacy_level, change_id)
        else:
            privacy = data_store.add_to_privacies(
                self.default_privacy, self.default_privacy_level, change_id
            )

        return datafile_name, datafile_type, privacy
