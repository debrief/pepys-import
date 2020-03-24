from tqdm import tqdm
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
        self.add_measurement_to_dict(state, parser_name)
        return state

    def create_contact(self, data_store, platform, sensor, timestamp, parser_name):
        contact = data_store.db_classes.Contact(
            sensor_id=sensor.sensor_id, time=timestamp, source_id=self.datafile_id
        )
        contact.platform_name = platform.name
        contact.sensor_name = sensor.name
        self.add_measurement_to_dict(contact, parser_name)
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
        self.add_measurement_to_dict(comment, parser_name)
        return comment

    def add_measurement_to_dict(self, measurement, parser_name):
        # Cache objects according to their platform
        if measurement.platform_name not in self.measurements[parser_name]:
            self.measurements[parser_name][measurement.platform_name] = list()

        self.measurements[parser_name][measurement.platform_name].append(measurement)

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
            for key, objects in self.measurements[parser].items():
                for index, curr_object in enumerate(objects):
                    prev_object = None
                    if index >= 1:
                        prev_object = objects[index - 1]

                    BasicValidator(curr_object, errors, parser)
                    for basic_validator in LOCAL_BASIC_VALIDATORS:
                        basic_validator(curr_object, errors, parser)
                    EnhancedValidator(curr_object, errors, parser, prev_object)
                    for enhanced_validator in LOCAL_ENHANCED_VALIDATORS:
                        enhanced_validator(curr_object, errors, parser, prev_object)
            if not errors:
                return True
            return False

    def commit(self, data_store, change_id):
        # Since measurements are saved by their importer names, iterate over each key
        # and save its measurement objects.
        extraction_log = list()
        for key in self.measurements:
            total_objects = 0
            for platform, objects in self.measurements[key].items():
                total_objects += len(objects)
                print(f"Submitting measurements extracted by {key}.")
                for obj in tqdm(objects):
                    obj.submit(data_store, change_id)
            extraction_log.append(f"{total_objects} measurements extracted by {key}.")
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

    #
    # Rel Bearing properties
    #

    @hybrid_property
    def rel_bearing(self):
        # Return all rel_bearings as degrees
        if self._rel_bearing is None:
            return None
        else:
            return (self._rel_bearing * unit_registry.radian).to(unit_registry.degree)

    @rel_bearing.setter
    def rel_bearing(self, rel_bearing):
        if rel_bearing is None:
            self._rel_bearing = None
            return

        # Check the given bearing is a Quantity with a dimension of '' and units of
        # degrees or radians
        try:
            if not rel_bearing.check(""):
                raise ValueError(
                    "Relative Bearing must be a Quantity with a dimensionality of '' (ie. nothing)"
                )
            if not (
                rel_bearing.units == unit_registry.degree
                or rel_bearing.units == unit_registry.radian
            ):
                raise ValueError(
                    "Relative Bearing must be a Quantity with angular units (degree or radian)"
                )
        except AttributeError:
            raise TypeError("Relative Bearing must be a Quantity")

        # Set the actual bearing attribute to the given value converted to radians
        self._rel_bearing = rel_bearing.to(unit_registry.radian).magnitude

    @rel_bearing.expression
    def rel_bearing(self):
        return self._rel_bearing

    #
    # MLA properties
    #

    @hybrid_property
    def mla(self):
        # Return all MLA's as degrees
        if self._mla is None:
            return None
        else:
            return (self._mla * unit_registry.radian).to(unit_registry.degree)

    @mla.setter
    def mla(self, mla):
        if mla is None:
            self._mla = None
            return

        # Check the given bearing is a Quantity with a dimension of '' and units of
        # degrees or radians
        try:
            if not mla.check(""):
                raise ValueError(
                    "MLA must be a Quantity with a dimensionality of '' (ie. nothing)"
                )
            if not (
                mla.units == unit_registry.degree or mla.units == unit_registry.radian
            ):
                raise ValueError(
                    "MLA must be a Quantity with angular units (degree or radian)"
                )
        except AttributeError:
            raise TypeError("MLA must be a Quantity")

        # Set the actual bearing attribute to the given value converted to radians
        self._mla = mla.to(unit_registry.radian).magnitude

    @mla.expression
    def mla(self):
        return self._mla

    #
    # SOA properties
    #

    @hybrid_property
    def soa(self):
        # Return all soas as metres per second
        if self._soa is None:
            return None
        else:
            return self._soa * (unit_registry.metre / unit_registry.second)

    @soa.setter
    def soa(self, soa):
        if soa is None:
            self._soa = None
            return

        # Check the given soa is a Quantity with a dimension of 'length / time'
        try:
            if not soa.check("[length]/[time]"):
                raise ValueError(
                    "SOA must be a Quantity with a dimensionality of [length]/[time]"
                )
        except AttributeError:
            raise TypeError("SOA must be a Quantity")

        # Set the actual soa attribute to the given value converted to metres per second
        self._soa = soa.to(unit_registry.metre / unit_registry.second).magnitude

    @soa.expression
    def soa(self):
        return self._soa

    #
    # Orientation properties
    #

    @hybrid_property
    def orientation(self):
        # Return all orientation's as degrees
        if self._orientation is None:
            return None
        else:
            return (self._orientation * unit_registry.radian).to(unit_registry.degree)

    @orientation.setter
    def orientation(self, orientation):
        if orientation is None:
            self._orientation = None
            return

        # Check the given orientation is a Quantity with a dimension of '' and units of
        # degrees or radians
        try:
            if not orientation.check(""):
                raise ValueError(
                    "Orientation must be a Quantity with a dimensionality of '' (ie. nothing)"
                )
            if not (
                orientation.units == unit_registry.degree
                or orientation.units == unit_registry.radian
            ):
                raise ValueError(
                    "Orientation must be a Quantity with angular units (degree or radian)"
                )
        except AttributeError:
            raise TypeError("Orientation must be a Quantity")

        # Set the actual bearing attribute to the given value converted to radians
        self._orientation = orientation.to(unit_registry.radian).magnitude

    @orientation.expression
    def orientation(self):
        return self._orientation

    #
    # Major property
    #

    @hybrid_property
    def major(self):
        # Return all majors as metres
        if self._major is None:
            return None
        else:
            return self._major * unit_registry.metre

    @major.setter
    def major(self, major):
        if major is None:
            self._major = None
            return

        # Check the given major is a Quantity with a dimension of 'length'
        try:
            if not major.check("[length]"):
                raise ValueError(
                    "Major must be a Quantity with a dimensionality of [length]"
                )
        except AttributeError:
            raise TypeError("Major must be a Quantity")

        # Set the actual major attribute to the given value converted to metres
        self._major = major.to(unit_registry.metre).magnitude

    @major.expression
    def major(self):
        return self._major

    #
    # Minor property
    #

    @hybrid_property
    def minor(self):
        # Return all minors as metres
        if self._minor is None:
            return None
        else:
            return self._minor * unit_registry.metre

    @minor.setter
    def minor(self, minor):
        if minor is None:
            self._minor = None
            return

        # Check the given minor is a Quantity with a dimension of 'length'
        try:
            if not minor.check("[length]"):
                raise ValueError(
                    "Minor must be a Quantity with a dimensionality of [length]"
                )
        except AttributeError:
            raise TypeError("Minor must be a Quantity")

        # Set the actual minor attribute to the given value converted to metres
        self._minor = minor.to(unit_registry.metre).magnitude

    @minor.expression
    def minor(self):
        return self._minor

    #
    # Range property
    #

    @hybrid_property
    def range(self):
        # Return all ranges as metres
        if self._range is None:
            return None
        else:
            return self._range * unit_registry.metre

    @range.setter
    def range(self, range):
        if range is None:
            self._range = None
            return

        # Check the given range is a Quantity with a dimension of 'length'
        try:
            if not range.check("[length]"):
                raise ValueError(
                    "Range must be a Quantity with a dimensionality of [length]"
                )
        except AttributeError:
            raise TypeError("Range must be a Quantity")

        # Set the actual range attribute to the given value converted to metres
        self._range = range.to(unit_registry.metre).magnitude

    @range.expression
    def range(self):
        return self._range

    #
    # Freq property
    #

    @hybrid_property
    def freq(self):
        # Return all freqs as Hz
        if self._freq is None:
            return None
        else:
            return self._freq * unit_registry.hertz

    @freq.setter
    def freq(self, freq):
        if freq is None:
            self._freq = None
            return

        # Check the given freq is a Quantity with a dimension of 'time^-1' (ie. 'per unit time')
        try:
            if not freq.check("[time]^-1"):
                raise ValueError(
                    "Freq must be a Quantity with a dimensionality of [time]^-1"
                )
        except AttributeError:
            raise TypeError("Freq must be a Quantity")

        # Set the actual freq attribute to the given value converted to hertz
        self._freq = freq.to(unit_registry.hertz).magnitude

    @freq.expression
    def freq(self):
        return self._freq


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


class ActivationMixin:
    #
    # min_range property
    #
    @hybrid_property
    def min_range(self):
        # Return all min_ranges as metres
        if self._min_range is None:
            return None
        else:
            return self._min_range * unit_registry.metre

    @min_range.setter
    def min_range(self, min_range):
        if min_range is None:
            self._min_range = None
            return

        # Check the given min_range is a Quantity with a dimension of 'length'
        try:
            if not min_range.check("[length]"):
                raise ValueError(
                    "min_range must be a Quantity with a dimensionality of [length]"
                )
        except AttributeError:
            raise TypeError("min_range must be a Quantity")

        # Set the actual min_range attribute to the given value converted to metres
        self._min_range = min_range.to(unit_registry.metre).magnitude

    @min_range.expression
    def min_range(self):
        return self._min_range

    #
    # max_range property
    #
    @hybrid_property
    def max_range(self):
        # Return all max_ranges as metres
        if self._max_range is None:
            return None
        else:
            return self._max_range * unit_registry.metre

    @max_range.setter
    def max_range(self, max_range):
        if max_range is None:
            self._max_range = None
            return

        # Check the given max_range is a Quantity with a dimension of 'length'
        try:
            if not max_range.check("[length]"):
                raise ValueError(
                    "max_range must be a Quantity with a dimensionality of [length]"
                )
        except AttributeError:
            raise TypeError("max_range must be a Quantity")

        # Set the actual max_range attribute to the given value converted to metres
        self._max_range = max_range.to(unit_registry.metre).magnitude

    @max_range.expression
    def max_range(self):
        return self._max_range

    #
    # left_arc properties
    #

    @hybrid_property
    def left_arc(self):
        # Return all left_arcs as degrees
        if self._left_arc is None:
            return None
        else:
            return (self._left_arc * unit_registry.radian).to(unit_registry.degree)

    @left_arc.setter
    def left_arc(self, left_arc):
        if left_arc is None:
            self._left_arc = None
            return

        # Check the given left_arc is a Quantity with a dimension of '' and units of
        # degrees or radians
        try:
            if not left_arc.check(""):
                raise ValueError(
                    "left_arc must be a Quantity with a dimensionality of '' (ie. nothing)"
                )
            if not (
                left_arc.units == unit_registry.degree
                or left_arc.units == unit_registry.radian
            ):
                raise ValueError(
                    "left_arc must be a Quantity with angular units (degree or radian)"
                )
        except AttributeError:
            raise TypeError("left_arc must be a Quantity")

        # Set the actual left_arc attribute to the given value converted to radians
        self._left_arc = left_arc.to(unit_registry.radian).magnitude

    @left_arc.expression
    def left_arc(self):
        return self._left_arc

    #
    # right_arc properties
    #

    @hybrid_property
    def right_arc(self):
        # Return all right_arcs as degrees
        if self._right_arc is None:
            return None
        else:
            return (self._right_arc * unit_registry.radian).to(unit_registry.degree)

    @right_arc.setter
    def right_arc(self, right_arc):
        if right_arc is None:
            self._right_arc = None
            return

        # Check the given right_arc is a Quantity with a dimension of '' and units of
        # degrees or radians
        try:
            if not right_arc.check(""):
                raise ValueError(
                    "right_arc must be a Quantity with a dimensionality of '' (ie. nothing)"
                )
            if not (
                right_arc.units == unit_registry.degree
                or right_arc.units == unit_registry.radian
            ):
                raise ValueError(
                    "right_arc must be a Quantity with angular units (degree or radian)"
                )
        except AttributeError:
            raise TypeError("right_arc must be a Quantity")

        # Set the actual right_arc attribute to the given value converted to radians
        self._right_arc = right_arc.to(unit_registry.radian).magnitude

    @right_arc.expression
    def right_arc(self):
        return self._right_arc
