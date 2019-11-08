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

    entry_id = Column(Integer, primary_key=True)
    table_type_id = Column(Integer, nullable=False)
    created_user = Column(Integer)


class TableType(base):
    __tablename__ = "TableTypes"
    table_type = TableTypes.METADATA

    table_type_id = Column(Integer, nullable=False, primary_key=True)
    name = Column(String(150))


class SensorType(base):
    __tablename__ = "SensorTypes"
    table_type = TableTypes.REFERENCE

    sensor_type_id = Column(Integer, primary_key=True)
    # TODO: does this, or other string limits need checking or validating on file import?
    name = Column(String(150))


class Sensor(base):
    __tablename__ = "Sensors"
    table_type = TableTypes.METADATA

    # These only needed for tables referenced by Entry table
    table_type_id = 2
    tableName = "Sensor"

    sensor_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    sensor_type_id = Column(Integer, nullable=False)
    platform_id = Column(Integer, nullable=False)


class PlatformType(base):
    __tablename__ = "PlatformTypes"
    table_type = TableTypes.REFERENCE

    platform_type_id = Column(Integer, primary_key=True)
    # TODO: does this, or other string limits need checking or validating on file import?
    name = Column(String(150))
    # TODO: add relationships and ForeignKey entries to auto-create Entry ids


class Platform(base):
    __tablename__ = "Platforms"
    table_type = TableTypes.METADATA

    # These only needed for tables referenced by Entry table
    table_type_id = 1
    tableName = "Platforms"

    platform_id = Column(Integer, primary_key=True)
    # TODO: does this, or other string limits need checking or validating on file import?
    name = Column(String(150))
    platform_type_id = Column(Integer, nullable=False)
    host_platform_id = Column(Integer)
    nationality_id = Column(Integer, nullable=False)
    # TODO: add relationships and ForeignKey entries to auto-create Entry ids

    privacy_id = Column(Integer, nullable=False)


class DatafileType(base):
    __tablename__ = "DatafileTypes"
    table_type = TableTypes.REFERENCE

    datafile_type_id = Column(Integer, primary_key=True)
    # TODO: does this, or other string limits need checking or validating on file import?
    name = Column(String(150), nullable=False)


class Datafile(base):
    __tablename__ = "Datafiles"
    table_type = TableTypes.METADATA

    # These only needed for tables referenced by Entry table
    table_type_id = 4
    tableName = "Datafiles"

    datafile_id = Column(Integer, primary_key=True)
    # TODO: does this, or other string limits need checking or validating on file import?
    simulated = Column(Boolean)
    reference = Column(String(150))
    url = Column(String(150))
    privacy_id = Column(Integer, nullable=False)
    datafile_type_id = Column(Integer, nullable=False)
    # TODO: add relationships and ForeignKey entries to auto-create Entry ids


class State(base):
    __tablename__ = "States"
    table_type = TableTypes.MEASUREMENT

    # These only needed for tables referenced by Entry table
    table_type_id = 3
    tableName = "States"

    state_id = Column(Integer, primary_key=True)
    time = Column(DATETIME, nullable=False)
    sensor_id = Column(Integer, nullable=False)
    # location = Column(Geometry(geometry_type='POINT', srid=4326))
    location = Column(String(150), nullable=False)
    heading = Column(REAL)
    course = Column(REAL)
    speed = Column(REAL)
    datafile_id = Column(Integer, nullable=False)
    privacy_id = Column(Integer)


class Nationality(base):
    __tablename__ = "Nationalities"
    table_type = TableTypes.REFERENCE

    nationality_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)


class Privacy(base):
    __tablename__ = "Privacies"
    table_type = TableTypes.REFERENCE

    privacy_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
