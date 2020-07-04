"""Add unique constraint for Platform

Revision ID: 4fb1c8780273
Revises: e752bda39400
Create Date: 2020-05-29 16:37:13.344722

"""
from datetime import datetime
from uuid import uuid4

from alembic import op
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import (  # used to defer fetching attributes unless it's specifically called
    deferred,
)

from pepys_import.core.store import constants
from pepys_import.core.store.common_db import (
    DatafileMixin,
    PlatformMixin,
    ReferenceRepr,
    SensorMixin,
)
from pepys_import.core.store.db_base import sqlite_naming_convention
from pepys_import.core.store.db_status import TableTypes
from pepys_import.utils.sqlalchemy_utils import UUIDType

Metadata = MetaData(naming_convention=sqlite_naming_convention)
BaseSpatiaLite = declarative_base(metadata=Metadata)


class Platform(BaseSpatiaLite, PlatformMixin):
    __tablename__ = constants.PLATFORM
    table_type = TableTypes.METADATA
    table_type_id = 3

    platform_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(
        String(150), CheckConstraint("name <> ''", name="ck_Platforms_name"), nullable=False
    )
    identifier = deferred(
        Column(
            String(10),
            CheckConstraint("identifier <> ''", name="ck_Platforms_identifier"),
            nullable=False,
        )
    )
    trigraph = deferred(Column(String(3)))
    quadgraph = deferred(Column(String(4)))
    nationality_id = Column(
        UUIDType, ForeignKey("Nationalities.nationality_id", onupdate="cascade"), nullable=False
    )
    platform_type_id = Column(
        UUIDType, ForeignKey("PlatformTypes.platform_type_id", onupdate="cascade"), nullable=False
    )
    privacy_id = Column(
        UUIDType, ForeignKey("Privacies.privacy_id", onupdate="cascade"), nullable=False
    )
    created_date = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "name", "nationality_id", "identifier", name="uq_Platform_name_nat_identifier"
        ),
    )


class SensorType(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.SENSOR_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 21

    sensor_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class Sensor(BaseSpatiaLite, SensorMixin):
    __tablename__ = constants.SENSOR
    table_type = TableTypes.METADATA
    table_type_id = 2

    sensor_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(
        String(150), CheckConstraint("name <> ''", name="ck_Sensors_name"), nullable=False
    )
    sensor_type_id = Column(
        UUIDType, ForeignKey("SensorTypes.sensor_type_id", onupdate="cascade"), nullable=False
    )
    host = Column(UUIDType, ForeignKey("Platforms.platform_id", onupdate="cascade"), nullable=False)
    privacy_id = Column(
        UUIDType, ForeignKey("Privacies.privacy_id", onupdate="cascade"), nullable=False
    )
    created_date = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("name", "host", name="uq_sensors_name_host"),)


class GeometryType(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.GEOMETRY_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 15

    geo_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class Datafile(BaseSpatiaLite, DatafileMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.measurements = dict()

    __tablename__ = constants.DATAFILE
    table_type = TableTypes.METADATA
    table_type_id = 6

    datafile_id = Column(UUIDType, primary_key=True, default=uuid4)
    simulated = deferred(Column(Boolean, nullable=False))
    privacy_id = Column(
        UUIDType, ForeignKey("Privacies.privacy_id", onupdate="cascade"), nullable=False
    )
    datafile_type_id = Column(
        UUIDType, ForeignKey("DatafileTypes.datafile_type_id", onupdate="cascade"), nullable=False
    )
    reference = Column(String(150))
    url = Column(String(150))
    size = deferred(Column(Integer, nullable=False))
    hash = deferred(
        Column(String(32), CheckConstraint("hash <> ''", name="ck_Datafiles_hash"), nullable=False)
    )
    created_date = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("size", "hash", name="uq_Datafile_size_hash"),)


class Nationality(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.NATIONALITY
    table_type = TableTypes.REFERENCE
    table_type_id = 14

    nationality_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    priority = Column(Integer)
    created_date = Column(DateTime, default=datetime.utcnow)


class DatafileType(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.DATAFILE_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 23

    datafile_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class PlatformType(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.PLATFORM_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 13

    platform_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class Privacy(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.PRIVACY
    table_type = TableTypes.REFERENCE
    table_type_id = 22

    privacy_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    level = Column(Integer, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class GeometrySubType(BaseSpatiaLite):
    __tablename__ = constants.GEOMETRY_SUBTYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 16

    geo_sub_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False)
    parent = Column(
        UUIDType, ForeignKey("GeometryTypes.geo_type_id", onupdate="cascade"), nullable=False
    )
    created_date = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("name", "parent", name="uq_GeometrySubType_name_parent"),)


# revision identifiers, used by Alembic.
revision = "4fb1c8780273"
down_revision = "b03fb305981b"
branch_labels = None
depends_on = None


def upgrade():
    UniqueConstraint(GeometrySubType.name, name="uq_GeometrySubTypes_name")
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("Datafiles", schema=None, copy_from=Datafile.__table__) as batch_op:
        batch_op.create_unique_constraint("uq_Datafile_size_hash", ["size", "hash"])

    with op.batch_alter_table(
        "GeometrySubTypes", schema=None, copy_from=GeometrySubType.__table__
    ) as batch_op:
        batch_op.create_unique_constraint("uq_GeometrySubType_name_parent", ["name", "parent"])
        batch_op.drop_constraint("uq_GeometrySubTypes_name", type_="unique")

    with op.batch_alter_table("Platforms", schema=None, copy_from=Platform.__table__) as batch_op:
        batch_op.create_unique_constraint(
            "uq_Platform_name_nat_identifier", ["name", "nationality_id", "identifier"]
        )

    with op.batch_alter_table("Sensors", schema=None, copy_from=Sensor.__table__) as batch_op:
        batch_op.create_unique_constraint("uq_sensors_name_host", ["name", "host"])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("Sensors", schema=None, copy_from=Sensor.__table__) as batch_op:
        batch_op.drop_constraint("uq_sensors_name_host", type_="unique")

    with op.batch_alter_table("Platforms", schema=None, copy_from=Platform.__table__) as batch_op:
        batch_op.drop_constraint("uq_Platform_name_nat_identifier", type_="unique")

    with op.batch_alter_table(
        "GeometrySubTypes", schema=None, copy_from=GeometrySubType.__table__
    ) as batch_op:
        batch_op.create_unique_constraint("uq_GeometrySubTypes_name", ["name"])
        batch_op.drop_constraint("uq_GeometrySubType_name_parent", type_="unique")

    with op.batch_alter_table("Datafiles", schema=None, copy_from=Datafile.__table__) as batch_op:
        batch_op.drop_constraint("uq_Datafile_size_hash", type_="unique")

    # ### end Alembic commands ###
