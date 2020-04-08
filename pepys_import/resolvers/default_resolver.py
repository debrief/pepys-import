from .data_resolver import DataResolver


class DefaultResolver(DataResolver):
    # Hardcoded default values
    default_platform_name = "PLATFORM-1"
    default_trigraph = "PL1"
    default_quadgraph = "PLT1"
    default_pennant_number = "123"
    default_platform_type = "Warship"
    default_nationality = "UK"
    default_sensor_name = "SENSOR-1"
    default_sensor_type = "Position"
    default_privacy = "PRIVACY-1"
    default_datafile_name = "DATAFILE-1"
    default_datafile_type = "DATAFILE-TYPE-1"

    def resolve_platform(
        self, data_store, platform_name, platform_type, nationality, privacy, change_id
    ):
        # needs to establish defaults for platform_name, platform_type, nationality and privacy
        if not platform_name:
            platform_name = self.default_platform_name

        if platform_type:
            platform_type = data_store.add_to_platform_types(platform_type, change_id)
        else:
            platform_type = data_store.add_to_platform_types(self.default_platform_type, change_id)

        if nationality:
            nationality = data_store.add_to_nationalities(nationality, change_id)
        else:
            nationality = data_store.add_to_nationalities(self.default_nationality, change_id)

        if privacy:
            privacy = data_store.add_to_privacies(privacy, change_id)
        else:
            privacy = data_store.add_to_privacies(self.default_privacy, change_id)
        return (
            platform_name,
            self.default_trigraph,
            self.default_quadgraph,
            self.default_pennant_number,
            platform_type,
            nationality,
            privacy,
        )

    def resolve_sensor(self, data_store, sensor_name, sensor_type, privacy, change_id):

        # needs to establish defaults for sensor name, sensor type, and privacy
        if not sensor_name:
            sensor_name = self.default_sensor_name

        if sensor_type:
            sensor_type = data_store.add_to_sensor_types(sensor_type, change_id)
        else:
            sensor_type = data_store.add_to_sensor_types(self.default_sensor_type, change_id)

        if privacy:
            privacy = data_store.add_to_privacies(privacy, change_id)
        else:
            privacy = data_store.add_to_privacies(self.default_privacy, change_id)

        return sensor_name, sensor_type, privacy

    def resolve_privacy(self, data_store, change_id, data_type=None):
        # needs to establish defaults for privacy
        privacy = data_store.search_privacy(self.default_privacy)
        if not privacy:
            privacy = data_store.add_to_privacies(self.default_privacy, change_id)

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
            privacy = data_store.add_to_privacies(privacy, change_id)
        else:
            privacy = data_store.add_to_privacies(self.default_privacy, change_id)

        return datafile_name, datafile_type, privacy
