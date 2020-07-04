"""Add remark column

Revision ID: 0f716b0487aa
Revises: a18abf8b0488
Create Date: 2020-06-30 14:01:06.319095

"""
from datetime import datetime
from uuid import uuid4

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.sqlite import REAL, TIMESTAMP
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import (  # used to defer fetching attributes unless it's specifically called
    deferred,
    relationship,
)

from pepys_import.core.store import constants
from pepys_import.core.store.common_db import (
    ActivationMixin,
    CommentMixin,
    ContactMixin,
    DatafileMixin,
    ElevationPropertyMixin,
    GeometryMixin,
    LocationPropertyMixin,
    LogsHoldingMixin,
    MediaMixin,
    PlatformMixin,
    ReferenceRepr,
    SensorMixin,
    StateMixin,
    TaskMixin,
)
from pepys_import.core.store.db_base import sqlite_naming_convention
from pepys_import.core.store.db_status import TableTypes
from pepys_import.utils.sqlalchemy_utils import UUIDType

Metadata = MetaData(naming_convention=sqlite_naming_convention)
BaseSpatiaLite = declarative_base(metadata=Metadata)


class PlatformType(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.PLATFORM_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 13

    platform_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class State(BaseSpatiaLite, StateMixin, ElevationPropertyMixin, LocationPropertyMixin):
    __tablename__ = constants.STATE
    table_type = TableTypes.MEASUREMENT
    table_type_id = 28

    state_id = Column(UUIDType, primary_key=True, default=uuid4)
    time = Column(TIMESTAMP, nullable=False)
    sensor_id = Column(
        UUIDType, ForeignKey("Sensors.sensor_id", onupdate="cascade"), nullable=False
    )
    _location = deferred(
        Column(
            "location",
            Geometry(geometry_type="POINT", srid=4326, management=True, spatial_index=False),
        )
    )
    _elevation = deferred(Column("elevation", REAL))
    _heading = deferred(Column("heading", REAL))
    _course = deferred(Column("course", REAL))
    _speed = deferred(Column("speed", REAL))
    source_id = Column(
        UUIDType, ForeignKey("Datafiles.datafile_id", onupdate="cascade"), nullable=False
    )
    privacy_id = Column(UUIDType, ForeignKey("Privacies.privacy_id", onupdate="cascade"))
    remarks = Column(Text)
    created_date = Column(DateTime, default=datetime.utcnow)

    @declared_attr
    def platform(self):
        return relationship(
            "Platform",
            secondary=constants.SENSOR,
            primaryjoin="State.sensor_id == Sensor.sensor_id",
            secondaryjoin="Platform.platform_id == Sensor.host",
            lazy="joined",
            join_depth=1,
            uselist=False,
            viewonly=True,
        )

    @declared_attr
    def platform_name(self):
        return association_proxy("platform", "name")


class ContactType(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.CONTACT_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 20

    contact_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class Geometry1(BaseSpatiaLite, GeometryMixin):
    __tablename__ = constants.GEOMETRY
    table_type = TableTypes.MEASUREMENT
    table_type_id = 33

    geometry_id = Column(UUIDType, primary_key=True, default=uuid4)
    _geometry = Column(
        "geometry",
        Geometry(geometry_type="GEOMETRY", srid=4326, management=True, spatial_index=False),
        nullable=False,
    )
    name = Column(String(150))
    geo_type_id = Column(
        UUIDType, ForeignKey("GeometryTypes.geo_type_id", onupdate="cascade"), nullable=False
    )
    geo_sub_type_id = Column(
        UUIDType, ForeignKey("GeometrySubTypes.geo_sub_type_id", onupdate="cascade"), nullable=False
    )
    start = Column(TIMESTAMP)
    end = Column(TIMESTAMP)
    task_id = Column(UUIDType, ForeignKey("Tasks.task_id", onupdate="cascade"))
    subject_platform_id = Column(UUIDType, ForeignKey("Platforms.platform_id", onupdate="cascade"))
    sensor_platform_id = Column(UUIDType, ForeignKey("Platforms.platform_id", onupdate="cascade"))
    source_id = Column(
        UUIDType, ForeignKey("Datafiles.datafile_id", onupdate="cascade"), nullable=False
    )
    privacy_id = Column(UUIDType, ForeignKey("Privacies.privacy_id", onupdate="cascade"))
    remarks = Column(Text)
    created_date = Column(DateTime, default=datetime.utcnow)


class CommodityType(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.COMMODITY_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 26

    commodity_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class GeometryType(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.GEOMETRY_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 15

    geo_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class UnitType(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.UNIT_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 18

    unit_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
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


class Comment(BaseSpatiaLite, CommentMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sensor_name = "N/A"

    __tablename__ = constants.COMMENT
    table_type = TableTypes.MEASUREMENT
    table_type_id = 32

    comment_id = Column(UUIDType, primary_key=True, default=uuid4)
    platform_id = Column(UUIDType, ForeignKey("Platforms.platform_id", onupdate="cascade"))
    time = Column(TIMESTAMP, nullable=False)
    comment_type_id = Column(
        UUIDType, ForeignKey("CommentTypes.comment_type_id", onupdate="cascade"), nullable=False
    )
    content = Column(Text, nullable=False)
    source_id = Column(
        UUIDType, ForeignKey("Datafiles.datafile_id", onupdate="cascade"), nullable=False
    )
    privacy_id = Column(UUIDType, ForeignKey("Privacies.privacy_id", onupdate="cascade"))
    created_date = Column(DateTime, default=datetime.utcnow)


class ClassificationType(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.CLASSIFICATION_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 19

    class_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class Nationality(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.NATIONALITY
    table_type = TableTypes.REFERENCE
    table_type_id = 14

    nationality_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    priority = Column(Integer)
    created_date = Column(DateTime, default=datetime.utcnow)


class MediaType(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.MEDIA_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 24

    media_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class Contact(BaseSpatiaLite, ContactMixin, LocationPropertyMixin, ElevationPropertyMixin):
    __tablename__ = constants.CONTACT
    table_type = TableTypes.MEASUREMENT
    table_type_id = 29

    contact_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150))
    sensor_id = Column(
        UUIDType, ForeignKey("Sensors.sensor_id", onupdate="cascade"), nullable=False
    )
    time = Column(TIMESTAMP, nullable=False)
    _bearing = deferred(Column("bearing", REAL))
    _rel_bearing = deferred(Column("rel_bearing", REAL))
    _ambig_bearing = deferred(Column("ambig_bearing", REAL))
    _freq = deferred(Column("freq", REAL))
    _range = deferred(Column("range", REAL))
    _location = deferred(
        Column(
            "location",
            Geometry(geometry_type="POINT", srid=4326, management=True, spatial_index=False),
        )
    )
    _elevation = deferred(Column("elevation", REAL))
    _major = deferred(Column("major", REAL))
    _minor = deferred(Column("minor", REAL))
    _orientation = deferred(Column("orientation", REAL))
    classification = deferred(Column(UUIDType, ForeignKey("ClassificationTypes.class_type_id")))
    confidence = deferred(Column(UUIDType, ForeignKey("ConfidenceLevels.confidence_level_id")))
    contact_type = deferred(Column(UUIDType, ForeignKey("ContactTypes.contact_type_id")))
    _mla = deferred(Column("mla", REAL))
    _soa = deferred(Column("soa", REAL))
    track_number = Column(String(20))
    subject_id = Column(UUIDType, ForeignKey("Platforms.platform_id", onupdate="cascade"))
    source_id = Column(
        UUIDType, ForeignKey("Datafiles.datafile_id", onupdate="cascade"), nullable=False
    )
    privacy_id = Column(UUIDType, ForeignKey("Privacies.privacy_id", onupdate="cascade"))
    remarks = Column(Text)
    created_date = deferred(Column(DateTime, default=datetime.utcnow))

    @declared_attr
    def platform(self):
        return relationship(
            "Platform",
            secondary=constants.SENSOR,
            primaryjoin="Contact.sensor_id == Sensor.sensor_id",
            secondaryjoin="Platform.platform_id == Sensor.host",
            lazy="joined",
            join_depth=1,
            uselist=False,
            viewonly=True,
        )

    @declared_attr
    def platform_name(self):
        return association_proxy("platform", "name")


class SensorType(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.SENSOR_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 21

    sensor_type_id = Column(UUIDType, primary_key=True, default=uuid4)
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


class ConfidenceLevel(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.CONFIDENCE_LEVEL
    table_type = TableTypes.REFERENCE
    table_type_id = 27

    confidence_level_id = Column(UUIDType, primary_key=True, default=uuid4)
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


class Media(BaseSpatiaLite, MediaMixin, ElevationPropertyMixin, LocationPropertyMixin):
    __tablename__ = constants.MEDIA
    table_type = TableTypes.MEASUREMENT
    table_type_id = 34

    media_id = Column(UUIDType, primary_key=True, default=uuid4)
    platform_id = Column(UUIDType, ForeignKey("Platforms.platform_id", onupdate="cascade"))
    subject_id = Column(UUIDType, ForeignKey("Platforms.platform_id", onupdate="cascade"))
    sensor_id = Column(UUIDType, ForeignKey("Sensors.sensor_id", onupdate="cascade"))
    _location = deferred(
        Column(
            "location",
            Geometry(geometry_type="POINT", srid=4326, management=True, spatial_index=False),
        )
    )
    _elevation = deferred(Column("elevation", REAL))
    time = Column(TIMESTAMP)
    media_type_id = Column(
        UUIDType, ForeignKey("MediaTypes.media_type_id", onupdate="cascade"), nullable=False
    )
    url = deferred(Column(String(150), nullable=False))
    source_id = Column(
        UUIDType, ForeignKey("Datafiles.datafile_id", onupdate="cascade"), nullable=False
    )
    privacy_id = Column(UUIDType, ForeignKey("Privacies.privacy_id", onupdate="cascade"))
    remarks = Column(Text)
    created_date = Column(DateTime, default=datetime.utcnow)


class Activation(BaseSpatiaLite, ActivationMixin):
    __tablename__ = constants.ACTIVATION
    table_type = TableTypes.MEASUREMENT
    table_type_id = 30

    activation_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150))
    sensor_id = Column(
        UUIDType, ForeignKey("Sensors.sensor_id", onupdate="cascade"), nullable=False
    )
    start = deferred(Column(TIMESTAMP))
    end = deferred(Column(TIMESTAMP))
    _min_range = deferred(Column("min_range", REAL))
    _max_range = deferred(Column("max_range", REAL))
    _left_arc = deferred(Column("left_arc", REAL))
    _right_arc = deferred(Column("right_arc", REAL))
    source_id = Column(
        UUIDType, ForeignKey("Datafiles.datafile_id", onupdate="cascade"), nullable=False
    )
    privacy_id = Column(UUIDType, ForeignKey("Privacies.privacy_id", onupdate="cascade"))
    remarks = Column(Text)
    created_date = Column(DateTime, default=datetime.utcnow)


class Task(BaseSpatiaLite, TaskMixin):
    __tablename__ = constants.TASK
    table_type = TableTypes.METADATA
    table_type_id = 4

    task_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False)
    parent_id = Column(UUIDType, ForeignKey("Tasks.task_id", onupdate="cascade"), nullable=False)
    start = Column(TIMESTAMP, nullable=False)
    end = Column(TIMESTAMP, nullable=False)
    environment = deferred(Column(String(150)))
    location = deferred(Column(String(150)))
    privacy_id = Column(
        UUIDType, ForeignKey("Privacies.privacy_id", onupdate="cascade"), nullable=False
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class DatafileType(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.DATAFILE_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 23

    datafile_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class LogsHolding(BaseSpatiaLite, LogsHoldingMixin):
    __tablename__ = constants.LOGS_HOLDING
    table_type = TableTypes.MEASUREMENT
    table_type_id = 31

    logs_holding_id = Column(UUIDType, primary_key=True, default=uuid4)
    time = Column(TIMESTAMP, nullable=False)
    commodity_id = Column(
        UUIDType, ForeignKey("CommodityTypes.commodity_type_id", onupdate="cascade"), nullable=False
    )
    quantity = Column(REAL, nullable=False)
    unit_type_id = Column(
        UUIDType, ForeignKey("UnitTypes.unit_type_id", onupdate="cascade"), nullable=False
    )
    platform_id = Column(
        UUIDType, ForeignKey("Platforms.platform_id", onupdate="cascade"), nullable=False
    )
    comment = Column(Text(), nullable=False)
    source_id = Column(
        UUIDType, ForeignKey("Datafiles.datafile_id", onupdate="cascade"), nullable=False
    )
    privacy_id = Column(UUIDType, ForeignKey("Privacies.privacy_id", onupdate="cascade"))
    created_date = Column(DateTime, default=datetime.utcnow)


class CommentType(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.COMMENT_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 25

    comment_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


# revision identifiers, used by Alembic.
revision = "0f716b0487aa"
down_revision = "a18abf8b0488"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table(
        "Activations", schema=None, copy_from=Activation.__table__
    ) as batch_op:
        batch_op.add_column(sa.Column("remarks", sa.Text(), nullable=True))

    with op.batch_alter_table("Comments", schema=None, copy_from=Comment.__table__) as batch_op:
        batch_op.alter_column(
            "content",
            existing_type=sa.VARCHAR(length=150),
            type_=sa.Text(),
            existing_nullable=False,
        )

    with op.batch_alter_table("Contacts", schema=None, copy_from=Contact.__table__) as batch_op:
        batch_op.add_column(sa.Column("remarks", sa.Text(), nullable=True))

    with op.batch_alter_table("Geometries", schema=None, copy_from=Geometry1.__table__) as batch_op:
        batch_op.add_column(sa.Column("remarks", sa.Text(), nullable=True))

    with op.batch_alter_table(
        "LogsHoldings", schema=None, copy_from=LogsHolding.__table__
    ) as batch_op:
        batch_op.alter_column(
            "comment",
            existing_type=sa.VARCHAR(length=150),
            type_=sa.Text(),
            existing_nullable=False,
        )

    with op.batch_alter_table("Media", schema=None, copy_from=Media.__table__) as batch_op:
        batch_op.add_column(sa.Column("remarks", sa.Text(), nullable=True))

    with op.batch_alter_table("States", schema=None, copy_from=State.__table__) as batch_op:
        batch_op.add_column(sa.Column("remarks", sa.Text(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("States", schema=None, copy_from=State.__table__) as batch_op:
        batch_op.drop_column("remarks")

    with op.batch_alter_table("Media", schema=None, copy_from=Media.__table__) as batch_op:
        batch_op.drop_column("remarks")

    with op.batch_alter_table(
        "LogsHoldings", schema=None, copy_from=LogsHolding.__table__
    ) as batch_op:
        batch_op.alter_column(
            "comment",
            existing_type=sa.Text(),
            type_=sa.VARCHAR(length=150),
            existing_nullable=False,
        )

    with op.batch_alter_table("Geometries", schema=None, copy_from=Geometry1.__table__) as batch_op:
        batch_op.drop_column("remarks")

    with op.batch_alter_table("Contacts", schema=None, copy_from=Contact.__table__) as batch_op:
        batch_op.drop_column("remarks")

    with op.batch_alter_table("Comments", schema=None, copy_from=Comment.__table__) as batch_op:
        batch_op.alter_column(
            "content",
            existing_type=sa.Text(),
            type_=sa.VARCHAR(length=150),
            existing_nullable=False,
        )

    with op.batch_alter_table(
        "Activations", schema=None, copy_from=Activation.__table__
    ) as batch_op:
        batch_op.drop_column("remarks")

    # ### end Alembic commands ###
