from .data_resolver import DataResolver


class DefaultResolver(DataResolver):
    # Hardcoded default values
    default_platform_type = "Warship"
    default_nationality = "UK"
    default_sensor_type = "Position"
    default_privacy = "Private"

    def resolve_platform(self, data_store, platformName):
        # needs to establish defaults for platform_type, nationality

        platform_type = data_store.search_platform_type(self.default_platform_type)
        if not platform_type:
            platform_type = data_store.add_to_platform_types(self.default_platform_type)

        nationality = data_store.search_nationality(self.default_nationality)
        if not nationality:
            nationality = data_store.add_to_nationalities(self.default_nationality)

        return platformName, platform_type, nationality

    def resolve_sensor(self, data_store, sensorName):
        # needs to establish defaults for sensorType

        sensor_type = data_store.search_sensor_type(self.default_sensor_type)
        if not sensor_type:
            sensor_type = data_store.add_to_sensor_types(self.default_sensor_type)

        return sensorName, sensor_type

    def resolve_privacy(self, data_store, table_type_id, table_name):
        # needs to establish defaults for privacy

        privacy = data_store.search_privacy(self.default_privacy)
        if not privacy:
            privacy = data_store.add_to_privacies(self.default_privacy)

        return table_type_id, privacy
