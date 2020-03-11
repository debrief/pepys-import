from pepys_import.core.validators import constants as validation_constants

from pepys_import.core.validators.basic_validator import BasicValidator
from pepys_import.core.validators.enhanced_validator import EnhancedValidator


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
        host = data_store.db_classes.Platform().search_platform(data_store, host)

        sensor_obj = data_store.db_classes.Sensor(
            name=name, sensor_type_id=sensor_type.sensor_type_id, host=host.platform_id,
        )
        session.add(sensor_obj)
        session.flush()

        return sensor_obj


class PlatformMixin:
    @classmethod
    def search_platform(cls, data_store, name):
        # search for any platform with this name
        Platform = data_store.db_classes.Platform
        return data_store.session.query(Platform).filter(Platform.name == name).first()

    def get_sensor(self, data_store, sensor_name=None, sensor_type=None, privacy=None):
        """
         Lookup or create a sensor of this name for this :class:`Platform`.
         Specified sensor will be added to the :class:`Sensor` table.
         It uses find_sensor method to search existing sensors.

        :param data_store: DataStore object to to query DB and use missing data resolver
        :type data_store: DataStore
        :param sensor_name: Name of :class:`Sensor`
        :type sensor_name: String
        :param sensor_type: Type of :class:`Sensor`
        :type sensor_type: SensorType
        :param privacy: Privacy of :class:`Sensor`
        :type privacy: Privacy
        :return: Created :class:`Sensor` entity
        :rtype: Sensor
        """
        Sensor = data_store.db_classes.Sensor

        sensor = Sensor().find_sensor(data_store, sensor_name, self.platform_id)
        if sensor:
            return sensor

        if sensor_type is None or privacy is None:
            resolved_data = data_store.missing_data_resolver.resolve_sensor(
                data_store, sensor_name, sensor_type, privacy
            )
            # It means that new sensor added as a synonym and existing sensor returned
            if isinstance(resolved_data, Sensor):
                return resolved_data
            elif len(resolved_data) == 3:
                (sensor_name, sensor_type, privacy,) = resolved_data

        assert isinstance(
            sensor_type, data_store.db_classes.SensorType
        ), "Type error for Sensor Type entity"
        # TODO: we don't use privacy for sensor. Is it necessary to resolve it?
        # assert isinstance(privacy, Privacy), "Type error for Privacy entity"

        return Sensor().add_to_sensors(
            data_store=data_store,
            name=sensor_name,
            sensor_type=sensor_type.name,
            host=self.name,
        )


class DatafileMixin:
    def create_state(self, data_store, sensor, timestamp, parser_name):
        state = data_store.db_classes.State(
            sensor_id=sensor.sensor_id, time=timestamp, source_id=self.datafile_id
        )
        self.measurements[parser_name].append(state)
        return state

    def create_contact(self, data_store, sensor, timestamp, parser_name):
        contact = data_store.db_classes.Contact(
            sensor_id=sensor.sensor_id, time=timestamp, source_id=self.datafile_id
        )
        self.measurements[parser_name].append(contact)
        return contact

    def create_comment(
        self, data_store, platform_id, timestamp, comment, comment_type, parser_name
    ):
        comment = data_store.db_classes.Comment(
            platform_id=platform_id,
            time=timestamp,
            content=comment,
            comment_type_id=comment_type.comment_type_id,
            source_id=self.datafile_id,
        )
        self.measurements[parser_name].append(comment)
        return comment

    def validate(
        self,
        validation_level=validation_constants.NONE_LEVEL,
        errors=None,
        parser="Default",
    ):
        # If there is no parsing error, it will return None.If that's the case, create a new list for validation errors.
        if errors is None:
            errors = list()
        assert isinstance(errors, list), "Type error for errors!"

        if validation_level == validation_constants.NONE_LEVEL:
            return True
        elif validation_level == validation_constants.BASIC_LEVEL:
            for measurement in self.measurements[parser]:
                BasicValidator(measurement, errors, parser)
            if not errors:
                return True
            return False
        elif validation_level == validation_constants.ENHANCED_LEVEL:
            for measurement in self.measurements[parser]:
                BasicValidator(measurement, errors, parser)
                # TODO: Commented out at the moment as there is a bug in the validator
                # Need to bring this back in once that is fixed.
                # EnhancedValidator(measurement, errors, parser)
            if not errors:
                return True
            return False

    def commit(self, session):
        # Since measurements are saved by their importer names, iterate over each key
        # and save its measurement objects.
        extraction_log = list()
        for key in self.measurements.keys():
            for file in self.measurements[key]:
                file.submit(session)
            extraction_log.append(
                f"{len(self.measurements[key])} measurement objects parsed by {key}."
            )
        return extraction_log


class SensorTypeMixin:
    @classmethod
    def search_sensor_type(cls, data_store, name):
        # search for any sensor type featuring this name
        return (
            data_store.session.query(data_store.db_classes.SensorType)
            .filter(data_store.db_classes.SensorType.name == name)
            .first()
        )
