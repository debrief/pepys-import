from .data_resolver import DataResolver


class DefaultResolver(DataResolver):
    # Hardcoded default values
    default_platform_type = "Warship"
    default_nationality = "UK"
    default_sensor_type = "Position"
    default_privacy = "Private"

    def resolve_platform(self, data_store, platformName):
        # needs to establish defaults for platform_type, nationality

        platform_type = data_store.searchplatform_type(self.default_platform_type)
        if not platform_type:
            platform_type = data_store.addToPlatformsType(self.default_platform_type)

        nationality = data_store.searchNationality(self.default_nationality)
        if not nationality:
            nationality = data_store.addNationality(self.default_nationality)

        return platformName, platform_type, nationality

    def resolve_sensor(self, data_store, sensorName):
        # needs to establish defaults for sensorType

        sensor_type = data_store.searchsensor_type(self.default_sensor_type)
        if not sensor_type:
            sensor_type = data_store.addTosensor_types(self.default_sensor_type)

        return sensorName, sensor_type

    def resolve_privacy(self, data_store, table_type_id, table_name):
        # needs to establish defaults for privacy

        privacy = data_store.searchPrivacy(self.default_privacy)
        if not privacy:
            privacy = data_store.addToPrivacies(self.default_privacy)

        return table_type_id, privacy
