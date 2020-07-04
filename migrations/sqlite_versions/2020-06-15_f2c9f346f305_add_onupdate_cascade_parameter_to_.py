"""Add onupdate=cascade parameter to foreign key fields

Revision ID: f2c9f346f305
Revises: 4fb1c8780273
Create Date: 2020-06-15 12:57:28.809322

"""
from datetime import datetime
from uuid import uuid4

import geoalchemy2
import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy import (
    DATE,
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
    HostedByMixin,
    LocationPropertyMixin,
    LogMixin,
    LogsHoldingMixin,
    MediaMixin,
    ParticipantMixin,
    PlatformMixin,
    ReferenceRepr,
    SensorMixin,
    StateMixin,
    TaggedItemMixin,
    TaskMixin,
)
from pepys_import.core.store.db_base import sqlite_naming_convention
from pepys_import.core.store.db_status import TableTypes
from pepys_import.utils.sqlalchemy_utils import UUIDType

Metadata = MetaData(naming_convention=sqlite_naming_convention)
BaseSpatiaLite = declarative_base(metadata=Metadata)


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


class UnitType(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.UNIT_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 18

    unit_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class User(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.USER
    table_type = TableTypes.REFERENCE
    table_type_id = 17

    user_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class SensorType(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.SENSOR_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 21

    sensor_type_id = Column(UUIDType, primary_key=True, default=uuid4)
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


class GeometryType(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.GEOMETRY_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 15

    geo_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class ContactType(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.CONTACT_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 20

    contact_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class Tag(BaseSpatiaLite):
    __tablename__ = constants.TAG
    table_type = TableTypes.METADATA
    table_type_id = 11

    tag_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False)
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


class HostedBy(BaseSpatiaLite, HostedByMixin):
    __tablename__ = constants.HOSTED_BY
    table_type = TableTypes.METADATA
    table_type_id = 1

    hosted_by_id = Column(UUIDType, primary_key=True, default=uuid4)
    subject_id = Column(
        UUIDType, ForeignKey("Platforms.platform_id", onupdate="cascade"), nullable=False
    )
    host_id = Column(
        UUIDType, ForeignKey("Platforms.platform_id", onupdate="cascade"), nullable=False
    )
    hosted_from = Column(DATE, nullable=False)
    host_to = Column(DATE, nullable=False)
    privacy_id = Column(
        Integer, ForeignKey("Privacies.privacy_id", onupdate="cascade"), nullable=False
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class ClassificationType(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.CLASSIFICATION_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 19

    class_type_id = Column(UUIDType, primary_key=True, default=uuid4)
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


class Log(BaseSpatiaLite, LogMixin):
    __tablename__ = constants.LOG
    table_type = TableTypes.METADATA
    table_type_id = 9

    log_id = Column(UUIDType, primary_key=True, default=uuid4)
    table = Column(String(150), nullable=False)
    id = Column(UUIDType, nullable=False)
    field = Column(String(150))
    new_value = Column(String(150))
    change_id = Column(
        UUIDType, ForeignKey("Changes.change_id", onupdate="cascade"), nullable=False
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class CommodityType(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.COMMODITY_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 26

    commodity_type_id = Column(UUIDType, primary_key=True, default=uuid4)
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
    subject_id = Column(UUIDType, ForeignKey("Platforms.platform_id", onupdate="cascade"))
    source_id = Column(
        UUIDType, ForeignKey("Datafiles.datafile_id", onupdate="cascade"), nullable=False
    )
    privacy_id = Column(UUIDType, ForeignKey("Privacies.privacy_id", onupdate="cascade"))
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


class CommentType(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.COMMENT_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 25

    comment_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
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
    created_date = Column(DateTime, default=datetime.utcnow)


class ConfidenceLevel(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.CONFIDENCE_LEVEL
    table_type = TableTypes.REFERENCE
    table_type_id = 27

    confidence_level_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class Change(BaseSpatiaLite):
    __tablename__ = constants.CHANGE
    table_type = TableTypes.METADATA
    table_type_id = 8

    change_id = Column(UUIDType, primary_key=True, default=uuid4)
    user = Column(String(150), nullable=False)
    modified = Column(DATE, nullable=False)
    reason = Column(String(500), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class DatafileType(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.DATAFILE_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 23

    datafile_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


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


class Nationality(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.NATIONALITY
    table_type = TableTypes.REFERENCE
    table_type_id = 14

    nationality_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    priority = Column(Integer)
    created_date = Column(DateTime, default=datetime.utcnow)


class PlatformType(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.PLATFORM_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 13

    platform_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class Participant(BaseSpatiaLite, ParticipantMixin):
    __tablename__ = constants.PARTICIPANT
    table_type = TableTypes.METADATA
    table_type_id = 5

    participant_id = Column(UUIDType, primary_key=True, default=uuid4)
    platform_id = Column(
        UUIDType, ForeignKey("Platforms.platform_id", onupdate="cascade"), nullable=False
    )
    task_id = Column(UUIDType, ForeignKey("Tasks.task_id", onupdate="cascade"), nullable=False)
    start = Column(TIMESTAMP)
    end = Column(TIMESTAMP)
    force = Column(String(150))
    privacy_id = Column(
        UUIDType, ForeignKey("Privacies.privacy_id", onupdate="cascade"), nullable=False
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class TaggedItem(BaseSpatiaLite, TaggedItemMixin):
    __tablename__ = constants.TAGGED_ITEM
    table_type = TableTypes.METADATA
    table_type_id = 12

    tagged_item_id = Column(UUIDType, primary_key=True, default=uuid4)
    tag_id = Column(UUIDType, ForeignKey("Tags.tag_id", onupdate="cascade"), nullable=False)
    item_id = Column(UUIDType, nullable=False)
    tagged_by_id = Column(UUIDType, ForeignKey("Users.user_id", onupdate="cascade"), nullable=False)
    private = Column(Boolean, nullable=False)
    tagged_on = Column(DATE, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class MediaType(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.MEDIA_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 24

    media_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


# revision identifiers, used by Alembic.
revision = "f2c9f346f305"
down_revision = "4fb1c8780273"
branch_labels = None
depends_on = None

naming_convention = {
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
}


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table(
        "Activations",
        schema=None,
        naming_convention=naming_convention,
        copy_from=Activation.__table__,
    ) as batch_op:
        batch_op.drop_constraint("fk_Activations_privacy_id_Privacies", type_="foreignkey")
        batch_op.drop_constraint("fk_Activations_source_id_Datafiles", type_="foreignkey")
        batch_op.drop_constraint("fk_Activations_sensor_id_Sensors", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_Activations_privacy_id_Privacies"),
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Activations_source_id_Datafiles"),
            "Datafiles",
            ["source_id"],
            ["datafile_id"],
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Activations_sensor_id_Sensors"),
            "Sensors",
            ["sensor_id"],
            ["sensor_id"],
            onupdate="cascade",
        )

    with op.batch_alter_table(
        "Comments", schema=None, naming_convention=naming_convention, copy_from=Comment.__table__
    ) as batch_op:
        batch_op.drop_constraint("fk_Comments_comment_type_id_CommentTypes", type_="foreignkey")
        batch_op.drop_constraint("fk_Comments_source_id_Datafiles", type_="foreignkey")
        batch_op.drop_constraint("fk_Comments_privacy_id_Privacies", type_="foreignkey")
        batch_op.drop_constraint("fk_Comments_platform_id_Platforms", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_Comments_comment_type_id_CommentTypes"),
            "CommentTypes",
            ["comment_type_id"],
            ["comment_type_id"],
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Comments_source_id_Datafiles"),
            "Datafiles",
            ["source_id"],
            ["datafile_id"],
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Comments_privacy_id_Privacies"),
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Comments_platform_id_Platforms"),
            "Platforms",
            ["platform_id"],
            ["platform_id"],
            onupdate="cascade",
        )

    with op.batch_alter_table(
        "Contacts", schema=None, naming_convention=naming_convention, copy_from=Contact.__table__
    ) as batch_op:
        batch_op.drop_constraint("fk_Contacts_subject_id_Platforms", type_="foreignkey")
        batch_op.drop_constraint("fk_Contacts_privacy_id_Privacies", type_="foreignkey")
        batch_op.drop_constraint("fk_Contacts_source_id_Datafiles", type_="foreignkey")
        batch_op.drop_constraint("fk_Contacts_sensor_id_Sensors", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_Contacts_subject_id_Platforms"),
            "Platforms",
            ["subject_id"],
            ["platform_id"],
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Contacts_privacy_id_Privacies"),
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Contacts_source_id_Datafiles"),
            "Datafiles",
            ["source_id"],
            ["datafile_id"],
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Contacts_sensor_id_Sensors"),
            "Sensors",
            ["sensor_id"],
            ["sensor_id"],
            onupdate="cascade",
        )

    with op.batch_alter_table(
        "Datafiles", schema=None, naming_convention=naming_convention, copy_from=Datafile.__table__
    ) as batch_op:
        batch_op.drop_constraint("fk_Datafiles_privacy_id_Privacies", type_="foreignkey")
        batch_op.drop_constraint("fk_Datafiles_datafile_type_id_DatafileTypes", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_Datafiles_privacy_id_Privacies"),
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Datafiles_datafile_type_id_DatafileTypes"),
            "DatafileTypes",
            ["datafile_type_id"],
            ["datafile_type_id"],
            onupdate="cascade",
        )

    with op.batch_alter_table(
        "Geometries",
        schema=None,
        naming_convention=naming_convention,
        copy_from=Geometry1.__table__,
    ) as batch_op:
        batch_op.drop_constraint("fk_Geometries_sensor_platform_id_Platforms", type_="foreignkey")
        batch_op.drop_constraint("fk_Geometries_geo_type_id_GeometryTypes", type_="foreignkey")
        batch_op.drop_constraint("fk_Geometries_privacy_id_Privacies", type_="foreignkey")
        batch_op.drop_constraint(
            "fk_Geometries_geo_sub_type_id_GeometrySubTypes", type_="foreignkey"
        )
        batch_op.drop_constraint("fk_Geometries_subject_platform_id_Platforms", type_="foreignkey")
        batch_op.drop_constraint("fk_Geometries_source_id_Datafiles", type_="foreignkey")
        batch_op.drop_constraint("fk_Geometries_task_id_Tasks", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_Geometries_sensor_platform_id_Platforms"),
            "Platforms",
            ["sensor_platform_id"],
            ["platform_id"],
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Geometries_geo_type_id_GeometryTypes"),
            "GeometryTypes",
            ["geo_type_id"],
            ["geo_type_id"],
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Geometries_privacy_id_Privacies"),
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Geometries_geo_sub_type_id_GeometrySubTypes"),
            "GeometrySubTypes",
            ["geo_sub_type_id"],
            ["geo_sub_type_id"],
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Geometries_subject_platform_id_Platforms"),
            "Platforms",
            ["subject_platform_id"],
            ["platform_id"],
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Geometries_source_id_Datafiles"),
            "Datafiles",
            ["source_id"],
            ["datafile_id"],
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Geometries_task_id_Tasks"),
            "Tasks",
            ["task_id"],
            ["task_id"],
            onupdate="cascade",
        )

    with op.batch_alter_table(
        "HostedBy", schema=None, naming_convention=naming_convention, copy_from=HostedBy.__table__
    ) as batch_op:
        batch_op.drop_constraint("fk_HostedBy_subject_id_Platforms", type_="foreignkey")
        batch_op.drop_constraint("fk_HostedBy_host_id_Platforms", type_="foreignkey")
        batch_op.drop_constraint("fk_HostedBy_privacy_id_Privacies", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_HostedBy_subject_id_Platforms"),
            "Platforms",
            ["subject_id"],
            ["platform_id"],
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_HostedBy_host_id_Platforms"),
            "Platforms",
            ["host_id"],
            ["platform_id"],
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_HostedBy_privacy_id_Privacies"),
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            onupdate="cascade",
        )

    with op.batch_alter_table(
        "Logs", schema=None, naming_convention=naming_convention, copy_from=Log.__table__
    ) as batch_op:
        batch_op.drop_constraint("fk_Logs_change_id_Changes", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_Logs_change_id_Changes"),
            "Changes",
            ["change_id"],
            ["change_id"],
            onupdate="cascade",
        )

    with op.batch_alter_table(
        "LogsHoldings",
        schema=None,
        naming_convention=naming_convention,
        copy_from=LogsHolding.__table__,
    ) as batch_op:
        batch_op.drop_constraint("fk_LogsHoldings_privacy_id_Privacies", type_="foreignkey")
        batch_op.drop_constraint("fk_LogsHoldings_unit_type_id_UnitTypes", type_="foreignkey")
        batch_op.drop_constraint("fk_LogsHoldings_platform_id_Platforms", type_="foreignkey")
        batch_op.drop_constraint("fk_LogsHoldings_source_id_Datafiles", type_="foreignkey")
        batch_op.drop_constraint("fk_LogsHoldings_commodity_id_CommodityTypes", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_LogsHoldings_privacy_id_Privacies"),
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_LogsHoldings_unit_type_id_UnitTypes"),
            "UnitTypes",
            ["unit_type_id"],
            ["unit_type_id"],
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_LogsHoldings_platform_id_Platforms"),
            "Platforms",
            ["platform_id"],
            ["platform_id"],
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_LogsHoldings_source_id_Datafiles"),
            "Datafiles",
            ["source_id"],
            ["datafile_id"],
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_LogsHoldings_commodity_id_CommodityTypes"),
            "CommodityTypes",
            ["commodity_id"],
            ["commodity_type_id"],
            onupdate="cascade",
        )

    with op.batch_alter_table(
        "Media", schema=None, naming_convention=naming_convention, copy_from=Media.__table__
    ) as batch_op:
        batch_op.drop_constraint("fk_Media_subject_id_Platforms", type_="foreignkey")
        batch_op.drop_constraint("fk_Media_sensor_id_Sensors", type_="foreignkey")
        batch_op.drop_constraint("fk_Media_source_id_Datafiles", type_="foreignkey")
        batch_op.drop_constraint("fk_Media_media_type_id_MediaTypes", type_="foreignkey")
        batch_op.drop_constraint("fk_Media_platform_id_Platforms", type_="foreignkey")
        batch_op.drop_constraint("fk_Media_privacy_id_Privacies", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_Media_subject_id_Platforms"),
            "Platforms",
            ["subject_id"],
            ["platform_id"],
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Media_sensor_id_Sensors"),
            "Sensors",
            ["sensor_id"],
            ["sensor_id"],
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Media_source_id_Datafiles"),
            "Datafiles",
            ["source_id"],
            ["datafile_id"],
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Media_media_type_id_MediaTypes"),
            "MediaTypes",
            ["media_type_id"],
            ["media_type_id"],
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Media_platform_id_Platforms"),
            "Platforms",
            ["platform_id"],
            ["platform_id"],
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Media_privacy_id_Privacies"),
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            onupdate="cascade",
        )

    with op.batch_alter_table(
        "Participants",
        schema=None,
        naming_convention=naming_convention,
        copy_from=Participant.__table__,
    ) as batch_op:
        batch_op.drop_constraint("fk_Participants_privacy_id_Privacies", type_="foreignkey")
        batch_op.drop_constraint("fk_Participants_task_id_Tasks", type_="foreignkey")
        batch_op.drop_constraint("fk_Participants_platform_id_Platforms", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_Participants_privacy_id_Privacies"),
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Participants_task_id_Tasks"),
            "Tasks",
            ["task_id"],
            ["task_id"],
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Participants_platform_id_Platforms"),
            "Platforms",
            ["platform_id"],
            ["platform_id"],
            onupdate="cascade",
        )

    with op.batch_alter_table(
        "Platforms", schema=None, naming_convention=naming_convention, copy_from=Platform.__table__
    ) as batch_op:
        batch_op.drop_constraint("fk_Platforms_platform_type_id_PlatformTypes", type_="foreignkey")
        batch_op.drop_constraint("fk_Platforms_nationality_id_Nationalities", type_="foreignkey")
        batch_op.drop_constraint("fk_Platforms_privacy_id_Privacies", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_Platforms_platform_type_id_PlatformTypes"),
            "PlatformTypes",
            ["platform_type_id"],
            ["platform_type_id"],
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Platforms_nationality_id_Nationalities"),
            "Nationalities",
            ["nationality_id"],
            ["nationality_id"],
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Platforms_privacy_id_Privacies"),
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            onupdate="cascade",
        )

    with op.batch_alter_table(
        "Sensors", schema=None, naming_convention=naming_convention, copy_from=Sensor.__table__
    ) as batch_op:
        batch_op.drop_constraint("fk_Sensors_privacy_id_Privacies", type_="foreignkey")
        batch_op.drop_constraint("fk_Sensors_host_Platforms", type_="foreignkey")
        batch_op.drop_constraint("fk_Sensors_sensor_type_id_SensorTypes", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_Sensors_privacy_id_Privacies"),
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Sensors_host_Platforms"),
            "Platforms",
            ["host"],
            ["platform_id"],
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Sensors_sensor_type_id_SensorTypes"),
            "SensorTypes",
            ["sensor_type_id"],
            ["sensor_type_id"],
            onupdate="cascade",
        )

    with op.batch_alter_table(
        "States", schema=None, naming_convention=naming_convention, copy_from=State.__table__
    ) as batch_op:
        batch_op.drop_constraint("fk_States_source_id_Datafiles", type_="foreignkey")
        batch_op.drop_constraint("fk_States_privacy_id_Privacies", type_="foreignkey")
        batch_op.drop_constraint("fk_States_sensor_id_Sensors", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_States_source_id_Datafiles"),
            "Datafiles",
            ["source_id"],
            ["datafile_id"],
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_States_privacy_id_Privacies"),
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_States_sensor_id_Sensors"),
            "Sensors",
            ["sensor_id"],
            ["sensor_id"],
            onupdate="cascade",
        )

    with op.batch_alter_table(
        "TaggedItems",
        schema=None,
        naming_convention=naming_convention,
        copy_from=TaggedItem.__table__,
    ) as batch_op:
        batch_op.drop_constraint("fk_TaggedItems_tagged_by_id_Users", type_="foreignkey")
        batch_op.drop_constraint("fk_TaggedItems_tag_id_Tags", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_TaggedItems_tagged_by_id_Users"),
            "Users",
            ["tagged_by_id"],
            ["user_id"],
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_TaggedItems_tag_id_Tags"),
            "Tags",
            ["tag_id"],
            ["tag_id"],
            onupdate="cascade",
        )

    with op.batch_alter_table(
        "Tasks", schema=None, naming_convention=naming_convention, copy_from=Task.__table__
    ) as batch_op:
        batch_op.drop_constraint("fk_Tasks_parent_id_Tasks", type_="foreignkey")
        batch_op.drop_constraint("fk_Tasks_privacy_id_Privacies", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_Tasks_parent_id_Tasks"),
            "Tasks",
            ["parent_id"],
            ["task_id"],
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Tasks_privacy_id_Privacies"),
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            onupdate="cascade",
        )

    ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table(
        "Tasks", schema=None, naming_convention=naming_convention, copy_from=Task.__table__
    ) as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_Tasks_privacy_id_Privacies"), type_="foreignkey")
        batch_op.drop_constraint(batch_op.f("fk_Tasks_parent_id_Tasks"), type_="foreignkey")
        batch_op.create_foreign_key(None, "Privacies", ["privacy_id"], ["privacy_id"])
        batch_op.create_foreign_key(None, "Tasks", ["parent_id"], ["task_id"])

    with op.batch_alter_table(
        "TaggedItems",
        schema=None,
        naming_convention=naming_convention,
        copy_from=TaggedItem.__table__,
    ) as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_TaggedItems_tag_id_Tags"), type_="foreignkey")
        batch_op.drop_constraint(
            batch_op.f("fk_TaggedItems_tagged_by_id_Users"), type_="foreignkey"
        )
        batch_op.create_foreign_key(None, "Users", ["tagged_by_id"], ["user_id"])
        batch_op.create_foreign_key(None, "Tags", ["tag_id"], ["tag_id"])

    with op.batch_alter_table(
        "States", schema=None, naming_convention=naming_convention, copy_from=State.__table__
    ) as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_States_sensor_id_Sensors"), type_="foreignkey")
        batch_op.drop_constraint(batch_op.f("fk_States_privacy_id_Privacies"), type_="foreignkey")
        batch_op.drop_constraint(batch_op.f("fk_States_source_id_Datafiles"), type_="foreignkey")
        batch_op.create_foreign_key(None, "Sensors", ["sensor_id"], ["sensor_id"])
        batch_op.create_foreign_key(None, "Datafiles", ["source_id"], ["datafile_id"])
        batch_op.create_foreign_key(None, "Privacies", ["privacy_id"], ["privacy_id"])
        batch_op.alter_column(
            "location",
            existing_type=geoalchemy2.types.Geometry(
                geometry_type="POINT", srid=4326, management=True, spatial_index=False
            ),
            type_=sa.INTEGER(),
            existing_nullable=True,
        )

    with op.batch_alter_table(
        "Sensors", schema=None, naming_convention=naming_convention, copy_from=Sensor.__table__
    ) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_Sensors_sensor_type_id_SensorTypes"), type_="foreignkey"
        )
        batch_op.drop_constraint(batch_op.f("fk_Sensors_host_Platforms"), type_="foreignkey")
        batch_op.drop_constraint(batch_op.f("fk_Sensors_privacy_id_Privacies"), type_="foreignkey")
        batch_op.create_foreign_key(None, "Privacies", ["privacy_id"], ["privacy_id"])
        batch_op.create_foreign_key(None, "Platforms", ["host"], ["platform_id"])
        batch_op.create_foreign_key(None, "SensorTypes", ["sensor_type_id"], ["sensor_type_id"])

    with op.batch_alter_table(
        "Platforms", schema=None, naming_convention=naming_convention, copy_from=Platform.__table__
    ) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_Platforms_privacy_id_Privacies"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("fk_Platforms_nationality_id_Nationalities"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("fk_Platforms_platform_type_id_PlatformTypes"), type_="foreignkey"
        )
        batch_op.create_foreign_key(
            None, "PlatformTypes", ["platform_type_id"], ["platform_type_id"]
        )
        batch_op.create_foreign_key(None, "Nationalities", ["nationality_id"], ["nationality_id"])
        batch_op.create_foreign_key(None, "Privacies", ["privacy_id"], ["privacy_id"])

    with op.batch_alter_table(
        "Participants",
        schema=None,
        naming_convention=naming_convention,
        copy_from=Participant.__table__,
    ) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_Participants_platform_id_Platforms"), type_="foreignkey"
        )
        batch_op.drop_constraint(batch_op.f("fk_Participants_task_id_Tasks"), type_="foreignkey")
        batch_op.drop_constraint(
            batch_op.f("fk_Participants_privacy_id_Privacies"), type_="foreignkey"
        )
        batch_op.create_foreign_key(None, "Platforms", ["platform_id"], ["platform_id"])
        batch_op.create_foreign_key(None, "Privacies", ["privacy_id"], ["privacy_id"])
        batch_op.create_foreign_key(None, "Tasks", ["task_id"], ["task_id"])

    with op.batch_alter_table(
        "Media", schema=None, naming_convention=naming_convention, copy_from=Media.__table__
    ) as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_Media_privacy_id_Privacies"), type_="foreignkey")
        batch_op.drop_constraint(batch_op.f("fk_Media_platform_id_Platforms"), type_="foreignkey")
        batch_op.drop_constraint(
            batch_op.f("fk_Media_media_type_id_MediaTypes"), type_="foreignkey"
        )
        batch_op.drop_constraint(batch_op.f("fk_Media_source_id_Datafiles"), type_="foreignkey")
        batch_op.drop_constraint(batch_op.f("fk_Media_sensor_id_Sensors"), type_="foreignkey")
        batch_op.drop_constraint(batch_op.f("fk_Media_subject_id_Platforms"), type_="foreignkey")
        batch_op.create_foreign_key(None, "Datafiles", ["source_id"], ["datafile_id"])
        batch_op.create_foreign_key(None, "Platforms", ["subject_id"], ["platform_id"])
        batch_op.create_foreign_key(None, "Privacies", ["privacy_id"], ["privacy_id"])
        batch_op.create_foreign_key(None, "Sensors", ["sensor_id"], ["sensor_id"])
        batch_op.create_foreign_key(None, "Platforms", ["platform_id"], ["platform_id"])
        batch_op.create_foreign_key(None, "MediaTypes", ["media_type_id"], ["media_type_id"])
        batch_op.alter_column(
            "location",
            existing_type=geoalchemy2.types.Geometry(
                geometry_type="POINT", srid=4326, management=True, spatial_index=False
            ),
            type_=sa.INTEGER(),
            existing_nullable=True,
        )

    with op.batch_alter_table(
        "LogsHoldings",
        schema=None,
        naming_convention=naming_convention,
        copy_from=LogsHolding.__table__,
    ) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_LogsHoldings_commodity_id_CommodityTypes"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("fk_LogsHoldings_source_id_Datafiles"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("fk_LogsHoldings_platform_id_Platforms"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("fk_LogsHoldings_unit_type_id_UnitTypes"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("fk_LogsHoldings_privacy_id_Privacies"), type_="foreignkey"
        )
        batch_op.create_foreign_key(None, "Datafiles", ["source_id"], ["datafile_id"])
        batch_op.create_foreign_key(None, "Platforms", ["platform_id"], ["platform_id"])
        batch_op.create_foreign_key(None, "CommodityTypes", ["commodity_id"], ["commodity_type_id"])
        batch_op.create_foreign_key(None, "UnitTypes", ["unit_type_id"], ["unit_type_id"])
        batch_op.create_foreign_key(None, "Privacies", ["privacy_id"], ["privacy_id"])

    with op.batch_alter_table(
        "Logs", schema=None, naming_convention=naming_convention, copy_from=Log.__table__
    ) as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_Logs_change_id_Changes"), type_="foreignkey")
        batch_op.create_foreign_key(None, "Changes", ["change_id"], ["change_id"])

    with op.batch_alter_table(
        "HostedBy", schema=None, naming_convention=naming_convention, copy_from=HostedBy.__table__
    ) as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_HostedBy_privacy_id_Privacies"), type_="foreignkey")
        batch_op.drop_constraint(batch_op.f("fk_HostedBy_host_id_Platforms"), type_="foreignkey")
        batch_op.drop_constraint(batch_op.f("fk_HostedBy_subject_id_Platforms"), type_="foreignkey")
        batch_op.create_foreign_key(None, "Privacies", ["privacy_id"], ["privacy_id"])
        batch_op.create_foreign_key(None, "Platforms", ["host_id"], ["platform_id"])
        batch_op.create_foreign_key(None, "Platforms", ["subject_id"], ["platform_id"])

    with op.batch_alter_table(
        "Geometries",
        schema=None,
        naming_convention=naming_convention,
        copy_from=Geometry1.__table__,
    ) as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_Geometries_task_id_Tasks"), type_="foreignkey")
        batch_op.drop_constraint(
            batch_op.f("fk_Geometries_source_id_Datafiles"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("fk_Geometries_subject_platform_id_Platforms"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("fk_Geometries_geo_sub_type_id_GeometrySubTypes"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("fk_Geometries_privacy_id_Privacies"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("fk_Geometries_geo_type_id_GeometryTypes"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("fk_Geometries_sensor_platform_id_Platforms"), type_="foreignkey"
        )
        batch_op.create_foreign_key(None, "Privacies", ["privacy_id"], ["privacy_id"])
        batch_op.create_foreign_key(None, "Platforms", ["subject_platform_id"], ["platform_id"])
        batch_op.create_foreign_key(
            None, "GeometrySubTypes", ["geo_sub_type_id"], ["geo_sub_type_id"]
        )
        batch_op.create_foreign_key(None, "GeometryTypes", ["geo_type_id"], ["geo_type_id"])
        batch_op.create_foreign_key(None, "Platforms", ["sensor_platform_id"], ["platform_id"])
        batch_op.create_foreign_key(None, "Datafiles", ["source_id"], ["datafile_id"])
        batch_op.create_foreign_key(None, "Tasks", ["task_id"], ["task_id"])
        batch_op.alter_column(
            "geometry",
            existing_type=geoalchemy2.types.Geometry(management=True, spatial_index=False),
            type_=sa.NUMERIC(),
            existing_nullable=False,
        )

    with op.batch_alter_table(
        "Datafiles", schema=None, naming_convention=naming_convention, copy_from=Datafile.__table__
    ) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_Datafiles_datafile_type_id_DatafileTypes"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("fk_Datafiles_privacy_id_Privacies"), type_="foreignkey"
        )
        batch_op.create_foreign_key(None, "Privacies", ["privacy_id"], ["privacy_id"])
        batch_op.create_foreign_key(
            None, "DatafileTypes", ["datafile_type_id"], ["datafile_type_id"]
        )

    with op.batch_alter_table(
        "Contacts", schema=None, naming_convention=naming_convention, copy_from=Contact.__table__
    ) as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_Contacts_sensor_id_Sensors"), type_="foreignkey")
        batch_op.drop_constraint(batch_op.f("fk_Contacts_source_id_Datafiles"), type_="foreignkey")
        batch_op.drop_constraint(batch_op.f("fk_Contacts_privacy_id_Privacies"), type_="foreignkey")
        batch_op.drop_constraint(batch_op.f("fk_Contacts_subject_id_Platforms"), type_="foreignkey")
        batch_op.create_foreign_key(None, "Datafiles", ["source_id"], ["datafile_id"])
        batch_op.create_foreign_key(None, "Platforms", ["subject_id"], ["platform_id"])
        batch_op.create_foreign_key(None, "Privacies", ["privacy_id"], ["privacy_id"])
        batch_op.create_foreign_key(None, "Sensors", ["sensor_id"], ["sensor_id"])
        batch_op.alter_column(
            "location",
            existing_type=geoalchemy2.types.Geometry(
                geometry_type="POINT", srid=4326, management=True, spatial_index=False
            ),
            type_=sa.INTEGER(),
            existing_nullable=True,
        )

    with op.batch_alter_table(
        "Comments", schema=None, naming_convention=naming_convention, copy_from=Comment.__table__
    ) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_Comments_platform_id_Platforms"), type_="foreignkey"
        )
        batch_op.drop_constraint(batch_op.f("fk_Comments_privacy_id_Privacies"), type_="foreignkey")
        batch_op.drop_constraint(batch_op.f("fk_Comments_source_id_Datafiles"), type_="foreignkey")
        batch_op.drop_constraint(
            batch_op.f("fk_Comments_comment_type_id_CommentTypes"), type_="foreignkey"
        )
        batch_op.create_foreign_key(None, "Platforms", ["platform_id"], ["platform_id"])
        batch_op.create_foreign_key(None, "CommentTypes", ["comment_type_id"], ["comment_type_id"])
        batch_op.create_foreign_key(None, "Datafiles", ["source_id"], ["datafile_id"])
        batch_op.create_foreign_key(None, "Privacies", ["privacy_id"], ["privacy_id"])

    with op.batch_alter_table(
        "Activations",
        schema=None,
        naming_convention=naming_convention,
        copy_from=Activation.__table__,
    ) as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_Activations_sensor_id_Sensors"), type_="foreignkey")
        batch_op.drop_constraint(
            batch_op.f("fk_Activations_source_id_Datafiles"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("fk_Activations_privacy_id_Privacies"), type_="foreignkey"
        )
        batch_op.create_foreign_key(None, "Privacies", ["privacy_id"], ["privacy_id"])
        batch_op.create_foreign_key(None, "Sensors", ["sensor_id"], ["sensor_id"])
        batch_op.create_foreign_key(None, "Datafiles", ["source_id"], ["datafile_id"])

    # ### end Alembic commands ###
