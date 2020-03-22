from sqlalchemy.ext.hybrid import hybrid_property

from pepys_import.core.formats import unit_registry

from config import LOCAL_BASIC_TESTS, LOCAL_ENHANCED_TESTS
from pepys_import.core.store import constants
from pepys_import.core.validators import constants as validation_constants
from pepys_import.core.validators.basic_validator import BasicValidator
from pepys_import.core.validators.enhanced_validator import EnhancedValidator
from pepys_import.utils.import_utils import import_validators

from pepys_import.core.formats.location import Location


LOCAL_BASIC_VALIDATORS = import_validators(LOCAL_BASIC_TESTS)
LOCAL_ENHANCED_VALIDATORS = import_validators(LOCAL_ENHANCED_TESTS)


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
    def add_to_sensors(cls, data_store, name, sensor_type, host, change_id):
        session = data_store.session
        sensor_type = data_store.db_classes.SensorType().search_sensor_type(
            data_store, sensor_type
        )
        host = data_store.db_classes.Platform().search_platform(data_store, host)

        sensor_obj = data_store.db_classes.Sensor(
            name=name, sensor_type_id=sensor_type.sensor_type_id, host=host.platform_id,
        )
        session.add(sensor_obj)
        session.flush()

        data_store.add_to_logs(
            table=constants.SENSOR, row_id=sensor_obj.sensor_id, change_id=change_id
        )
        return sensor_obj


class PlatformMixin:
    @classmethod
    def search_platform(cls, data_store, name):
        # search for any platform with this name
        Platform = data_store.db_classes.Platform
        return data_store.session.query(Platform).filter(Platform.name == name).first()

    def get_sensor(
        self,
        data_store,
        sensor_name=None,
        sensor_type=None,
        privacy=None,
        change_id=None,
    ):
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
        :param change_id: ID of the :class:`Change` object
        :type change_id: Integer or UUID
        :return: Created :class:`Sensor` entity
        :rtype: Sensor
        """
        Sensor = data_store.db_classes.Sensor

        sensor = Sensor().find_sensor(data_store, sensor_name, self.platform_id)
        if sensor:
            return sensor

        if sensor_type is None or privacy is None:
            resolved_data = data_store.missing_data_resolver.resolve_sensor(
                data_store, sensor_name, sensor_type, privacy, change_id
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
            change_id=change_id,
        )


class DatafileMixin:
    def create_state(self, data_store, platform, sensor, timestamp, parser_name):
        state = data_store.db_classes.State(
            sensor_id=sensor.sensor_id, time=timestamp, source_id=self.datafile_id
        )
        state.platform_name = platform.name
        state.sensor_name = sensor.name
        self.measurements[parser_name].append(state)
        return state

    def create_contact(self, data_store, platform, sensor, timestamp, parser_name):
        contact = data_store.db_classes.Contact(
            sensor_id=sensor.sensor_id, time=timestamp, source_id=self.datafile_id
        )
        contact.platform_name = platform.name
        contact.sensor_name = sensor.name
        self.measurements[parser_name].append(contact)
        return contact

    def create_comment(
        self, data_store, platform, timestamp, comment, comment_type, parser_name,
    ):
        comment = data_store.db_classes.Comment(
            platform_id=platform.platform_id,
            time=timestamp,
            content=comment,
            comment_type_id=comment_type.comment_type_id,
            source_id=self.datafile_id,
        )
        comment.platform_name = platform.name
        comment.sensor_name = "N/A"
        self.measurements[parser_name].append(comment)
        return comment

    def validate(
        self,
        validation_level=validation_constants.NONE_LEVEL,
        errors=None,
        parser="Default",
    ):
        # If there is no parsing error, it will return None. If that's the case,
        # create a new list for validation errors.
        if errors is None:
            errors = list()
        assert isinstance(errors, list), "Type error for errors!"

        if validation_level == validation_constants.NONE_LEVEL:
            return True
        elif validation_level == validation_constants.BASIC_LEVEL:
            for measurement in self.measurements[parser]:
                BasicValidator(measurement, errors, parser)
                for basic_validator in LOCAL_BASIC_VALIDATORS:
                    basic_validator(measurement, errors, parser)
            if not errors:
                return True
            return False
        elif validation_level == validation_constants.ENHANCED_LEVEL:
            for measurement in self.measurements[parser]:
                BasicValidator(measurement, errors, parser)
                for basic_validator in LOCAL_BASIC_VALIDATORS:
                    basic_validator(measurement, errors, parser)
                EnhancedValidator(measurement, errors, parser)
                for enhanced_validator in LOCAL_ENHANCED_VALIDATORS:
                    enhanced_validator(measurement, errors, parser)
            if not errors:
                return True
            return False

    def commit(self, data_store, change_id):
        # Since measurements are saved by their importer names, iterate over each key
        # and save its measurement objects.
        extraction_log = list()
        for key in self.measurements.keys():
            for file in self.measurements[key]:
                file.submit(data_store, change_id)
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


class StateMixin:
    def submit(self, data_store, change_id):
        """Submit intermediate object to the DB"""
        data_store.session.add(self)
        data_store.session.flush()
        data_store.session.expire(self, ["_location"])
        # Log new State object creation
        data_store.add_to_logs(
            table=constants.STATE, row_id=self.state_id, change_id=change_id
        )
        return self

    #
    # Speed properties
    #

    @hybrid_property
    def speed(self):
        # Return all speeds as metres per second
        if self._speed is None:
            return None
        else:
            return self._speed * (unit_registry.metre / unit_registry.second)

    @speed.setter
    def speed(self, speed):
        if speed is None:
            self._speed = None
            return

        # Check the given speed is a Quantity with a dimension of 'length / time'
        try:
            if not speed.check("[length]/[time]"):
                raise ValueError(
                    "Speed must be a Quantity with a dimensionality of [length]/[time]"
                )
        except AttributeError:
            raise TypeError("Speed must be a Quantity")

        # Set the actual speed attribute to the given value converted to metres per second
        self._speed = speed.to(unit_registry.metre / unit_registry.second).magnitude

    @speed.expression
    def speed(self):
        # We need a separate @speed.expression function to return a float rather than a
        # Quantity object, as otherwise this won't work in the SQLAlchemy filtering functions
        return self._speed

    #
    # Heading properties
    #

    @hybrid_property
    def heading(self):
        # Return all headings as degrees
        if self._heading is None:
            return None
        else:
            return (self._heading * unit_registry.radian).to(unit_registry.degree)

    @heading.setter
    def heading(self, heading):
        if heading is None:
            self._heading = None
            return

        # Check the given heading is a Quantity with a dimension of '' and units of
        # degrees or radians
        try:
            if not heading.check(""):
                raise ValueError(
                    "Heading must be a Quantity with a dimensionality of '' (ie. nothing)"
                )
            if not (
                heading.units == unit_registry.degree
                or heading.units == unit_registry.radian
            ):
                raise ValueError(
                    "Heading must be a Quantity with angular units (degree or radian)"
                )
        except AttributeError:
            raise TypeError("Heading must be a Quantity")

        # Set the actual heading attribute to the given value converted to radians
        self._heading = heading.to(unit_registry.radian).magnitude

    @heading.expression
    def heading(self):
        return self._heading

    #
    # Course properties
    #

    @hybrid_property
    def course(self):
        # Return all courses as degrees
        if self._course is None:
            return None
        else:
            return (self._course * unit_registry.radian).to(unit_registry.degree)

    @course.setter
    def course(self, course):
        if course is None:
            self._course = None
            return

        # Check the given course is a Quantity with a dimension of '' and units of
        # degrees or radians
        try:
            if not course.check(""):
                raise ValueError(
                    "Course must be a Quantity with a dimensionality of '' (ie. nothing)"
                )
            if not (
                course.units == unit_registry.degree
                or course.units == unit_registry.radian
            ):
                raise ValueError(
                    "Course must be a Quantity with angular units (degree or radian)"
                )
        except AttributeError:
            raise TypeError("Course must be a Quantity")

        # Set the actual course attribute to the given value converted to radians
        self._course = course.to(unit_registry.radian).magnitude

    @course.expression
    def course(self):
        return self._course


class ContactMixin:
    def submit(self, data_store, change_id):
        """Submit intermediate object to the DB"""
        data_store.session.add(self)
        data_store.session.flush()
        data_store.session.expire(self, ["_location"])
        # Log new Contact object creation
        data_store.add_to_logs(
            table=constants.CONTACT, row_id=self.contact_id, change_id=change_id
        )
        return self

    #
    # Bearing properties
    #

    @hybrid_property
    def bearing(self):
        # Return all bearings as degrees
        if self._bearing is None:
            return None
        else:
            return (self._bearing * unit_registry.radian).to(unit_registry.degree)

    @bearing.setter
    def bearing(self, bearing):
        if bearing is None:
            self._bearing = None
            return

        # Check the given bearing is a Quantity with a dimension of '' and units of
        # degrees or radians
        try:
            if not bearing.check(""):
                raise ValueError(
                    "Bearing must be a Quantity with a dimensionality of '' (ie. nothing)"
                )
            if not (
                bearing.units == unit_registry.degree
                or bearing.units == unit_registry.radian
            ):
                raise ValueError(
                    "Bearing must be a Quantity with angular units (degree or radian)"
                )
        except AttributeError:
            raise TypeError("Bearing must be a Quantity")

        # Set the actual bearing attribute to the given value converted to radians
        self._bearing = bearing.to(unit_registry.radian).magnitude

    @bearing.expression
    def bearing(self):
        return self._bearing


class CommentMixin:
    def submit(self, data_store, change_id):
        """Submit intermediate object to the DB"""
        data_store.session.add(self)
        data_store.session.flush()
        # Log new Comment object creation
        data_store.add_to_logs(
            table=constants.COMMENT, row_id=self.comment_id, change_id=change_id
        )
        return self


class MediaMixin:
    pass


class ElevationPropertyMixin:
    @hybrid_property
    def elevation(self):
        # Return all elevations as metres
        if self._elevation is None:
            return None
        else:
            return self._elevation * unit_registry.metre

    @elevation.setter
    def elevation(self, elevation):
        if elevation is None:
            self._elevation = None
            return

        # Check the given elevation is a Quantity with a dimension of 'length'
        try:
            if not elevation.check("[length]"):
                raise ValueError(
                    "Elevation must be a Quantity with a dimensionality of [length]"
                )
        except AttributeError:
            raise TypeError("Elevation must be a Quantity")

        # Set the actual elevation attribute to the given value converted to metres
        self._elevation = elevation.to(unit_registry.metre).magnitude

    @elevation.expression
    def elevation(self):
        return self._elevation


class LocationPropertyMixin:
    @hybrid_property
    def location(self):
        if self._location is None:
            return None
        else:
            loc = Location()
            if isinstance(self._location, str):
                loc.set_from_wkt_string(self._location)
            else:
                loc.set_from_wkb(self._location.desc)

            return loc

    @location.setter
    def location(self, location):
        if location is None:
            self._location = None
            return

        if not isinstance(location, Location):
            raise TypeError("location value must be an instance of the Location class")

        if not location.check_valid():
            raise ValueError("location object does not have valid values")

        self._location = location.to_wkt()

    @location.expression
    def location(self):
        return self._location
