"""Add CheckConstraints to ensure that empty strings cannot be set as the value for String fields that are used for uniqueness checks

Revision ID: 806cb8898cab
Revises:
Create Date: 2020-06-23 11:38:46.654985

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
from sqlalchemy.orm import declarative_base, deferred

from pepys_import.core.store import constants
from pepys_import.core.store.common_db import DatafileMixin, PlatformMixin, SensorMixin
from pepys_import.core.store.db_base import sqlite_naming_convention
from pepys_import.core.store.db_status import TableTypes
from pepys_import.utils.sqlalchemy_utils import UUIDType

# revision identifiers, used by Alembic.
revision = "806cb8898cab"
down_revision = "f2c9f346f305"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("Sensors", schema=None) as batch_op:
        batch_op.create_check_constraint("ck_Sensors_name", condition="name <> ''")

    with op.batch_alter_table("Platforms", schema=None) as batch_op:
        batch_op.create_check_constraint("ck_Platforms_name", condition="name <> ''")
        batch_op.create_check_constraint("ck_Platforms_identifier", condition="identifier <> ''")

    with op.batch_alter_table("Datafiles", schema=None) as batch_op:
        batch_op.create_check_constraint("ck_Datafiles_hash", condition="hash <> ''")


def downgrade():
    Metadata = MetaData(naming_convention=sqlite_naming_convention)
    BaseSpatiaLite = declarative_base(metadata=Metadata)

    class Sensor(BaseSpatiaLite, SensorMixin):
        __tablename__ = constants.SENSOR
        table_type = TableTypes.METADATA
        table_type_id = 2

        sensor_id = Column(UUIDType, primary_key=True, default=uuid4)
        name = Column(String(150), nullable=False)
        sensor_type_id = Column(
            UUIDType, ForeignKey("SensorTypes.sensor_type_id", onupdate="cascade"), nullable=False
        )
        host = Column(
            UUIDType, ForeignKey("Platforms.platform_id", onupdate="cascade"), nullable=False
        )
        privacy_id = Column(
            UUIDType, ForeignKey("Privacies.privacy_id", onupdate="cascade"), nullable=False
        )
        created_date = Column(DateTime, default=datetime.utcnow)

        __table_args__ = (
            UniqueConstraint("name", "host", name="uq_sensors_name_host"),
            CheckConstraint("name <> ''", name="ck_Sensors_name"),
        )

    class Platform(BaseSpatiaLite, PlatformMixin):
        __tablename__ = constants.PLATFORM
        table_type = TableTypes.METADATA
        table_type_id = 3

        platform_id = Column(UUIDType, primary_key=True, default=uuid4)
        name = Column(String(150), nullable=False)
        identifier = deferred(
            Column(
                String(10),
                nullable=False,
            )
        )
        trigraph = deferred(Column(String(3)))
        quadgraph = deferred(Column(String(4)))
        nationality_id = Column(
            UUIDType, ForeignKey("Nationalities.nationality_id", onupdate="cascade"), nullable=False
        )
        platform_type_id = Column(
            UUIDType,
            ForeignKey("PlatformTypes.platform_type_id", onupdate="cascade"),
            nullable=False,
        )
        privacy_id = Column(
            UUIDType, ForeignKey("Privacies.privacy_id", onupdate="cascade"), nullable=False
        )
        created_date = Column(DateTime, default=datetime.utcnow)

        __table_args__ = (
            UniqueConstraint(
                "name", "nationality_id", "identifier", name="uq_Platform_name_nat_identifier"
            ),
            CheckConstraint("name <> ''", name="ck_Platforms_name"),
            CheckConstraint("identifier <> ''", name="ck_Platforms_identifier"),
        )

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
            UUIDType,
            ForeignKey("DatafileTypes.datafile_type_id", onupdate="cascade"),
            nullable=False,
        )
        reference = Column(String(150))
        url = Column(String(150))
        size = deferred(Column(Integer, nullable=False))
        hash = deferred(Column(String(32), nullable=False))
        created_date = Column(DateTime, default=datetime.utcnow)

        __table_args__ = (
            UniqueConstraint("size", "hash", name="uq_Datafile_size_hash"),
            CheckConstraint("hash <> ''", name="ck_Datafiles_hash"),
        )

    # Sensor.__table__.append_constraint(CheckConstraint("name <> ''", name="ck_Sensors_name"))
    with op.batch_alter_table("Sensors", schema=None, copy_from=Sensor.__table__) as batch_op:
        batch_op.drop_constraint("ck_Sensors_name", type_="check")

    with op.batch_alter_table("Platforms", schema=None, copy_from=Platform.__table__) as batch_op:
        batch_op.drop_constraint("ck_Platforms_name", type_="check")
        batch_op.drop_constraint("ck_Platforms_identifier", type_="check")

    with op.batch_alter_table("Datafiles", schema=None, copy_from=Datafile.__table__) as batch_op:
        batch_op.drop_constraint("ck_Datafiles_hash", type_="check")
