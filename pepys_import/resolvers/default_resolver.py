from .data_resolver import DataResolver


class DefaultResolver(DataResolver):
    # Hardcoded default values
    default_platform_type = "Warship"
    default_nationality = "UK"
    default_sensor_type = "Position"
    default_privacy = "PRIVACY-1"
    default_datafile_type = "DATAFILE-TYPE-1"

    def resolve_platform(
        self, data_store, platform_name, platform_type, nationality, privacy
    ):
        # needs to establish defaults for platform_type, nationality
        if not platform_type:
            platform_type = self.default_platform_type
            platform_type = data_store.search_platform_type(platform_type)
            if not platform_type:
                platform_type = data_store.add_to_platform_types(
                    self.default_platform_type
                )

        if not nationality:
            nationality = self.default_nationality
            nationality = data_store.search_nationality(nationality)
            if not nationality:
                nationality = data_store.add_to_nationalities(self.default_nationality)

        if not privacy:
            privacy = self.default_privacy
            privacy = data_store.search_privacy(privacy)
            if not privacy:
                privacy = data_store.add_to_privacies(self.default_privacy)

        return platform_name, platform_type, nationality, privacy

    def resolve_sensor(self, data_store, sensor_name):
        # needs to establish defaults for sensorType

        sensor_type = data_store.search_sensor_type(self.default_sensor_type)
        if not sensor_type:
            sensor_type = data_store.add_to_sensor_types(self.default_sensor_type)

        return sensor_name, sensor_type

    def resolve_privacy(self, data_store, table_name):
        # needs to establish defaults for privacy

        privacy = data_store.search_privacy(self.default_privacy)
        if not privacy:
            privacy = data_store.add_to_privacies(self.default_privacy)

        return privacy
