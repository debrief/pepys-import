"""Switch to UUIDs for PKs for SQLite

Revision ID: 6c1e62ee267f
Revises: ccc37f794db6
Create Date: 2020-05-18 16:54:47.274410

"""
from datetime import datetime
from uuid import uuid4

import geoalchemy2
import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy import DATE, Boolean, Column, DateTime, ForeignKey, Integer, MetaData, String
from sqlalchemy.dialects.sqlite import REAL, TIMESTAMP
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import (  # used to defer fetching attributes unless it's specifically called
    deferred,
    relationship,
)

import pepys_import
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


class HostedBy(BaseSpatiaLite, HostedByMixin):
    __tablename__ = constants.HOSTED_BY
    table_type = TableTypes.METADATA
    table_type_id = 1

    hosted_by_id = Column(UUIDType, primary_key=True, default=uuid4)
    subject_id = Column(UUIDType, ForeignKey("Platforms.platform_id"), nullable=False)
    host_id = Column(UUIDType, ForeignKey("Platforms.platform_id"), nullable=False)
    hosted_from = Column(DATE, nullable=False)
    host_to = Column(DATE, nullable=False)
    privacy_id = Column(Integer, ForeignKey("Privacies.privacy_id"), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class CommentType(BaseSpatiaLite):
    __tablename__ = constants.COMMENT_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 25

    comment_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class Synonym(BaseSpatiaLite):
    __tablename__ = constants.SYNONYM
    table_type = TableTypes.METADATA
    table_type_id = 7

    synonym_id = Column(UUIDType, primary_key=True, default=uuid4)
    table = Column(String(150), nullable=False)
    entity = Column(UUIDType, nullable=False)
    synonym = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Media(BaseSpatiaLite, MediaMixin, ElevationPropertyMixin, LocationPropertyMixin):
    __tablename__ = constants.MEDIA
    table_type = TableTypes.MEASUREMENT
    table_type_id = 34

    media_id = Column(UUIDType, primary_key=True, default=uuid4)
    platform_id = Column(UUIDType, ForeignKey("Platforms.platform_id"))
    subject_id = Column(UUIDType, ForeignKey("Platforms.platform_id"))
    sensor_id = Column(UUIDType, ForeignKey("Sensors.sensor_id"))
    _location = deferred(
        Column("location", Geometry(geometry_type="POINT", srid=4326, management=True))
    )
    _elevation = deferred(Column("elevation", REAL))
    time = Column(TIMESTAMP)
    media_type_id = Column(UUIDType, ForeignKey("MediaTypes.media_type_id"), nullable=False)
    url = deferred(Column(String(150), nullable=False))
    source_id = Column(UUIDType, ForeignKey("Datafiles.datafile_id"), nullable=False)
    privacy_id = Column(UUIDType, ForeignKey("Privacies.privacy_id"))
    created_date = Column(DateTime, default=datetime.utcnow)


class ConfidenceLevel(BaseSpatiaLite):
    __tablename__ = constants.CONFIDENCE_LEVEL
    table_type = TableTypes.REFERENCE
    table_type_id = 27

    confidence_level_id = Column(UUIDType, primary_key=True, default=uuid4)
    level = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class MediaType(BaseSpatiaLite):
    __tablename__ = constants.MEDIA_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 24

    media_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class Tag(BaseSpatiaLite):
    __tablename__ = constants.TAG
    table_type = TableTypes.METADATA
    table_type_id = 11

    tag_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class User(BaseSpatiaLite):
    __tablename__ = constants.USER
    table_type = TableTypes.REFERENCE
    table_type_id = 17

    user_id = Column(UUIDType, primary_key=True, default=uuid4)
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
    privacy_id = Column(UUIDType, ForeignKey("Privacies.privacy_id"), nullable=False)
    datafile_type_id = Column(
        UUIDType, ForeignKey("DatafileTypes.datafile_type_id"), nullable=False
    )
    reference = Column(String(150))
    url = Column(String(150))
    size = deferred(Column(Integer, nullable=False))
    hash = deferred(Column(String(32), nullable=False))
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


class Comment(BaseSpatiaLite, CommentMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sensor_name = "N/A"

    __tablename__ = constants.COMMENT
    table_type = TableTypes.MEASUREMENT
    table_type_id = 32

    comment_id = Column(UUIDType, primary_key=True, default=uuid4)
    platform_id = Column(UUIDType, ForeignKey("Platforms.platform_id"))
    time = Column(TIMESTAMP, nullable=False)
    comment_type_id = Column(UUIDType, ForeignKey("CommentTypes.comment_type_id"), nullable=False)
    content = Column(String(150), nullable=False)
    source_id = Column(UUIDType, ForeignKey("Datafiles.datafile_id"), nullable=False)
    privacy_id = Column(UUIDType, ForeignKey("Privacies.privacy_id"))
    created_date = Column(DateTime, default=datetime.utcnow)


class Log(BaseSpatiaLite, LogMixin):
    __tablename__ = constants.LOG
    table_type = TableTypes.METADATA
    table_type_id = 9

    log_id = Column(UUIDType, primary_key=True, default=uuid4)
    table = Column(String(150), nullable=False)
    id = Column(UUIDType, nullable=False)
    field = Column(String(150))
    new_value = Column(String(150))
    change_id = Column(UUIDType, ForeignKey("Changes.change_id"), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Nationality(BaseSpatiaLite):
    __tablename__ = constants.NATIONALITY
    table_type = TableTypes.REFERENCE
    table_type_id = 14

    nationality_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)

    created_date = Column(DateTime, default=datetime.utcnow)


class ClassificationType(BaseSpatiaLite):
    __tablename__ = constants.CLASSIFICATION_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 19

    class_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class LogsHolding(BaseSpatiaLite, LogsHoldingMixin):
    __tablename__ = constants.LOGS_HOLDING
    table_type = TableTypes.MEASUREMENT
    table_type_id = 31

    logs_holding_id = Column(UUIDType, primary_key=True, default=uuid4)
    time = Column(TIMESTAMP, nullable=False)
    commodity_id = Column(UUIDType, ForeignKey("CommodityTypes.commodity_type_id"), nullable=False)
    quantity = Column(REAL, nullable=False)
    unit_type_id = Column(UUIDType, ForeignKey("UnitTypes.unit_type_id"), nullable=False)
    platform_id = Column(UUIDType, ForeignKey("Platforms.platform_id"), nullable=False)
    comment = Column(String(150), nullable=False)
    source_id = Column(UUIDType, ForeignKey("Datafiles.datafile_id"), nullable=False)
    privacy_id = Column(UUIDType, ForeignKey("Privacies.privacy_id"))
    created_date = Column(DateTime, default=datetime.utcnow)


class Participant(BaseSpatiaLite, ParticipantMixin):
    __tablename__ = constants.PARTICIPANT
    table_type = TableTypes.METADATA
    table_type_id = 5

    participant_id = Column(UUIDType, primary_key=True, default=uuid4)
    platform_id = Column(UUIDType, ForeignKey("Platforms.platform_id"), nullable=False)
    task_id = Column(UUIDType, ForeignKey("Tasks.task_id"), nullable=False)
    start = Column(TIMESTAMP)
    end = Column(TIMESTAMP)
    force = Column(String(150))
    privacy_id = Column(UUIDType, ForeignKey("Privacies.privacy_id"), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class CommodityType(BaseSpatiaLite):
    __tablename__ = constants.COMMODITY_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 26

    commodity_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class UnitType(BaseSpatiaLite):
    __tablename__ = constants.UNIT_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 18

    unit_type_id = Column(UUIDType, primary_key=True, default=uuid4)
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


class Activation(BaseSpatiaLite, ActivationMixin):
    __tablename__ = constants.ACTIVATION
    table_type = TableTypes.MEASUREMENT
    table_type_id = 30

    activation_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False)
    sensor_id = Column(UUIDType, ForeignKey("Sensors.sensor_id"), nullable=False)
    start = deferred(Column(TIMESTAMP, nullable=False))
    end = deferred(Column(TIMESTAMP, nullable=False))
    _min_range = deferred(Column("min_range", REAL))
    _max_range = deferred(Column("max_range", REAL))
    _left_arc = deferred(Column("left_arc", REAL))
    _right_arc = deferred(Column("right_arc", REAL))
    source_id = Column(UUIDType, ForeignKey("Datafiles.datafile_id"), nullable=False)
    privacy_id = Column(UUIDType, ForeignKey("Privacies.privacy_id"))
    created_date = Column(DateTime, default=datetime.utcnow)


class TaggedItem(BaseSpatiaLite, TaggedItemMixin):
    __tablename__ = constants.TAGGED_ITEM
    table_type = TableTypes.METADATA
    table_type_id = 12

    tagged_item_id = Column(UUIDType, primary_key=True, default=uuid4)
    tag_id = Column(UUIDType, ForeignKey("Tags.tag_id"), nullable=False)
    item_id = Column(UUIDType, nullable=False)
    tagged_by_id = Column(UUIDType, ForeignKey("Users.user_id"), nullable=False)
    private = Column(Boolean, nullable=False)
    tagged_on = Column(DATE, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Extraction(BaseSpatiaLite):
    __tablename__ = constants.EXTRACTION
    table_type = TableTypes.METADATA
    table_type_id = 10

    extraction_id = Column(UUIDType, primary_key=True, default=uuid4)
    table = Column(String(150), nullable=False)
    field = Column(String(150), nullable=False)
    chars = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Platform(BaseSpatiaLite, PlatformMixin):
    __tablename__ = constants.PLATFORM
    table_type = TableTypes.METADATA
    table_type_id = 3

    platform_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False)

    trigraph = deferred(Column(String(3)))
    quadgraph = deferred(Column(String(4)))
    nationality_id = Column(UUIDType, ForeignKey("Nationalities.nationality_id"), nullable=False)
    platform_type_id = Column(
        UUIDType, ForeignKey("PlatformTypes.platform_type_id"), nullable=False
    )
    privacy_id = Column(UUIDType, ForeignKey("Privacies.privacy_id"), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Geometry1(BaseSpatiaLite, GeometryMixin):
    __tablename__ = constants.GEOMETRY
    table_type = TableTypes.MEASUREMENT
    table_type_id = 33

    geometry_id = Column(UUIDType, primary_key=True, default=uuid4)
    geometry = deferred(Column(Geometry(geometry_type="GEOMETRY", management=True), nullable=False))
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


class ContactType(BaseSpatiaLite):
    __tablename__ = constants.CONTACT_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 20

    contact_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    contact_type = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class SensorType(BaseSpatiaLite):
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
    name = Column(String(150), nullable=False)
    sensor_type_id = Column(UUIDType, ForeignKey("SensorTypes.sensor_type_id"), nullable=False)
    host = Column(UUIDType, ForeignKey("Platforms.platform_id"), nullable=False)
    privacy_id = Column(UUIDType, ForeignKey("Privacies.privacy_id"), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class GeometryType(BaseSpatiaLite):
    __tablename__ = constants.GEOMETRY_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 15

    geo_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class State(BaseSpatiaLite, StateMixin, ElevationPropertyMixin, LocationPropertyMixin):
    __tablename__ = constants.STATE
    table_type = TableTypes.MEASUREMENT
    table_type_id = 28

    state_id = Column(UUIDType, primary_key=True, default=uuid4)
    time = Column(TIMESTAMP, nullable=False)
    sensor_id = Column(UUIDType, ForeignKey("Sensors.sensor_id"), nullable=False)
    _location = deferred(
        Column("location", Geometry(geometry_type="POINT", srid=4326, management=True))
    )
    _elevation = deferred(Column("elevation", REAL))
    _heading = deferred(Column("heading", REAL))
    _course = deferred(Column("course", REAL))
    _speed = deferred(Column("speed", REAL))
    source_id = Column(UUIDType, ForeignKey("Datafiles.datafile_id"), nullable=False)
    privacy_id = Column(UUIDType, ForeignKey("Privacies.privacy_id"))
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


class Contact(BaseSpatiaLite, ContactMixin, LocationPropertyMixin, ElevationPropertyMixin):
    __tablename__ = constants.CONTACT
    table_type = TableTypes.MEASUREMENT
    table_type_id = 29

    contact_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150))
    sensor_id = Column(UUIDType, ForeignKey("Sensors.sensor_id"), nullable=False)
    time = Column(TIMESTAMP, nullable=False)
    _bearing = deferred(Column("bearing", REAL))
    _rel_bearing = deferred(Column("rel_bearing", REAL))
    _ambig_bearing = deferred(Column("ambig_bearing", REAL))
    _freq = deferred(Column("freq", REAL))
    _range = deferred(Column("range", REAL))
    _location = deferred(
        Column("location", Geometry(geometry_type="POINT", srid=4326, management=True))
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
    subject_id = Column(UUIDType, ForeignKey("Platforms.platform_id"))
    source_id = Column(UUIDType, ForeignKey("Datafiles.datafile_id"), nullable=False)
    privacy_id = Column(UUIDType, ForeignKey("Privacies.privacy_id"))
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


class PlatformType(BaseSpatiaLite):
    __tablename__ = constants.PLATFORM_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 13

    platform_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class DatafileType(BaseSpatiaLite):
    __tablename__ = constants.DATAFILE_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 23

    datafile_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


# revision identifiers, used by Alembic.
revision = "6c1e62ee267f"
down_revision = "ccc37f794db6"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table(
        "Activations", schema=None, copy_from=Activation.__table__
    ) as batch_op:
        batch_op.alter_column(
            "activation_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
        )
        batch_op.alter_column(
            "privacy_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "sensor_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "source_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=False,
        )

    with op.batch_alter_table("Changes", schema=None, copy_from=Change.__table__) as batch_op:
        batch_op.alter_column(
            "change_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
        )

    with op.batch_alter_table(
        "ClassificationTypes", schema=None, copy_from=ClassificationType.__table__
    ) as batch_op:
        batch_op.alter_column(
            "class_type_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
        )

    with op.batch_alter_table(
        "CommentTypes", schema=None, copy_from=CommentType.__table__
    ) as batch_op:
        batch_op.alter_column(
            "comment_type_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
        )

    with op.batch_alter_table("Comments", schema=None, copy_from=Comment.__table__) as batch_op:
        batch_op.alter_column(
            "comment_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
        )
        batch_op.alter_column(
            "comment_type_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "platform_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "privacy_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "source_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=False,
        )

    with op.batch_alter_table(
        "CommodityTypes", schema=None, copy_from=CommodityType.__table__
    ) as batch_op:
        batch_op.alter_column(
            "commodity_type_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
        )

    with op.batch_alter_table(
        "ConfidenceLevels", schema=None, copy_from=ConfidenceLevel.__table__
    ) as batch_op:
        batch_op.alter_column(
            "confidence_level_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
        )

    with op.batch_alter_table(
        "ContactTypes", schema=None, copy_from=ContactType.__table__
    ) as batch_op:
        batch_op.alter_column(
            "contact_type_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
        )

    with op.batch_alter_table("Contacts", schema=None, copy_from=Contact.__table__) as batch_op:
        batch_op.alter_column(
            "contact_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
        )
        batch_op.alter_column(
            "privacy_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "sensor_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "source_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "subject_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=True,
        )

    with op.batch_alter_table(
        "DatafileTypes", schema=None, copy_from=DatafileType.__table__
    ) as batch_op:
        batch_op.alter_column(
            "datafile_type_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
        )

    with op.batch_alter_table("Datafiles", schema=None, copy_from=Datafile.__table__) as batch_op:
        batch_op.alter_column(
            "datafile_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
        )
        batch_op.alter_column(
            "datafile_type_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "privacy_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=False,
        )

    with op.batch_alter_table(
        "Extractions", schema=None, copy_from=Extraction.__table__
    ) as batch_op:
        batch_op.alter_column(
            "extraction_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
        )

    with op.batch_alter_table("Geometries", schema=None, copy_from=Geometry1.__table__) as batch_op:
        batch_op.alter_column(
            "geo_sub_type_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "geo_type_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "geometry_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
        )
        batch_op.alter_column(
            "privacy_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "sensor_platform_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "source_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "subject_platform_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "task_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=True,
        )

    with op.batch_alter_table(
        "GeometrySubTypes", schema=None, copy_from=GeometrySubType.__table__
    ) as batch_op:
        batch_op.alter_column(
            "geo_sub_type_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
        )

    with op.batch_alter_table(
        "GeometryTypes", schema=None, copy_from=GeometryType.__table__
    ) as batch_op:
        batch_op.alter_column(
            "geo_type_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
        )

    with op.batch_alter_table("HostedBy", schema=None, copy_from=HostedBy.__table__) as batch_op:
        batch_op.alter_column(
            "host_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "hosted_by_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
        )
        batch_op.alter_column(
            "subject_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=False,
        )

    with op.batch_alter_table("Logs", schema=None, copy_from=Log.__table__) as batch_op:
        batch_op.alter_column(
            "change_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "log_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
        )

    with op.batch_alter_table(
        "LogsHoldings", schema=None, copy_from=LogsHolding.__table__
    ) as batch_op:
        batch_op.alter_column(
            "commodity_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "logs_holding_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
        )
        batch_op.alter_column(
            "platform_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "privacy_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "source_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "unit_type_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=False,
        )

    with op.batch_alter_table("Media", schema=None, copy_from=Media.__table__) as batch_op:
        batch_op.alter_column(
            "media_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
        )
        batch_op.alter_column(
            "media_type_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "platform_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "privacy_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "sensor_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "source_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "subject_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=True,
        )

    with op.batch_alter_table("MediaTypes", schema=None, copy_from=MediaType.__table__) as batch_op:
        batch_op.alter_column(
            "media_type_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
        )

    with op.batch_alter_table(
        "Nationalities", schema=None, copy_from=Nationality.__table__
    ) as batch_op:
        batch_op.alter_column(
            "nationality_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
        )

    with op.batch_alter_table(
        "Participants", schema=None, copy_from=Participant.__table__
    ) as batch_op:
        batch_op.alter_column(
            "participant_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
        )
        batch_op.alter_column(
            "platform_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "privacy_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "task_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=False,
        )

    with op.batch_alter_table(
        "PlatformTypes", schema=None, copy_from=PlatformType.__table__
    ) as batch_op:
        batch_op.alter_column(
            "platform_type_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
        )

    with op.batch_alter_table("Platforms", schema=None, copy_from=Platform.__table__) as batch_op:
        batch_op.alter_column(
            "nationality_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "platform_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
        )
        batch_op.alter_column(
            "platform_type_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "privacy_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=False,
        )

    with op.batch_alter_table("Privacies", schema=None, copy_from=Privacy.__table__) as batch_op:
        batch_op.alter_column(
            "privacy_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
        )

    with op.batch_alter_table(
        "SensorTypes", schema=None, copy_from=SensorType.__table__
    ) as batch_op:
        batch_op.alter_column(
            "sensor_type_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
        )

    with op.batch_alter_table("Sensors", schema=None, copy_from=Sensor.__table__) as batch_op:
        batch_op.alter_column(
            "host",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "privacy_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "sensor_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
        )
        batch_op.alter_column(
            "sensor_type_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=False,
        )

    with op.batch_alter_table("States", schema=None, copy_from=State.__table__) as batch_op:
        batch_op.alter_column(
            "privacy_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "sensor_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "source_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "state_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
        )

    with op.batch_alter_table("Synonyms", schema=None, copy_from=Synonym.__table__) as batch_op:
        batch_op.alter_column(
            "entity",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "synonym_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
        )

    with op.batch_alter_table(
        "TaggedItems", schema=None, copy_from=TaggedItem.__table__
    ) as batch_op:
        batch_op.alter_column(
            "item_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "tag_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "tagged_by_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "tagged_item_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
        )

    with op.batch_alter_table("Tags", schema=None, copy_from=Tag.__table__) as batch_op:
        batch_op.alter_column(
            "tag_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
        )

    with op.batch_alter_table("Tasks", schema=None, copy_from=Task.__table__) as batch_op:
        batch_op.alter_column(
            "parent_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "privacy_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "task_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
        )

    with op.batch_alter_table("UnitTypes", schema=None, copy_from=UnitType.__table__) as batch_op:
        batch_op.alter_column(
            "unit_type_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
        )

    with op.batch_alter_table("Users", schema=None, copy_from=User.__table__) as batch_op:
        batch_op.alter_column(
            "user_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
        )

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("Users", schema=None, copy_from=User.__table__) as batch_op:
        batch_op.alter_column(
            "user_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
        )

    with op.batch_alter_table("UnitTypes", schema=None, copy_from=UnitType.__table__) as batch_op:
        batch_op.alter_column(
            "unit_type_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
        )

    with op.batch_alter_table("Tasks", schema=None, copy_from=Task.__table__) as batch_op:
        batch_op.alter_column(
            "task_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
        )
        batch_op.alter_column(
            "privacy_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "parent_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=False,
        )

    with op.batch_alter_table("Tags", schema=None, copy_from=Tag.__table__) as batch_op:
        batch_op.alter_column(
            "tag_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
        )

    with op.batch_alter_table(
        "TaggedItems", schema=None, copy_from=TaggedItem.__table__
    ) as batch_op:
        batch_op.alter_column(
            "tagged_item_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
        )
        batch_op.alter_column(
            "tagged_by_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "tag_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "item_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=False,
        )

    with op.batch_alter_table("Synonyms", schema=None, copy_from=Synonym.__table__) as batch_op:
        batch_op.alter_column(
            "synonym_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
        )
        batch_op.alter_column(
            "entity",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=False,
        )

    with op.batch_alter_table("States", schema=None, copy_from=State.__table__) as batch_op:
        batch_op.alter_column(
            "state_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
        )
        batch_op.alter_column(
            "source_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "sensor_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "privacy_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=True,
        )

    with op.batch_alter_table("Sensors", schema=None, copy_from=Sensor.__table__) as batch_op:
        batch_op.alter_column(
            "sensor_type_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "sensor_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
        )
        batch_op.alter_column(
            "privacy_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "host",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=False,
        )

    with op.batch_alter_table(
        "SensorTypes", schema=None, copy_from=SensorType.__table__
    ) as batch_op:
        batch_op.alter_column(
            "sensor_type_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
        )

    with op.batch_alter_table("Privacies", schema=None, copy_from=Privacy.__table__) as batch_op:
        batch_op.alter_column(
            "privacy_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
        )

    with op.batch_alter_table("Platforms", schema=None, copy_from=Platform.__table__) as batch_op:
        batch_op.alter_column(
            "privacy_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "platform_type_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "platform_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
        )
        batch_op.alter_column(
            "nationality_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=False,
        )

    with op.batch_alter_table(
        "PlatformTypes", schema=None, copy_from=PlatformType.__table__
    ) as batch_op:
        batch_op.alter_column(
            "platform_type_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
        )

    with op.batch_alter_table(
        "Participants", schema=None, copy_from=Participant.__table__
    ) as batch_op:
        batch_op.alter_column(
            "task_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "privacy_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "platform_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "participant_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
        )

    with op.batch_alter_table(
        "Nationalities", schema=None, copy_from=Nationality.__table__
    ) as batch_op:
        batch_op.alter_column(
            "nationality_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
        )

    with op.batch_alter_table("MediaTypes", schema=None, copy_from=MediaType.__table__) as batch_op:
        batch_op.alter_column(
            "media_type_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
        )

    with op.batch_alter_table("Media", schema=None, copy_from=Media.__table__) as batch_op:
        batch_op.alter_column(
            "subject_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "source_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "sensor_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "privacy_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "platform_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "media_type_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "media_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
        )

    with op.batch_alter_table(
        "LogsHoldings", schema=None, copy_from=LogsHolding.__table__
    ) as batch_op:
        batch_op.alter_column(
            "unit_type_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "source_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "privacy_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "platform_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "logs_holding_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
        )
        batch_op.alter_column(
            "commodity_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=False,
        )

    with op.batch_alter_table("Logs", schema=None, copy_from=Log.__table__) as batch_op:
        batch_op.alter_column(
            "log_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
        )
        batch_op.alter_column(
            "id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "change_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=False,
        )

    with op.batch_alter_table("HostedBy", schema=None, copy_from=HostedBy.__table__) as batch_op:
        batch_op.alter_column(
            "subject_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "hosted_by_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
        )
        batch_op.alter_column(
            "host_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=False,
        )

    with op.batch_alter_table(
        "GeometryTypes", schema=None, copy_from=GeometryType.__table__
    ) as batch_op:
        batch_op.alter_column(
            "geo_type_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
        )

    with op.batch_alter_table(
        "GeometrySubTypes", schema=None, copy_from=GeometrySubType.__table__
    ) as batch_op:
        batch_op.alter_column(
            "geo_sub_type_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
        )

    with op.batch_alter_table("Geometries", schema=None, copy_from=Geometry1.__table__) as batch_op:
        batch_op.alter_column(
            "task_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "subject_platform_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "source_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "sensor_platform_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "privacy_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "geometry_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
        )
        batch_op.alter_column(
            "geo_type_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "geo_sub_type_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=False,
        )

    with op.batch_alter_table(
        "Extractions", schema=None, copy_from=Extraction.__table__
    ) as batch_op:
        batch_op.alter_column(
            "extraction_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
        )

    with op.batch_alter_table("Datafiles", schema=None, copy_from=Datafile.__table__) as batch_op:
        batch_op.alter_column(
            "privacy_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "datafile_type_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "datafile_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
        )

    with op.batch_alter_table(
        "DatafileTypes", schema=None, copy_from=DatafileType.__table__
    ) as batch_op:
        batch_op.alter_column(
            "datafile_type_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
        )

    with op.batch_alter_table("Contacts", schema=None, copy_from=Contact.__table__) as batch_op:
        batch_op.alter_column(
            "subject_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "source_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "sensor_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "privacy_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "contact_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
        )

    with op.batch_alter_table(
        "ContactTypes", schema=None, copy_from=ContactType.__table__
    ) as batch_op:
        batch_op.alter_column(
            "contact_type_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
        )

    with op.batch_alter_table(
        "ConfidenceLevels", schema=None, copy_from=ConfidenceLevel.__table__
    ) as batch_op:
        batch_op.alter_column(
            "confidence_level_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
        )

    with op.batch_alter_table(
        "CommodityTypes", schema=None, copy_from=CommodityType.__table__
    ) as batch_op:
        batch_op.alter_column(
            "commodity_type_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
        )

    with op.batch_alter_table("Comments", schema=None, copy_from=Comment.__table__) as batch_op:
        batch_op.alter_column(
            "source_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "privacy_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "platform_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "comment_type_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "comment_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
        )

    with op.batch_alter_table(
        "CommentTypes", schema=None, copy_from=CommentType.__table__
    ) as batch_op:
        batch_op.alter_column(
            "comment_type_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
        )

    with op.batch_alter_table(
        "ClassificationTypes", schema=None, copy_from=ClassificationType.__table__
    ) as batch_op:
        batch_op.alter_column(
            "class_type_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
        )

    with op.batch_alter_table("Changes", schema=None, copy_from=Change.__table__) as batch_op:
        batch_op.alter_column(
            "change_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
        )

    with op.batch_alter_table(
        "Activations", schema=None, copy_from=Activation.__table__
    ) as batch_op:
        batch_op.alter_column(
            "source_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "sensor_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "privacy_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "activation_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
        )

    # ### end Alembic commands ###
