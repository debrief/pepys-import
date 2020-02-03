from sqlalchemy import Column, Integer, String, Boolean, FetchedValue
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import TIME
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION

from .db_base import base_postgres as base
from .db_status import TableTypes


def map_uuid_type(val):
    # postgres needs to map to string
    return str(val)


class Entry(base):
    __tablename__ = "Entry"
    table_type = TableTypes.METADATA

    entry_id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=FetchedValue()
    )
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
    table_type_id = 2  # Only needed for tables referenced by Entry table

    sensor_id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=FetchedValue()
    )
    name = Column(String(150), nullable=False)
    sensor_type_id = Column(UUID, nullable=False)
    platform_id = Column(UUID, nullable=False)


class Platforms(base):
    __tablename__ = "Platforms"
    table_type = TableTypes.METADATA
    table_type_id = 1  # Only needed for tables referenced by Entry table

    platform_id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=FetchedValue()
    )
    # TODO: does this, or other string limits need checking or validating on file import?
    name = Column(String(150))
    platform_type_id = Column(UUID(as_uuid=True), nullable=False)
    host_platform_id = Column(UUID(as_uuid=True))
    nationality_id = Column(UUID(as_uuid=True), nullable=False)
    # TODO: add relationships and ForeignKey entries to auto-create Entry ids

    privacy_id = Column(UUID(as_uuid=True), nullable=False)


class Tasks(base):
    pass


class Participants(base):
    pass


class Datafiles(base):
    __tablename__ = "Datafiles"
    table_type = TableTypes.METADATA
    table_type_id = 4  # Only needed for tables referenced by Entry table

    datafile_id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=FetchedValue()
    )
    # TODO: does this, or other string limits need checking or validating on file import?
    simulated = Column(Boolean)
    reference = Column(String(150))
    url = Column(String(150))
    privacy_id = Column(UUID(as_uuid=True), nullable=False)
    datafile_type_id = Column(UUID(as_uuid=True), nullable=False)
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
class PlatformType(base):
    __tablename__ = "PlatformTypes"
    table_type = TableTypes.REFERENCE

    platform_type_id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=FetchedValue()
    )
    # TODO: does this, or other string limits need checking or validating on file import?
    name = Column(String(150))
    # TODO: add relationships and ForeignKey entries to auto-create Entry ids


class Nationalities(base):
    __tablename__ = "Nationalities"
    table_type = TableTypes.REFERENCE

    nationality_id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=FetchedValue()
    )
    name = Column(String(150), nullable=False)


class GeometryTypes(base):
    pass


class GeometrySubTypes(base):
    pass


class Users(base):
    pass


class UnitTypes(base):
    pass


class ClassificationTypes(base):
    pass


class ContactTypes(base):
    pass


class SensorTypes(base):
    __tablename__ = "SensorTypes"
    table_type = TableTypes.REFERENCE

    sensor_type_id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=FetchedValue()
    )
    # TODO: does this, or other string limits need checking or validating on file import?
    name = Column(String(150))


class Privacies(base):
    __tablename__ = "Privacies"
    table_type = TableTypes.REFERENCE

    privacy_id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=FetchedValue()
    )
    name = Column(String(150), nullable=False)


class DatafileTypes(base):
    __tablename__ = "DatafileTypes"
    table_type = TableTypes.REFERENCE

    datafile_type_id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=FetchedValue()
    )
    # TODO: does this, or other string limits need checking or validating on file import?
    name = Column(String(150), nullable=False)


class MediaTypes(base):
    pass


class CommentTypes(base):
    pass


class CommodityTypes(base):
    pass


class ConfidenceLevels(base):
    pass


# Measurements Tables
class States(base):
    __tablename__ = "State"
    table_type = TableTypes.MEASUREMENT
    table_type_id = 3  # Only needed for tables referenced by Entry table

    state_id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=FetchedValue()
    )
    time = Column(TIME, nullable=False)
    sensor_id = Column(UUID(as_uuid=True), nullable=False)
    # location = Column(Geometry(geometry_type='POINT', srid=4326))
    location = Column(String(150), nullable=False)
    heading = Column(DOUBLE_PRECISION)
    course = Column(DOUBLE_PRECISION)
    speed = Column(DOUBLE_PRECISION)
    datafile_id = Column(UUID(as_uuid=True), nullable=False)
    privacy_id = Column(UUID(as_uuid=True))
