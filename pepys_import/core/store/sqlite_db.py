from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DATE, DateTime
from sqlalchemy.dialects.sqlite import TIMESTAMP, REAL

from geoalchemy2 import Geometry

from pepys_import.core.store.db_base import BaseSpatiaLite
from pepys_import.core.store.db_status import TableTypes
from pepys_import.core.store import constants

from pepys_import.core.store.common_db import (
    SensorMixin,
    PlatformMixin,
    DatafileMixin,
    SensorTypeMixin,
)


# Metadata Tables
class HostedBy(BaseSpatiaLite):
    __tablename__ = constants.HOSTED_BY
    table_type = TableTypes.METADATA
    table_type_id = 1

    hosted_by_id = Column(Integer, primary_key=True)
    subject_id = Column(Integer, nullable=False)
    host_id = Column(Integer, nullable=False)
    hosted_from = Column(DATE, nullable=False)
    host_to = Column(DATE, nullable=False)
    privacy_id = Column(Integer, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Sensor(BaseSpatiaLite, SensorMixin):
    __tablename__ = constants.SENSOR
    table_type = TableTypes.METADATA
    table_type_id = 2

    sensor_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    sensor_type_id = Column(Integer, nullable=False)
    host = Column(Integer, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Platform(BaseSpatiaLite, PlatformMixin):
    __tablename__ = constants.PLATFORM
    table_type = TableTypes.METADATA
    table_type_id = 3

    platform_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    pennant = Column(String(10))
    trigraph = Column(String(3))
    quadgraph = Column(String(4))
    nationality_id = Column(Integer, nullable=False)
    platform_type_id = Column(Integer, nullable=False)
    privacy_id = Column(Integer, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Task(BaseSpatiaLite):
    __tablename__ = constants.TASK
    table_type = TableTypes.METADATA
    table_type_id = 4

    task_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    parent_id = Column(Integer, nullable=False)
    start = Column(TIMESTAMP, nullable=False)
    end = Column(TIMESTAMP, nullable=False)
    environment = Column(String(150))
    location = Column(String(150))
    privacy_id = Column(Integer, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Participant(BaseSpatiaLite):
    __tablename__ = constants.PARTICIPANT
    table_type = TableTypes.METADATA
    table_type_id = 5

    participant_id = Column(Integer, primary_key=True)
    platform_id = Column(Integer, nullable=False)
    task_id = Column(Integer, nullable=False)
    start = Column(TIMESTAMP)
    end = Column(TIMESTAMP)
    force = Column(String(150))
    privacy_id = Column(Integer, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Datafile(BaseSpatiaLite, DatafileMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.measurements = dict()

    __tablename__ = constants.DATAFILE
    table_type = TableTypes.METADATA
    table_type_id = 6

    datafile_id = Column(Integer, primary_key=True)
    simulated = Column(Boolean, nullable=False)
    privacy_id = Column(Integer, nullable=False)
    datafile_type_id = Column(Integer, nullable=False)
    reference = Column(String(150))
    url = Column(String(150))
    created_date = Column(DateTime, default=datetime.utcnow)


class Synonym(BaseSpatiaLite):
    __tablename__ = constants.SYNONYM
    table_type = TableTypes.METADATA
    table_type_id = 7

    synonym_id = Column(Integer, primary_key=True)
    table = Column(String(150), nullable=False)
    entity = Column(Integer, nullable=False)
    synonym = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Change(BaseSpatiaLite):
    __tablename__ = constants.CHANGE
    table_type = TableTypes.METADATA
    table_type_id = 8

    change_id = Column(Integer, primary_key=True)
    user = Column(String(150), nullable=False)
    modified = Column(DATE, nullable=False)
    reason = Column(String(500), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Log(BaseSpatiaLite):
    __tablename__ = constants.LOG
    table_type = TableTypes.METADATA
    table_type_id = 9

    log_id = Column(Integer, primary_key=True)
    table = Column(String(150), nullable=False)
    id = Column(Integer, nullable=False)
    field = Column(String(150), nullable=False)
    new_value = Column(String(150), nullable=False)
    change_id = Column(Integer, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Extraction(BaseSpatiaLite):
    __tablename__ = constants.EXTRACTION
    table_type = TableTypes.METADATA
    table_type_id = 10

    extraction_id = Column(Integer, primary_key=True)
    table = Column(String(150), nullable=False)
    field = Column(String(150), nullable=False)
    chars = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Tag(BaseSpatiaLite):
    __tablename__ = constants.TAG
    table_type = TableTypes.METADATA
    table_type_id = 11

    tag_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class TaggedItem(BaseSpatiaLite):
    __tablename__ = constants.TAGGED_ITEM
    table_type = TableTypes.METADATA
    table_type_id = 12

    tagged_item_id = Column(Integer, primary_key=True)
    tag_id = Column(Integer, nullable=False)
    item_id = Column(Integer, nullable=False)
    tagged_by_id = Column(Integer, nullable=False)
    private = Column(Boolean, nullable=False)
    tagged_on = Column(DATE, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


# Reference Tables
class PlatformType(BaseSpatiaLite):
    __tablename__ = constants.PLATFORM_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 13

    platform_type_id = Column(Integer, primary_key=True)
    name = Column(String(150))
    created_date = Column(DateTime, default=datetime.utcnow)


class Nationality(BaseSpatiaLite):
    __tablename__ = constants.NATIONALITY
    table_type = TableTypes.REFERENCE
    table_type_id = 14

    nationality_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class GeometryType(BaseSpatiaLite):
    __tablename__ = constants.GEOMETRY_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 15

    geo_type_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class GeometrySubType(BaseSpatiaLite):
    __tablename__ = constants.GEOMETRY_SUBTYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 16

    geo_sub_type_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    parent = Column(Integer, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class User(BaseSpatiaLite):
    __tablename__ = constants.USER
    table_type = TableTypes.REFERENCE
    table_type_id = 17

    user_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class UnitType(BaseSpatiaLite):
    __tablename__ = constants.UNIT_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 18

    unit_type_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class ClassificationType(BaseSpatiaLite):
    __tablename__ = constants.CLASSIFICATION_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 19

    class_type_id = Column(Integer, primary_key=True)
    class_type = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class ContactType(BaseSpatiaLite):
    __tablename__ = constants.CONTACT_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 20

    contact_type_id = Column(Integer, primary_key=True)
    contact_type = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class SensorType(BaseSpatiaLite, SensorTypeMixin):
    __tablename__ = constants.SENSOR_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 21

    sensor_type_id = Column(Integer, primary_key=True)
    name = Column(String(150))
    created_date = Column(DateTime, default=datetime.utcnow)


class Privacy(BaseSpatiaLite):
    __tablename__ = constants.PRIVACY
    table_type = TableTypes.REFERENCE
    table_type_id = 22

    privacy_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class DatafileType(BaseSpatiaLite):
    __tablename__ = constants.DATAFILE_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 23

    datafile_type_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class MediaType(BaseSpatiaLite):
    __tablename__ = constants.MEDIA_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 24

    media_type_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class CommentType(BaseSpatiaLite):
    __tablename__ = constants.COMMENT_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 25

    comment_type_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class CommodityType(BaseSpatiaLite):
    __tablename__ = constants.COMMODITY_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 26

    commodity_type_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class ConfidenceLevel(BaseSpatiaLite):
    __tablename__ = constants.CONFIDENCE_LEVEL
    table_type = TableTypes.REFERENCE
    table_type_id = 27

    confidence_level_id = Column(Integer, primary_key=True)
    level = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


# Measurements Tables
class State(BaseSpatiaLite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prev_location = None

    __tablename__ = constants.STATE
    table_type = TableTypes.MEASUREMENT
    table_type_id = 28

    state_id = Column(Integer, primary_key=True)
    time = Column(TIMESTAMP, nullable=False)
    sensor_id = Column(Integer, nullable=False)
    location = Column(Geometry(geometry_type="POINT", management=True))
    elevation = Column(REAL)
    heading = Column(REAL)
    course = Column(REAL)
    speed = Column(REAL)
    source_id = Column(Integer, nullable=False)
    privacy_id = Column(Integer)
    created_date = Column(DateTime, default=datetime.utcnow)

    def submit(self, session):
        """Submit intermediate object to the DB"""
        session.add(self)
        session.flush()

        return self


class Contact(BaseSpatiaLite):
    __tablename__ = constants.CONTACT
    table_type = TableTypes.MEASUREMENT
    table_type_id = 29

    contact_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    sensor_id = Column(Integer, nullable=False)
    time = Column(TIMESTAMP, nullable=False)
    bearing = Column(REAL)
    rel_bearing = Column(REAL)
    freq = Column(REAL)
    location = Column(Geometry(geometry_type="POINT", management=True))
    elevation = Column(REAL)
    major = Column(REAL)
    minor = Column(REAL)
    orientation = Column(REAL)
    classification = Column(String(150))
    confidence = Column(String(150))
    contact_type = Column(String(150))
    mla = Column(REAL)
    sla = Column(REAL)
    subject_id = Column(Integer)
    source_id = Column(Integer, nullable=False)
    privacy_id = Column(Integer)
    created_date = Column(DateTime, default=datetime.utcnow)

    def submit(self, session):
        """Submit intermediate object to the DB"""
        session.add(self)
        session.flush()

        return self


class Activation(BaseSpatiaLite):
    __tablename__ = constants.ACTIVATION
    table_type = TableTypes.MEASUREMENT
    table_type_id = 30

    activation_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    sensor_id = Column(Integer, nullable=False)
    start = Column(TIMESTAMP, nullable=False)
    end = Column(TIMESTAMP, nullable=False)
    min_range = Column(REAL)
    max_range = Column(REAL)
    left_arc = Column(REAL)
    right_arc = Column(REAL)
    source_id = Column(Integer, nullable=False)
    privacy_id = Column(Integer)
    created_date = Column(DateTime, default=datetime.utcnow)


class LogsHolding(BaseSpatiaLite):
    __tablename__ = constants.LOGS_HOLDING
    table_type = TableTypes.MEASUREMENT
    table_type_id = 31

    logs_holding_id = Column(Integer, primary_key=True)
    time = Column(TIMESTAMP, nullable=False)
    commodity_id = Column(Integer, nullable=False)
    quantity = Column(REAL, nullable=False)
    unit_type_id = Column(Integer, nullable=False)
    platform_id = Column(Integer, nullable=False)
    comment = Column(String(150), nullable=False)
    source_id = Column(Integer, nullable=False)
    privacy_id = Column(Integer)
    created_date = Column(DateTime, default=datetime.utcnow)


class Comment(BaseSpatiaLite):
    __tablename__ = constants.COMMENT
    table_type = TableTypes.MEASUREMENT
    table_type_id = 32

    comment_id = Column(Integer, primary_key=True)
    platform_id = Column(Integer)
    time = Column(TIMESTAMP, nullable=False)
    comment_type_id = Column(Integer, nullable=False)
    content = Column(String(150), nullable=False)
    source_id = Column(Integer, nullable=False)
    privacy_id = Column(Integer)
    created_date = Column(DateTime, default=datetime.utcnow)

    def submit(self, session):
        """Submit intermediate object to the DB"""
        session.add(self)
        session.flush()

        return self


class Geometry1(BaseSpatiaLite):
    __tablename__ = constants.GEOMETRY
    table_type = TableTypes.MEASUREMENT
    table_type_id = 33

    geometry_id = Column(Integer, primary_key=True)
    geometry = Column(
        Geometry(geometry_type="GEOMETRY", management=True), nullable=False
    )
    name = Column(String(150), nullable=False)
    geo_type_id = Column(Integer, nullable=False)
    geo_sub_type_id = Column(Integer, nullable=False)
    start = Column(TIMESTAMP)
    end = Column(TIMESTAMP)
    task_id = Column(Integer)
    subject_platform_id = Column(Integer)
    sensor_platform_id = Column(Integer)
    source_id = Column(Integer, nullable=False)
    privacy_id = Column(Integer)
    created_date = Column(DateTime, default=datetime.utcnow)


class Media(BaseSpatiaLite):
    __tablename__ = constants.MEDIA
    table_type = TableTypes.MEASUREMENT
    table_type_id = 34

    media_id = Column(Integer, primary_key=True)
    platform_id = Column(Integer)
    subject_id = Column(Integer)
    sensor_id = Column(Integer)
    location = Column(Geometry(geometry_type="POINT", management=True))
    elevation = Column(REAL)
    time = Column(TIMESTAMP)
    media_type_id = Column(Integer, nullable=False)
    url = Column(String(150), nullable=False)
    source_id = Column(Integer, nullable=False)
    privacy_id = Column(Integer)
    created_date = Column(DateTime, default=datetime.utcnow)
