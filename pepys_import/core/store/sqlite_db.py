from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.dialects.sqlite import DATETIME
from sqlalchemy.dialects.sqlite import REAL
import uuid

from .db_base import base_sqlite as base
from .db_status import TableTypes
from .uuid import UUID


def map_uuid_type(val):
    # sql does not need to map to string
    return val


class Entry(base):
    __tablename__ = "Entry"
    table_type = TableTypes.METADATA

    entry_id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    table_type_id = Column(Integer, nullable=False)
    created_user = Column(Integer)


class TableType(base):
    __tablename__ = "TableTypes"
    table_type = TableTypes.METADATA

    table_type_id = Column(Integer, nullable=False, primary_key=True)
    name = Column(String(150))


# Metadata Tables
class HostedBy(base):
    pass


class Sensors(base):
    __tablename__ = "Sensors"
    table_type = TableTypes.METADATA

    # These only needed for tables referenced by Entry table
    table_type_id = 2
    tableName = "Sensor"

    sensor_id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(150), nullable=False)
    sensor_type_id = Column(UUID, nullable=False)
    platform_id = Column(UUID, nullable=False)


class Platforms(base):
    __tablename__ = "Platforms"
    table_type = TableTypes.METADATA

    # These only needed for tables referenced by Entry table
    table_type_id = 1
    tableName = "Platforms"

    platform_id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    # TODO: does this, or other string limits need checking or validating on file import?
    name = Column(String(150))
    platform_type_id = Column(UUID(), nullable=False)
    host_platform_id = Column(UUID())
    nationality_id = Column(UUID(), nullable=False)
    # TODO: add relationships and ForeignKey entries to auto-create Entry ids

    privacy_id = Column(UUID(), nullable=False)


class Tasks(base):
    pass


class Participants(base):
    pass


class Datafiles(base):
    __tablename__ = "Datafiles"
    table_type = TableTypes.METADATA

    # These only needed for tables referenced by Entry table
    table_type_id = 4
    tableName = "Datafiles"

    datafile_id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    # TODO: does this, or other string limits need checking or validating on file import?
    simulated = Column(Boolean)
    reference = Column(String(150))
    url = Column(String(150))
    privacy_id = Column(UUID(), nullable=False)
    datafile_type_id = Column(UUID(), nullable=False)
    # TODO: add relationships and ForeignKey entries to auto-create Entry ids


class Synonyms(base):
    pass


class Changes(base):
    pass


class Log(base):
    pass


class Extractions(base):
    pass


class Tags(base):
    pass


class TaggedItems(base):
    pass


# Reference Tables
class PlatformTypes(base):
    __tablename__ = "PlatformTypes"
    table_type = TableTypes.REFERENCE

    platform_type_id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    # TODO: does this, or other string limits need checking or validating on file import?
    name = Column(String(150))
    # TODO: add relationships and ForeignKey entries to auto-create Entry ids


class Nationalities(base):
    __tablename__ = "Nationalities"
    table_type = TableTypes.REFERENCE

    nationality_id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(150), nullable=False)


class GeometryTypes(base):
    __tablename__ = "GeometryTypes"
    table_type = TableTypes.REFERENCE

    geometry_type_id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(150), nullable=False)


class GeometrySubTypes(base):
    __tablename__ = "GeometrySubTypes"
    table_type = TableTypes.REFERENCE

    geometry_sub_type_id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(150), nullable=False)
    parent = Column(UUID, nullable=False)


class Users(base):
    __tablename__ = "Users"
    table_type = TableTypes.REFERENCE

    user_id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(150), nullable=False)


class UnitTypes(base):
    __tablename__ = "UnitTypes"
    table_type = TableTypes.REFERENCE

    unit_type_id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(150), nullable=False)


class ClassificationTypes(base):
    __tablename__ = "ClassificationTypes"
    table_type = TableTypes.REFERENCE

    classification_type_id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    class_type = Column(String(150), nullable=False)


class ContactTypes(base):
    __tablename__ = "ContactTypes"
    table_type = TableTypes.REFERENCE

    contact_type_id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    contact_type_name = Column(String(150), nullable=False)


class SensorTypes(base):
    __tablename__ = "SensorTypes"
    table_type = TableTypes.REFERENCE

    sensor_type_id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    # TODO: does this, or other string limits need checking or validating on file import?
    name = Column(String(150))


class Privacies(base):
    __tablename__ = "Privacies"
    table_type = TableTypes.REFERENCE

    privacy_id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(150), nullable=False)


class DatafileTypes(base):
    __tablename__ = "DatafileTypes"
    table_type = TableTypes.REFERENCE

    datafile_type_id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    # TODO: does this, or other string limits need checking or validating on file import?
    name = Column(String(150), nullable=False)


class MediaTypes(base):
    __tablename__ = "MediaTypes"
    table_type = TableTypes.REFERENCE

    media_type_id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(150), nullable=False)


class CommentTypes(base):
    __tablename__ = "CommentTypes"
    table_type = TableTypes.REFERENCE

    comment_type_id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(150), nullable=False)


class CommodityTypes(base):
    __tablename__ = "CommodityTypes"
    table_type = TableTypes.REFERENCE

    commodity_type_id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(150), nullable=False)


class ConfidenceLevels(base):
    __tablename__ = "ConfidenceLevels"
    table_type = TableTypes.REFERENCE

    confidence_level_id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    level = Column(String(150), nullable=False)


# Measurements Tables
class States(base):
    __tablename__ = "State"
    table_type = TableTypes.MEASUREMENT

    # These only needed for tables referenced by Entry table
    table_type_id = 3
    tableName = "State"

    state_id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    time = Column(DATETIME, nullable=False)
    sensor_id = Column(UUID(), nullable=False)
    # location = Column(Geometry(geometry_type='POINT', srid=4326))
    location = Column(String(150), nullable=False)
    heading = Column(REAL)
    course = Column(REAL)
    speed = Column(REAL)
    datafile_id = Column(UUID(), nullable=False)
    privacy_id = Column(UUID())


class Contacts(base):
    pass


class Activations(base):
    pass


class LogsHoldings(base):
    pass


class Comments(base):
    pass


class Geometries(base):
    pass


class Media(base):
    pass
