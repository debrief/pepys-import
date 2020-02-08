from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DATE, DateTime
from sqlalchemy.dialects.sqlite import DATETIME, TIMESTAMP, REAL

from geoalchemy2 import Geography, Geometry

from .db_base import base_sqlite as base
from .db_status import TableTypes


def map_uuid_type(val):
    # sql does not need to map to string
    return val


class Entry(base):
    __tablename__ = "Entry"
    table_type = TableTypes.METADATA

    entry_id = Column(Integer, primary_key=True)
    table_type_id = Column(Integer, nullable=False)
    created_user = Column(Integer)
    created_date = Column(DateTime, default=datetime.utcnow)


class TableType(base):
    __tablename__ = "TableTypes"
    table_type = TableTypes.METADATA

    table_type_id = Column(Integer, nullable=False, primary_key=True)
    name = Column(String(150))
    created_date = Column(DateTime, default=datetime.utcnow)


# Metadata Tables
class HostedBy(base):
    __tablename__ = "HostedBy"
    table_type = TableTypes.METADATA
    table_type_id = 1
    table_name = "HostedBy"

    hosted_by_id = Column(Integer, primary_key=True)
    subject_id = Column(Integer, nullable=False)
    host_id = Column(Integer, nullable=False)
    hosted_from = Column(DATE, nullable=False)
    host_to = Column(DATE, nullable=False)
    privacy_id = Column(Integer, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Sensors(base):
    __tablename__ = "Sensors"
    table_type = TableTypes.METADATA
    table_type_id = 2
    table_name = "Sensors"

    sensor_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    sensor_type_id = Column(Integer, nullable=False)
    platform_id = Column(Integer, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Platforms(base):
    __tablename__ = "Platforms"
    table_type = TableTypes.METADATA
    table_type_id = 3
    table_name = "Platforms"

    platform_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    nationality_id = Column(Integer, nullable=False)
    platform_type_id = Column(Integer, nullable=False)
    privacy_id = Column(Integer, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Tasks(base):
    __tablename__ = "Tasks"
    table_type = TableTypes.METADATA
    table_type_id = 4
    table_name = "Tasks"

    task_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    parent_id = Column(Integer, nullable=False)
    start = Column(TIMESTAMP, nullable=False)
    end = Column(TIMESTAMP, nullable=False)
    environment = Column(String(150))
    location = Column(String(150))
    privacy_id = Column(Integer, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Participants(base):
    __tablename__ = "Participants"
    table_type = TableTypes.METADATA
    table_type_id = 5
    table_name = "Participants"

    participant_id = Column(Integer, primary_key=True)
    platform_id = Column(Integer, nullable=False)
    task_id = Column(Integer, nullable=False)
    start = Column(TIMESTAMP)
    end = Column(TIMESTAMP)
    force = Column(String(150))
    privacy_id = Column(Integer, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Datafiles(base):
    __tablename__ = "Datafiles"
    table_type = TableTypes.METADATA
    table_type_id = 6
    table_name = "Datafiles"

    datafile_id = Column(Integer, primary_key=True)
    simulated = Column(Boolean, nullable=False)
    privacy_id = Column(Integer, nullable=False)
    datafile_type_id = Column(Integer, nullable=False)
    reference = Column(String(150))
    url = Column(String(150))
    created_date = Column(DateTime, default=datetime.utcnow)


class Synonyms(base):
    __tablename__ = "Synonyms"
    table_type = TableTypes.METADATA
    table_type_id = 7
    table_name = "Synonyms"

    synonym_id = Column(Integer, primary_key=True)
    table = Column(String(150), nullable=False)
    synonym = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Changes(base):
    __tablename__ = "Changes"
    table_type = TableTypes.METADATA
    table_type_id = 8
    table_name = "Changes"

    change_id = Column(Integer, primary_key=True)
    user = Column(String(150), nullable=False)
    modified = Column(DATE, nullable=False)
    reason = Column(String(500), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Logs(base):
    __tablename__ = "Logs"
    table_type = TableTypes.METADATA
    table_type_id = 9
    table_name = "Log"

    log_id = Column(Integer, primary_key=True)
    table = Column(String(150), nullable=False)
    id = Column(Integer, nullable=False)
    field = Column(String(150), nullable=False)
    new_value = Column(String(150), nullable=False)
    change_id = Column(Integer, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Extractions(base):
    __tablename__ = "Extractions"
    table_type = TableTypes.METADATA
    table_type_id = 10
    table_name = "Extractions"

    extraction_id = Column(Integer, primary_key=True)
    table = Column(String(150), nullable=False)
    field = Column(String(150), nullable=False)
    chars = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Tags(base):
    __tablename__ = "Tags"
    table_type = TableTypes.METADATA
    table_type_id = 11
    table_name = "Tags"

    tag_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class TaggedItems(base):
    __tablename__ = "TaggedItems"
    table_type = TableTypes.METADATA
    table_type_id = 12
    table_name = "TaggedItems"

    tagged_item_id = Column(Integer, primary_key=True)
    tag_id = Column(Integer, nullable=False)
    item_id = Column(Integer, nullable=False)
    tagged_by_id = Column(Integer, nullable=False)
    private = Column(Boolean, nullable=False)
    tagged_on = Column(DATE, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


# Reference Tables
class PlatformTypes(base):
    __tablename__ = "PlatformTypes"
    table_type = TableTypes.REFERENCE
    table_name = "PlatformTypes"
    table_type_id = 13

    platform_type_id = Column(Integer, primary_key=True)
    name = Column(String(150))
    created_date = Column(DateTime, default=datetime.utcnow)


class Nationalities(base):
    __tablename__ = "Nationalities"
    table_type = TableTypes.REFERENCE
    table_name = "Nationalities"
    table_type_id = 14

    nationality_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class GeometryTypes(base):
    __tablename__ = "GeometryTypes"
    table_type = TableTypes.REFERENCE
    table_name = "GeometryTypes"
    table_type_id = 15

    geo_type_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class GeometrySubTypes(base):
    __tablename__ = "GeometrySubTypes"
    table_type = TableTypes.REFERENCE
    table_name = "GeometrySubTypes"
    table_type_id = 16

    geo_sub_type_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    parent = Column(Integer, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Users(base):
    __tablename__ = "Users"
    table_type = TableTypes.REFERENCE
    table_name = "Users"
    table_type_id = 17

    user_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class UnitTypes(base):
    __tablename__ = "UnitTypes"
    table_type = TableTypes.REFERENCE
    table_name = "UnitTypes"
    table_type_id = 18

    unit_type_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class ClassificationTypes(base):
    __tablename__ = "ClassificationTypes"
    table_type = TableTypes.REFERENCE
    table_name = "ClassificationTypes"
    table_type_id = 19

    class_type_id = Column(Integer, primary_key=True)
    class_type = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class ContactTypes(base):
    __tablename__ = "ContactTypes"
    table_type = TableTypes.REFERENCE
    table_name = "ContactTypes"
    table_type_id = 20

    contact_type_id = Column(Integer, primary_key=True)
    contact_type = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class SensorTypes(base):
    __tablename__ = "SensorTypes"
    table_type = TableTypes.REFERENCE
    table_name = "SensorTypes"
    table_type_id = 21

    sensor_type_id = Column(Integer, primary_key=True)
    name = Column(String(150))
    created_date = Column(DateTime, default=datetime.utcnow)


class Privacies(base):
    __tablename__ = "Privacies"
    table_type = TableTypes.REFERENCE
    table_name = "Privacies"
    table_type_id = 22

    privacy_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class DatafileTypes(base):
    __tablename__ = "DatafileTypes"
    table_type = TableTypes.REFERENCE
    table_name = "DatafileTypes"
    table_type_id = 23

    datafile_type_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class MediaTypes(base):
    __tablename__ = "MediaTypes"
    table_type = TableTypes.REFERENCE
    table_name = "MediaTypes"
    table_type_id = 24

    media_type_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class CommentTypes(base):
    __tablename__ = "CommentTypes"
    table_type = TableTypes.REFERENCE
    table_name = "CommentTypes"
    table_type_id = 25

    comment_type_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class CommodityTypes(base):
    __tablename__ = "CommodityTypes"
    table_type = TableTypes.REFERENCE
    table_name = "CommodityTypes"
    table_type_id = 26

    commodity_type_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class ConfidenceLevels(base):
    __tablename__ = "ConfidenceLevels"
    table_type = TableTypes.REFERENCE
    table_name = "ConfidenceLevels"
    table_type_id = 27

    confidence_level_id = Column(Integer, primary_key=True)
    level = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


# Measurements Tables
class States(base):
    __tablename__ = "States"
    table_type = TableTypes.MEASUREMENT
    table_type_id = 28
    table_name = "States"

    state_id = Column(Integer, primary_key=True)
    time = Column(DATETIME, nullable=False)
    sensor_id = Column(Integer, nullable=False)
    location = Column(Geometry(geometry_type="POINT", management=True))
    heading = Column(REAL)
    course = Column(REAL)
    speed = Column(REAL)
    source_id = Column(Integer, nullable=False)
    privacy_id = Column(Integer)
    created_date = Column(DateTime, default=datetime.utcnow)


class Contacts(base):
    __tablename__ = "Contacts"
    table_type = TableTypes.MEASUREMENT
    table_type_id = 29
    table_name = "Contacts"

    contact_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    sensor_id = Column(Integer, nullable=False)
    time = Column(TIMESTAMP, nullable=False)
    bearing = Column(REAL)
    rel_bearing = Column(REAL)
    freq = Column(REAL)
    location = Column(Geometry(geometry_type="POINT", management=True))
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


class Activations(base):
    __tablename__ = "Activations"
    table_type = TableTypes.MEASUREMENT
    table_type_id = 30
    table_name = "Activations"

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


class LogsHoldings(base):
    __tablename__ = "LogsHoldings"
    table_type = TableTypes.MEASUREMENT
    table_type_id = 31
    table_name = "LogsHoldings"

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


class Comments(base):
    __tablename__ = "Comments"
    table_type = TableTypes.MEASUREMENT
    table_type_id = 32
    table_name = "Comments"

    comment_id = Column(Integer, primary_key=True)
    platform_id = Column(Integer)
    time = Column(TIMESTAMP, nullable=False)
    comment_type_id = Column(Integer, nullable=False)
    content = Column(String(150), nullable=False)
    source_id = Column(Integer, nullable=False)
    privacy_id = Column(Integer)
    created_date = Column(DateTime, default=datetime.utcnow)


class Geometries(base):
    __tablename__ = "Geometries"
    table_type = TableTypes.MEASUREMENT
    table_type_id = 33
    table_name = "Geometries"

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


class Media(base):
    __tablename__ = "Media"
    table_type = TableTypes.MEASUREMENT
    table_type_id = 34
    table_name = "Media"

    media_id = Column(Integer, primary_key=True)
    platform_id = Column(Integer)
    subject_id = Column(Integer)
    sensor_id = Column(Integer)
    location = Column(Geometry(geometry_type="POINT", management=True))
    time = Column(TIMESTAMP)
    media_type_id = Column(Integer, nullable=False)
    url = Column(String(150), nullable=False)
    source_id = Column(Integer, nullable=False)
    privacy_id = Column(Integer)
    created_date = Column(DateTime, default=datetime.utcnow)
