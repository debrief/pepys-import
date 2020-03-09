from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DATE, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP, DOUBLE_PRECISION

from geoalchemy2 import Geometry

from pepys_import.core.store.db_base import BasePostGIS
from pepys_import.core.store.db_status import TableTypes
from pepys_import.core.store import constants
from pepys_import.core.validators import constants as validation_constants
from uuid import uuid4


# Metadata Tables
from pepys_import.core.validators.basic_validator import BasicValidator
from pepys_import.core.validators.enhanced_validator import EnhancedValidator


class HostedBy(BasePostGIS):
    __tablename__ = constants.HOSTED_BY
    table_type = TableTypes.METADATA
    table_type_id = 1
    __table_args__ = {"schema": "pepys"}

    hosted_by_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    subject_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Platforms.platform_id"), nullable=False
    )
    host_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Platforms.platform_id"), nullable=False
    )
    hosted_from = Column(DATE, nullable=False)
    host_to = Column(DATE, nullable=False)
    privacy_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Privacies.privacy_id"), nullable=False
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class Sensor(BasePostGIS):
    __tablename__ = constants.SENSOR
    table_type = TableTypes.METADATA
    table_type_id = 2
    __table_args__ = {"schema": "pepys"}

    sensor_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False)
    sensor_type_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.SensorTypes.sensor_type_id"),
        nullable=False,
    )
    host = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Platforms.platform_id"), nullable=False
    )
    created_date = Column(DateTime, default=datetime.utcnow)

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
        :type platform_id: UUID
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
    def add_to_sensors(cls, session, name, sensor_type, host):
        sensor_type = SensorType().search_sensor_type(session, sensor_type)
        host = Platform().search_platform(session, host)

        sensor_obj = Sensor(
            name=name, sensor_type_id=sensor_type.sensor_type_id, host=host.platform_id,
        )
        session.add(sensor_obj)
        session.flush()

        return sensor_obj


class Platform(BasePostGIS):
    __tablename__ = constants.PLATFORM
    table_type = TableTypes.METADATA
    table_type_id = 3
    __table_args__ = {"schema": "pepys"}

    platform_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False)
    pennant = Column(String(10))
    trigraph = Column(String(3))
    quadgraph = Column(String(4))
    nationality_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Nationalities.nationality_id"),
        nullable=False,
    )
    platform_type_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.PlatformTypes.platform_type_id"),
        nullable=False,
    )
    privacy_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Privacies.privacy_id"), nullable=False
    )
    created_date = Column(DateTime, default=datetime.utcnow)

    @classmethod
    def search_platform(cls, session, name):
        # search for any platform with this name
        return session.query(Platform).filter(Platform.name == name).first()

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

        # Check for name match in Sensor and Synonym Tables
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

        assert isinstance(sensor_type, SensorType), "Type error for Sensor Type entity"
        # TODO: we don't use privacy for sensor. Is it necessary to resolve it?
        # assert isinstance(privacy, Privacy), "Type error for Privacy entity"

        return Sensor().add_to_sensors(
            session=data_store.session,
            name=sensor_name,
            sensor_type=sensor_type.name,
            host=self.name,
        )


class Task(BasePostGIS):
    __tablename__ = constants.TASK
    table_type = TableTypes.METADATA
    table_type_id = 4
    __table_args__ = {"schema": "pepys"}

    task_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    parent_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Tasks.task_id"), nullable=False
    )
    start = Column(TIMESTAMP, nullable=False)
    end = Column(TIMESTAMP, nullable=False)
    environment = Column(String(150))
    location = Column(String(150))
    privacy_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Privacies.privacy_id"), nullable=False
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class Participant(BasePostGIS):
    __tablename__ = constants.PARTICIPANT
    table_type = TableTypes.METADATA
    table_type_id = 5
    __table_args__ = {"schema": "pepys"}

    participant_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    platform_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Platforms.platform_id"), nullable=False
    )
    task_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Tasks.task_id"), nullable=False
    )
    start = Column(TIMESTAMP)
    end = Column(TIMESTAMP)
    force = Column(String(150))
    privacy_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Privacies.privacy_id"), nullable=False
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class Datafile(BasePostGIS):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.measurements = dict()

    __tablename__ = constants.DATAFILE
    table_type = TableTypes.METADATA
    table_type_id = 6  # Only needed for tables referenced by Entry table
    __table_args__ = {"schema": "pepys"}

    datafile_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    simulated = Column(Boolean)
    privacy_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Privacies.privacy_id"), nullable=False
    )
    datafile_type_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.DatafileTypes.datafile_type_id"),
        nullable=False,
    )
    reference = Column(String(150))
    url = Column(String(150))
    created_date = Column(DateTime, default=datetime.utcnow)

    def create_state(self, sensor, timestamp, parser_name):
        state = State(
            sensor_id=sensor.sensor_id, time=timestamp, source_id=self.datafile_id
        )
        self.measurements[parser_name].append(state)
        return state

    def create_contact(self, sensor, timestamp, parser_name):
        contact = Contact(
            sensor_id=sensor.sensor_id, time=timestamp, source_id=self.datafile_id
        )
        self.measurements[parser_name].append(contact)
        return contact

    def create_comment(
        self, platform_id, timestamp, comment, comment_type, parser_name
    ):
        comment = Comment(
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

    # def verify(self):
    #     pass


class Synonym(BasePostGIS):
    __tablename__ = constants.SYNONYM
    table_type = TableTypes.METADATA
    table_type_id = 7
    __table_args__ = {"schema": "pepys"}

    synonym_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    table = Column(String(150), nullable=False)
    entity = Column(UUID(as_uuid=True), nullable=False)
    synonym = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Change(BasePostGIS):
    __tablename__ = constants.CHANGE
    table_type = TableTypes.METADATA
    table_type_id = 8
    __table_args__ = {"schema": "pepys"}

    change_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user = Column(String(150), nullable=False)
    modified = Column(DATE, nullable=False)
    reason = Column(String(500), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Log(BasePostGIS):
    __tablename__ = constants.LOG
    table_type = TableTypes.METADATA
    table_type_id = 9
    __table_args__ = {"schema": "pepys"}

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    table = Column(String(150), nullable=False)
    id = Column(UUID(as_uuid=True), ForeignKey("pepys.Logs.log_id"), nullable=False)
    field = Column(String(150), nullable=False)
    new_value = Column(String(150), nullable=False)
    change_id = Column(UUID, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Extraction(BasePostGIS):
    __tablename__ = constants.EXTRACTION
    table_type = TableTypes.METADATA
    table_type_id = 10
    __table_args__ = {"schema": "pepys"}

    extraction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    table = Column(String(150), nullable=False)
    field = Column(String(150), nullable=False)
    chars = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Tag(BasePostGIS):
    __tablename__ = constants.TAG
    table_type = TableTypes.METADATA
    table_type_id = 11
    __table_args__ = {"schema": "pepys"}

    tag_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class TaggedItem(BasePostGIS):
    __tablename__ = constants.TAGGED_ITEM
    table_type = TableTypes.METADATA
    table_type_id = 12
    __table_args__ = {"schema": "pepys"}

    tagged_item_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tag_id = Column(UUID(as_uuid=True), ForeignKey("pepys.Tags.tag_id"), nullable=False)
    item_id = Column(UUID(as_uuid=True), nullable=False)
    tagged_by_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Users.user_id"), nullable=False
    )
    private = Column(Boolean, nullable=False)
    tagged_on = Column(DATE, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


# Reference Tables
class PlatformType(BasePostGIS):
    __tablename__ = constants.PLATFORM_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 13
    __table_args__ = {"schema": "pepys"}

    platform_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Nationality(BasePostGIS):
    __tablename__ = constants.NATIONALITY
    table_type = TableTypes.REFERENCE
    table_type_id = 14
    __table_args__ = {"schema": "pepys"}

    nationality_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class GeometryType(BasePostGIS):
    __tablename__ = constants.GEOMETRY_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 15
    __table_args__ = {"schema": "pepys"}

    geo_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class GeometrySubType(BasePostGIS):
    __tablename__ = constants.GEOMETRY_SUBTYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 16
    __table_args__ = {"schema": "pepys"}

    geo_sub_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False)
    # parent = Column(UUID(as_uuid=True), ForeignKey("pepys.GeometryTypes.geometry_type_id"))
    parent = Column(UUID, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class User(BasePostGIS):
    __tablename__ = constants.USER
    table_type = TableTypes.REFERENCE
    table_type_id = 17
    __table_args__ = {"schema": "pepys"}

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class UnitType(BasePostGIS):
    __tablename__ = constants.UNIT_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 18
    __table_args__ = {"schema": "pepys"}

    unit_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    units = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class ClassificationType(BasePostGIS):
    __tablename__ = constants.CLASSIFICATION_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 19
    __table_args__ = {"schema": "pepys"}

    class_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    class_type = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class ContactType(BasePostGIS):
    __tablename__ = constants.CONTACT_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 20
    __table_args__ = {"schema": "pepys"}

    contact_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    contact_type = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class SensorType(BasePostGIS):
    __tablename__ = constants.SENSOR_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 21
    __table_args__ = {"schema": "pepys"}

    sensor_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)

    @classmethod
    def search_sensor_type(cls, session, name):
        # search for any sensor type featuring this name
        return session.query(SensorType).filter(SensorType.name == name).first()


class Privacy(BasePostGIS):
    __tablename__ = constants.PRIVACY
    table_type = TableTypes.REFERENCE
    table_type_id = 22
    __table_args__ = {"schema": "pepys"}

    privacy_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class DatafileType(BasePostGIS):
    __tablename__ = constants.DATAFILE_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 23
    __table_args__ = {"schema": "pepys"}

    datafile_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class MediaType(BasePostGIS):
    __tablename__ = constants.MEDIA_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 24
    __table_args__ = {"schema": "pepys"}

    media_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class CommentType(BasePostGIS):
    __tablename__ = constants.COMMENT_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 25
    __table_args__ = {"schema": "pepys"}

    comment_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class CommodityType(BasePostGIS):
    __tablename__ = constants.COMMODITY_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 26
    __table_args__ = {"schema": "pepys"}

    commodity_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class ConfidenceLevel(BasePostGIS):
    __tablename__ = constants.CONFIDENCE_LEVEL
    table_type = TableTypes.REFERENCE
    table_type_id = 27  # Only needed for tables referenced by Entry table
    __table_args__ = {"schema": "pepys"}

    confidence_level_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    level = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


# Measurements Tables
class State(BasePostGIS):
    __tablename__ = constants.STATE
    table_type = TableTypes.MEASUREMENT
    table_type_id = 28
    __table_args__ = {"schema": "pepys"}

    state_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    time = Column(TIMESTAMP, nullable=False)
    sensor_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Sensors.sensor_id"), nullable=False
    )
    location = Column(Geometry(geometry_type="POINT", srid=0))
    elevation = Column(DOUBLE_PRECISION)
    heading = Column(DOUBLE_PRECISION)
    course = Column(DOUBLE_PRECISION)
    speed = Column(DOUBLE_PRECISION)
    source_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Datafiles.datafile_id"), nullable=False
    )
    privacy_id = Column(UUID(as_uuid=True), ForeignKey("pepys.Privacies.privacy_id"))
    created_date = Column(DateTime, default=datetime.utcnow)

    def submit(self, session):
        """Submit intermediate object to the DB"""
        session.add(self)
        session.flush()

        return self


class Contact(BasePostGIS):
    __tablename__ = constants.CONTACT
    table_type = TableTypes.MEASUREMENT
    table_type_id = 29
    __table_args__ = {"schema": "pepys"}

    contact_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False)
    sensor_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Sensors.sensor_id"), nullable=False
    )
    time = Column(TIMESTAMP, nullable=False)
    bearing = Column(DOUBLE_PRECISION)
    rel_bearing = Column(DOUBLE_PRECISION)
    freq = Column(DOUBLE_PRECISION)
    location = Column(Geometry(geometry_type="POINT", srid=4326))
    elevation = Column(DOUBLE_PRECISION)
    major = Column(DOUBLE_PRECISION)
    minor = Column(DOUBLE_PRECISION)
    orientation = Column(DOUBLE_PRECISION)
    classification = Column(String(150))
    confidence = Column(String(150))
    contact_type = Column(String(150))
    mla = Column(DOUBLE_PRECISION)
    sla = Column(DOUBLE_PRECISION)
    subject_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Platforms.platform_id"), nullable=False
    )
    source_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Datafiles.datafile_id"), nullable=False
    )
    privacy_id = Column(UUID(as_uuid=True), ForeignKey("pepys.Privacies.privacy_id"))
    created_date = Column(DateTime, default=datetime.utcnow)

    def submit(self, session):
        """Submit intermediate object to the DB"""
        session.add(self)
        session.flush()

        return self


class Activation(BasePostGIS):
    __tablename__ = constants.ACTIVATION
    table_type = TableTypes.MEASUREMENT
    table_type_id = 30
    __table_args__ = {"schema": "pepys"}

    activation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False)
    sensor_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Sensors.sensor_id"), nullable=False
    )
    start = Column(TIMESTAMP, nullable=False)
    end = Column(TIMESTAMP, nullable=False)
    min_range = Column(DOUBLE_PRECISION)
    max_range = Column(DOUBLE_PRECISION)
    left_arc = Column(DOUBLE_PRECISION)
    right_arc = Column(DOUBLE_PRECISION)
    source_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Datafiles.datafile_id"), nullable=False
    )
    privacy_id = Column(UUID(as_uuid=True), ForeignKey("pepys.Privacies.privacy_id"))
    created_date = Column(DateTime, default=datetime.utcnow)


class LogsHolding(BasePostGIS):
    __tablename__ = constants.LOGS_HOLDING
    table_type = TableTypes.MEASUREMENT
    table_type_id = 31
    __table_args__ = {"schema": "pepys"}

    logs_holding_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    time = Column(TIMESTAMP, nullable=False)
    quantity = Column(DOUBLE_PRECISION, nullable=False)
    unit_type_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.UnitTypes.unit_type_id"), nullable=False
    )
    platform_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Platforms.platform_id"), nullable=False
    )
    comment = Column(String(150), nullable=False)
    source_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Datafiles.datafile_id"), nullable=False
    )
    privacy_id = Column(UUID(as_uuid=True), ForeignKey("pepys.Privacies.privacy_id"))
    created_date = Column(DateTime, default=datetime.utcnow)


class Comment(BasePostGIS):
    __tablename__ = constants.COMMENT
    table_type = TableTypes.MEASUREMENT
    table_type_id = 32
    __table_args__ = {"schema": "pepys"}

    comment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    platform_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Platforms.platform_id"), nullable=False
    )
    time = Column(TIMESTAMP, nullable=False)
    comment_type_id = Column(UUID(as_uuid=True), nullable=False)
    content = Column(String(150), nullable=False)
    source_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Datafiles.datafile_id"), nullable=False
    )
    privacy_id = Column(UUID(as_uuid=True), ForeignKey("pepys.Privacies.privacy_id"))
    created_date = Column(DateTime, default=datetime.utcnow)

    def submit(self, session):
        """Submit intermediate object to the DB"""
        session.add(self)
        session.flush()

        return self


class Geometry1(BasePostGIS):
    __tablename__ = constants.GEOMETRY
    table_type = TableTypes.MEASUREMENT
    table_type_id = 33
    __table_args__ = {"schema": "pepys"}

    geometry_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    geometry = Column(Geometry, nullable=False)
    name = Column(String(150), nullable=False)
    geo_type_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.GeometryTypes.geo_type_id"),
        nullable=False,
    )
    geo_sub_type_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.GeometrySubTypes.geo_sub_type_id"),
        nullable=False,
    )
    start = Column(TIMESTAMP)
    end = Column(TIMESTAMP)
    task_id = Column(UUID(as_uuid=True))
    subject_platform_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Platforms.platform_id")
    )
    sensor_platform_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Platforms.platform_id")
    )
    source_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Datafiles.datafile_id"), nullable=False
    )
    privacy_id = Column(UUID(as_uuid=True), ForeignKey("pepys.Privacies.privacy_id"))
    created_date = Column(DateTime, default=datetime.utcnow)


class Media(BasePostGIS):
    __tablename__ = constants.MEDIA
    table_type = TableTypes.MEASUREMENT
    table_type_id = 34
    __table_args__ = {"schema": "pepys"}

    media_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    platform_id = Column(UUID(as_uuid=True), ForeignKey("pepys.Platforms.platform_id"))
    subject_id = Column(UUID(as_uuid=True), ForeignKey("pepys.Platforms.platform_id"))
    sensor_id = Column(UUID(as_uuid=True), ForeignKey("pepys.Sensors.sensor_id"))
    location = Column(Geometry(geometry_type="POINT", srid=4326))
    elevation = Column(DOUBLE_PRECISION)
    time = Column(TIMESTAMP)
    media_type_id = Column(UUID(as_uuid=True), nullable=False)
    url = Column(String(150), nullable=False)
    source_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Datafiles.datafile_id"), nullable=False
    )
    privacy_id = Column(UUID(as_uuid=True), ForeignKey("pepys.Privacies.privacy_id"))
    created_date = Column(DateTime, default=datetime.utcnow)
