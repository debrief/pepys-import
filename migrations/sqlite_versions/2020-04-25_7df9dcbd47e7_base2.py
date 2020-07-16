"""base2

Revision ID: 7df9dcbd47e7
Revises: bcff0ccb4fbd
Create Date: 2020-04-23 12:26:51.084226

"""

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, MetaData, String
from sqlalchemy.dialects.sqlite import TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import (  # used to defer fetching attributes unless it's specifically called
    deferred,
)

from pepys_import.core.store import constants
from pepys_import.core.store.common_db import DatafileMixin, GeometryMixin, PlatformMixin, TaskMixin
from pepys_import.core.store.db_base import sqlite_naming_convention
from pepys_import.core.store.db_status import TableTypes
from pepys_import.utils.sqlalchemy_utils import UUIDType

Metadata = MetaData(naming_convention=sqlite_naming_convention)
BaseSpatiaLite = declarative_base(metadata=Metadata)


class Datafile(BaseSpatiaLite, DatafileMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.measurements = dict()

    __tablename__ = constants.DATAFILE
    table_type = TableTypes.METADATA
    table_type_id = 6

    datafile_id = Column(UUIDType, primary_key=True, default=uuid4)
    simulated = deferred(Column(Boolean, nullable=False))
    privacy_id = Column(UUIDType, ForeignKey("Privacies.privacy_id"), nullable=False)
    datafile_type_id = Column(
        UUIDType, ForeignKey("DatafileTypes.datafile_type_id"), nullable=False
    )
    reference = Column(String(150))
    url = Column(String(150))
    size = deferred(Column(Integer, nullable=False))
    hash = deferred(Column(String(32), nullable=False))
    created_date = Column(DateTime, default=datetime.utcnow)


class PlatformType(BaseSpatiaLite):
    __tablename__ = constants.PLATFORM_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 13

    platform_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class Task(BaseSpatiaLite, TaskMixin):
    __tablename__ = constants.TASK
    table_type = TableTypes.METADATA
    table_type_id = 4

    task_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False)
    parent_id = Column(UUIDType, ForeignKey("Tasks.task_id"), nullable=False)
    start = Column(TIMESTAMP, nullable=False)
    end = Column(TIMESTAMP, nullable=False)
    environment = deferred(Column(String(150)))
    location = deferred(Column(String(150)))
    privacy_id = Column(UUIDType, ForeignKey("Privacies.privacy_id"), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Privacy(BaseSpatiaLite):
    __tablename__ = constants.PRIVACY
    table_type = TableTypes.REFERENCE
    table_type_id = 22

    privacy_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class GeometrySubType(BaseSpatiaLite):
    __tablename__ = constants.GEOMETRY_SUBTYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 16

    geo_sub_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    parent = Column(
        UUIDType, ForeignKey("GeometryTypes.geo_type_id", onupdate="cascade"), nullable=False
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class GeometryType(BaseSpatiaLite):
    __tablename__ = constants.GEOMETRY_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 15

    geo_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class Nationality(BaseSpatiaLite):
    __tablename__ = constants.NATIONALITY
    table_type = TableTypes.REFERENCE
    table_type_id = 14

    nationality_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class Geometry1(BaseSpatiaLite, GeometryMixin):
    __tablename__ = constants.GEOMETRY
    table_type = TableTypes.MEASUREMENT
    table_type_id = 33

    geometry_id = Column(UUIDType, primary_key=True, default=uuid4)
    geometry = deferred(
        Column(
            Geometry(geometry_type="GEOMETRY", management=True, spatial_index=False), nullable=False
        )
    )
    name = Column(String(150), nullable=False)
    geo_type_id = Column(UUIDType, ForeignKey("GeometryTypes.geo_type_id"), nullable=False)
    geo_sub_type_id = Column(
        UUIDType, ForeignKey("GeometrySubTypes.geo_sub_type_id"), nullable=False
    )
    start = Column(TIMESTAMP)
    end = Column(TIMESTAMP)
    task_id = Column(UUIDType, ForeignKey("Tasks.task_id"))
    subject_platform_id = Column(UUIDType, ForeignKey("Platforms.platform_id"))
    sensor_platform_id = Column(UUIDType, ForeignKey("Platforms.platform_id"))
    source_id = Column(UUIDType, ForeignKey("Datafiles.datafile_id"), nullable=False)
    privacy_id = Column(UUIDType, ForeignKey("Privacies.privacy_id"))
    created_date = Column(DateTime, default=datetime.utcnow)


class Platform(BaseSpatiaLite, PlatformMixin):
    __tablename__ = constants.PLATFORM
    table_type = TableTypes.METADATA
    table_type_id = 3

    platform_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False)
    pennant = deferred(Column(String(10), nullable=False))
    trigraph = deferred(Column(String(3)))
    quadgraph = deferred(Column(String(4)))
    nationality_id = Column(UUIDType, ForeignKey("Nationalities.nationality_id"), nullable=False)
    platform_type_id = Column(
        UUIDType, ForeignKey("PlatformTypes.platform_type_id"), nullable=False
    )
    privacy_id = Column(UUIDType, ForeignKey("Privacies.privacy_id"), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class DatafileType(BaseSpatiaLite):
    __tablename__ = constants.DATAFILE_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 23

    datafile_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


# revision identifiers, used by Alembic.
revision = "7df9dcbd47e7"
down_revision = "bcff0ccb4fbd"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("Geometries", schema=None) as batch_op:
        batch_op.alter_column("geometry", existing_type=sa.NUMERIC(), nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("Geometries", schema=None) as batch_op:
        batch_op.alter_column("geometry", existing_type=sa.NUMERIC(), nullable=True)

    # ### end Alembic commands ###
