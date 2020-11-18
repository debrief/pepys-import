from datetime import datetime
from uuid import uuid4

from geoalchemy2 import Geometry
from sqlalchemy import DATE, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, TIMESTAMP, UUID
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import (  # used to defer fetching attributes unless it's specifically called
    deferred,
    relationship,
)
from sqlalchemy.sql.schema import CheckConstraint, UniqueConstraint

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
    SynonymMixin,
    TaggedItemMixin,
    TaskMixin,
)
from pepys_import.core.store.db_base import BasePostGIS
from pepys_import.core.store.db_status import TableTypes


# Metadata Tables
class HostedBy(BasePostGIS, HostedByMixin):
    __tablename__ = constants.HOSTED_BY
    table_type = TableTypes.METADATA
    table_type_id = 1
    __table_args__ = {"schema": "pepys"}

    hosted_by_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    subject_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Platforms.platform_id", onupdate="cascade"),
        nullable=False,
    )
    host_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Platforms.platform_id", onupdate="cascade"),
        nullable=False,
    )
    hosted_from = Column(DATE, nullable=False)
    host_to = Column(DATE, nullable=False)
    privacy_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Privacies.privacy_id", onupdate="cascade"),
        nullable=False,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class Sensor(BasePostGIS, SensorMixin):
    __tablename__ = constants.SENSOR
    table_type = TableTypes.METADATA
    table_type_id = 2
    __table_args__ = (
        UniqueConstraint("name", "host", name="uq_sensors_name_host"),
        {"schema": "pepys"},
    )

    sensor_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(
        String(150), CheckConstraint("name <> ''", name="ck_Sensors_name"), nullable=False
    )
    sensor_type_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.SensorTypes.sensor_type_id", onupdate="cascade"),
        nullable=False,
    )
    host = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Platforms.platform_id", onupdate="cascade"),
        nullable=False,
    )
    privacy_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Privacies.privacy_id", onupdate="cascade"),
        nullable=False,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class Platform(BasePostGIS, PlatformMixin):
    __tablename__ = constants.PLATFORM
    table_type = TableTypes.METADATA
    table_type_id = 3
    __table_args__ = (
        UniqueConstraint(
            "name", "nationality_id", "identifier", name="uq_Platform_name_nat_identifier"
        ),
        {"schema": "pepys"},
    )

    platform_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
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
        UUID(as_uuid=True),
        ForeignKey("pepys.Nationalities.nationality_id", onupdate="cascade"),
        nullable=False,
    )
    platform_type_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.PlatformTypes.platform_type_id", onupdate="cascade"),
        nullable=False,
    )
    privacy_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Privacies.privacy_id", onupdate="cascade"),
        nullable=False,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class Task(BasePostGIS, TaskMixin):
    __tablename__ = constants.TASK
    table_type = TableTypes.METADATA
    table_type_id = 4
    __table_args__ = {"schema": "pepys"}

    task_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150), CheckConstraint("name <> ''", name="ck_Tasks_name"), nullable=False)
    parent_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Tasks.task_id", onupdate="cascade"), nullable=False
    )
    start = Column(TIMESTAMP, nullable=False)
    end = Column(TIMESTAMP, nullable=False)
    environment = deferred(Column(String(150)))
    location = deferred(Column(String(150)))
    privacy_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Privacies.privacy_id", onupdate="cascade"),
        nullable=False,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class Participant(BasePostGIS, ParticipantMixin):
    __tablename__ = constants.PARTICIPANT
    table_type = TableTypes.METADATA
    table_type_id = 5
    __table_args__ = {"schema": "pepys"}

    participant_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    platform_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Platforms.platform_id", onupdate="cascade"),
        nullable=False,
    )
    task_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Tasks.task_id", onupdate="cascade"), nullable=False
    )
    start = Column(TIMESTAMP)
    end = Column(TIMESTAMP)
    force = Column(String(150))
    privacy_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Privacies.privacy_id", onupdate="cascade"),
        nullable=False,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class Datafile(BasePostGIS, DatafileMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.measurements = dict()

    __tablename__ = constants.DATAFILE
    table_type = TableTypes.METADATA
    table_type_id = 6  # Only needed for tables referenced by Entry table
    __table_args__ = (
        UniqueConstraint("size", "hash", name="uq_Datafile_size_hash"),
        {"schema": "pepys"},
    )

    datafile_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    simulated = deferred(Column(Boolean, nullable=False))
    privacy_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Privacies.privacy_id", onupdate="cascade"),
        nullable=False,
    )
    datafile_type_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.DatafileTypes.datafile_type_id", onupdate="cascade"),
        nullable=False,
    )
    reference = Column(String(150))
    url = Column(String(150))
    size = deferred(Column(Integer, nullable=False))
    hash = deferred(
        Column(String(32), CheckConstraint("hash <> ''", name="ck_Datafiles_hash"), nullable=False)
    )
    created_date = deferred(Column(DateTime, default=datetime.utcnow))


class Synonym(BasePostGIS, SynonymMixin):
    __tablename__ = constants.SYNONYM
    table_type = TableTypes.METADATA
    table_type_id = 7
    __table_args__ = {"schema": "pepys"}

    synonym_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    table = Column(
        String(150), CheckConstraint("\"table\" <> ''", name="ck_Synonyms_table"), nullable=False
    )
    entity = Column(UUID(as_uuid=True), nullable=False)
    synonym = Column(
        String(150), CheckConstraint("synonym <> ''", name="ck_Synonyms_synonym"), nullable=False
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class Change(BasePostGIS):
    __tablename__ = constants.CHANGE
    table_type = TableTypes.METADATA
    table_type_id = 8
    __table_args__ = {"schema": "pepys"}

    change_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user = Column(
        String(150), CheckConstraint("user <> ''", name="ck_Changes_user"), nullable=False
    )
    modified = Column(DATE, nullable=False)
    reason = Column(
        String(500), CheckConstraint("reason <> ''", name="ck_Changes_reason"), nullable=False
    )
    datafile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Datafiles.datafile_id", onupdate="cascade"),
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class Log(BasePostGIS, LogMixin):
    __tablename__ = constants.LOG
    table_type = TableTypes.METADATA
    table_type_id = 9
    __table_args__ = {"schema": "pepys"}

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    table = Column(
        String(150), CheckConstraint("\"table\" <> ''", name="ck_Logs_table"), nullable=False
    )
    id = Column(UUID(as_uuid=True), nullable=False)
    field = Column(String(150))
    new_value = Column(String(150))
    change_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Changes.change_id", onupdate="cascade"),
        nullable=False,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class Extraction(BasePostGIS):
    __tablename__ = constants.EXTRACTION
    table_type = TableTypes.METADATA
    table_type_id = 10
    __table_args__ = {"schema": "pepys"}

    extraction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    table = Column(String(150), nullable=False)
    field = Column(String(150), nullable=False)
    chars = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Tag(BasePostGIS):
    __tablename__ = constants.TAG
    table_type = TableTypes.METADATA
    table_type_id = 11
    __table_args__ = {"schema": "pepys"}

    tag_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class TaggedItem(BasePostGIS, TaggedItemMixin):
    __tablename__ = constants.TAGGED_ITEM
    table_type = TableTypes.METADATA
    table_type_id = 12
    __table_args__ = {"schema": "pepys"}

    tagged_item_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tag_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Tags.tag_id", onupdate="cascade"), nullable=False
    )
    item_id = Column(UUID(as_uuid=True), nullable=False)
    tagged_by_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Users.user_id", onupdate="cascade"), nullable=False
    )
    private = Column(Boolean, nullable=False)
    tagged_on = Column(DATE, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


# Reference Tables
class PlatformType(BasePostGIS, ReferenceRepr):
    __tablename__ = constants.PLATFORM_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 13
    __table_args__ = {"schema": "pepys"}

    platform_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_PlatformTypes_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class Nationality(BasePostGIS, ReferenceRepr):
    __tablename__ = constants.NATIONALITY
    table_type = TableTypes.REFERENCE
    table_type_id = 14
    __table_args__ = {"schema": "pepys"}

    nationality_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_Nationalities_name"),
        nullable=False,
        unique=True,
    )
    priority = Column(Integer)
    created_date = Column(DateTime, default=datetime.utcnow)


class GeometryType(BasePostGIS, ReferenceRepr):
    __tablename__ = constants.GEOMETRY_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 15
    __table_args__ = {"schema": "pepys"}

    geo_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_GeometryTypes_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class GeometrySubType(BasePostGIS):
    __tablename__ = constants.GEOMETRY_SUBTYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 16
    __table_args__ = (
        UniqueConstraint("name", "parent", name="uq_GeometrySubType_name_parent"),
        {"schema": "pepys"},
    )

    geo_sub_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(
        String(150), CheckConstraint("name <> ''", name="ck_GeometrySubTypes_name"), nullable=False
    )
    parent = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.GeometryTypes.geo_type_id", onupdate="cascade"),
        nullable=False,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class User(BasePostGIS, ReferenceRepr):
    __tablename__ = constants.USER
    table_type = TableTypes.REFERENCE
    table_type_id = 17
    __table_args__ = {"schema": "pepys"}

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_Users_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class UnitType(BasePostGIS, ReferenceRepr):
    __tablename__ = constants.UNIT_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 18
    __table_args__ = {"schema": "pepys"}

    unit_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_UnitTypes_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class ClassificationType(BasePostGIS, ReferenceRepr):
    __tablename__ = constants.CLASSIFICATION_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 19
    __table_args__ = {"schema": "pepys"}

    class_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_ClassificationTypes_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class ContactType(BasePostGIS, ReferenceRepr):
    __tablename__ = constants.CONTACT_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 20
    __table_args__ = {"schema": "pepys"}

    contact_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_ContactTypes_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class SensorType(BasePostGIS, ReferenceRepr):
    __tablename__ = constants.SENSOR_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 21
    __table_args__ = {"schema": "pepys"}

    sensor_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_SensorTypes_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class Privacy(BasePostGIS, ReferenceRepr):
    __tablename__ = constants.PRIVACY
    table_type = TableTypes.REFERENCE
    table_type_id = 22
    __table_args__ = {"schema": "pepys"}

    privacy_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    level = Column(Integer, nullable=False)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_Privacies_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class DatafileType(BasePostGIS, ReferenceRepr):
    __tablename__ = constants.DATAFILE_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 23
    __table_args__ = {"schema": "pepys"}

    datafile_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_DatafileTypes_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class MediaType(BasePostGIS, ReferenceRepr):
    __tablename__ = constants.MEDIA_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 24
    __table_args__ = {"schema": "pepys"}

    media_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_MediaTypes_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class CommentType(BasePostGIS, ReferenceRepr):
    __tablename__ = constants.COMMENT_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 25
    __table_args__ = {"schema": "pepys"}

    comment_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_CommentTypes_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class CommodityType(BasePostGIS, ReferenceRepr):
    __tablename__ = constants.COMMODITY_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 26
    __table_args__ = {"schema": "pepys"}

    commodity_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_CommodityTypes_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class ConfidenceLevel(BasePostGIS, ReferenceRepr):
    __tablename__ = constants.CONFIDENCE_LEVEL
    table_type = TableTypes.REFERENCE
    table_type_id = 27  # Only needed for tables referenced by Entry table
    __table_args__ = {"schema": "pepys"}

    confidence_level_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_ConfidenceLevels_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


# Measurements Tables
class State(BasePostGIS, StateMixin, ElevationPropertyMixin, LocationPropertyMixin):
    __tablename__ = constants.STATE
    table_type = TableTypes.MEASUREMENT
    table_type_id = 28
    __table_args__ = {"schema": "pepys"}

    state_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    time = Column(TIMESTAMP, nullable=False)
    sensor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Sensors.sensor_id", onupdate="cascade"),
        nullable=False,
    )
    _location = deferred(Column("location", Geometry(geometry_type="POINT", srid=4326)))
    _elevation = deferred(Column("elevation", DOUBLE_PRECISION))
    _heading = deferred(Column("heading", DOUBLE_PRECISION))
    _course = deferred(Column("course", DOUBLE_PRECISION))
    _speed = deferred(Column("speed", DOUBLE_PRECISION))
    source_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Datafiles.datafile_id", onupdate="cascade"),
        nullable=False,
    )
    privacy_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Privacies.privacy_id", onupdate="cascade")
    )
    remarks = Column(Text)
    created_date = Column(DateTime, default=datetime.utcnow)

    @declared_attr
    def platform(self):
        return relationship(
            "Platform",
            secondary="pepys.Sensors",
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


class Contact(BasePostGIS, ContactMixin, LocationPropertyMixin, ElevationPropertyMixin):
    __tablename__ = constants.CONTACT
    table_type = TableTypes.MEASUREMENT
    table_type_id = 29
    __table_args__ = {"schema": "pepys"}

    contact_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150))
    sensor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Sensors.sensor_id", onupdate="cascade"),
        nullable=False,
    )
    time = Column(TIMESTAMP, nullable=False)
    _bearing = deferred(Column("bearing", DOUBLE_PRECISION))
    _rel_bearing = deferred(Column("rel_bearing", DOUBLE_PRECISION))
    _ambig_bearing = deferred(Column("ambig_bearing", DOUBLE_PRECISION))
    _freq = deferred(Column("freq", DOUBLE_PRECISION))
    _range = deferred(Column("range", DOUBLE_PRECISION))
    _location = deferred(Column("location", Geometry(geometry_type="POINT", srid=4326)))
    _elevation = deferred(Column("elevation", DOUBLE_PRECISION))
    _major = deferred(Column("major", DOUBLE_PRECISION))
    _minor = deferred(Column("minor", DOUBLE_PRECISION))
    _orientation = deferred(Column("orientation", DOUBLE_PRECISION))
    classification = deferred(
        Column(UUID(as_uuid=True), ForeignKey("pepys.ClassificationTypes.class_type_id"))
    )
    confidence = deferred(
        Column(UUID(as_uuid=True), ForeignKey("pepys.ConfidenceLevels.confidence_level_id"))
    )
    contact_type = deferred(
        Column(UUID(as_uuid=True), ForeignKey("pepys.ContactTypes.contact_type_id"))
    )
    _mla = deferred(Column("mla", DOUBLE_PRECISION))
    _soa = deferred(Column("soa", DOUBLE_PRECISION))
    track_number = Column(String(20))
    subject_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Platforms.platform_id", onupdate="cascade")
    )
    source_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Datafiles.datafile_id", onupdate="cascade"),
        nullable=False,
    )
    privacy_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Privacies.privacy_id", onupdate="cascade")
    )
    remarks = Column(Text)
    created_date = Column(DateTime, default=datetime.utcnow)

    @declared_attr
    def platform(self):
        return relationship(
            "Platform",
            secondary="pepys.Sensors",
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


class Activation(BasePostGIS, ActivationMixin):
    __tablename__ = constants.ACTIVATION
    table_type = TableTypes.MEASUREMENT
    table_type_id = 30
    __table_args__ = {"schema": "pepys"}

    activation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150))
    sensor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Sensors.sensor_id", onupdate="cascade"),
        nullable=False,
    )
    start = deferred(Column(TIMESTAMP))
    end = deferred(Column(TIMESTAMP))
    _min_range = deferred(Column("min_range", DOUBLE_PRECISION))
    _max_range = deferred(Column("max_range", DOUBLE_PRECISION))
    _left_arc = deferred(Column("left_arc", DOUBLE_PRECISION))
    _right_arc = deferred(Column("right_arc", DOUBLE_PRECISION))
    source_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Datafiles.datafile_id", onupdate="cascade"),
        nullable=False,
    )
    privacy_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Privacies.privacy_id", onupdate="cascade")
    )
    remarks = Column(Text)
    created_date = Column(DateTime, default=datetime.utcnow)


class LogsHolding(BasePostGIS, LogsHoldingMixin):
    __tablename__ = constants.LOGS_HOLDING
    table_type = TableTypes.MEASUREMENT
    table_type_id = 31
    __table_args__ = {"schema": "pepys"}

    logs_holding_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    time = Column(TIMESTAMP, nullable=False)
    commodity_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.CommodityTypes.commodity_type_id", onupdate="cascade"),
        nullable=False,
    )
    quantity = Column(DOUBLE_PRECISION, nullable=False)
    unit_type_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.UnitTypes.unit_type_id", onupdate="cascade"),
        nullable=False,
    )
    platform_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Platforms.platform_id", onupdate="cascade"),
        nullable=False,
    )
    comment = Column(Text, nullable=False)
    source_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Datafiles.datafile_id", onupdate="cascade"),
        nullable=False,
    )
    privacy_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Privacies.privacy_id", onupdate="cascade")
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class Comment(BasePostGIS, CommentMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sensor_name = "N/A"

    __tablename__ = constants.COMMENT
    table_type = TableTypes.MEASUREMENT
    table_type_id = 32
    __table_args__ = {"schema": "pepys"}

    comment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    platform_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Platforms.platform_id", onupdate="cascade")
    )
    time = Column(TIMESTAMP, nullable=False)
    comment_type_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.CommentTypes.comment_type_id", onupdate="cascade"),
        nullable=False,
    )
    content = Column(
        Text, CheckConstraint("content <> ''", name="ck_Comment_content"), nullable=False
    )
    source_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Datafiles.datafile_id", onupdate="cascade"),
        nullable=False,
    )
    privacy_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Privacies.privacy_id", onupdate="cascade")
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class Geometry1(BasePostGIS, GeometryMixin):
    __tablename__ = constants.GEOMETRY
    table_type = TableTypes.MEASUREMENT
    table_type_id = 33
    __table_args__ = {"schema": "pepys"}

    geometry_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    _geometry = Column("geometry", Geometry(srid=4326), nullable=False)
    name = Column(String(150))
    geo_type_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.GeometryTypes.geo_type_id", onupdate="cascade"),
        nullable=False,
    )
    geo_sub_type_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.GeometrySubTypes.geo_sub_type_id", onupdate="cascade"),
        nullable=False,
    )
    start = Column(TIMESTAMP)
    end = Column(TIMESTAMP)
    task_id = Column(UUID(as_uuid=True), ForeignKey("pepys.Tasks.task_id", onupdate="cascade"))
    subject_platform_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Platforms.platform_id", onupdate="cascade")
    )
    sensor_platform_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Platforms.platform_id", onupdate="cascade")
    )
    source_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Datafiles.datafile_id", onupdate="cascade"),
        nullable=False,
    )
    privacy_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Privacies.privacy_id", onupdate="cascade")
    )
    remarks = Column(Text)
    created_date = Column(DateTime, default=datetime.utcnow)


class Media(BasePostGIS, MediaMixin, ElevationPropertyMixin, LocationPropertyMixin):
    __tablename__ = constants.MEDIA
    table_type = TableTypes.MEASUREMENT
    table_type_id = 34
    __table_args__ = {"schema": "pepys"}

    media_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    platform_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Platforms.platform_id", onupdate="cascade")
    )
    subject_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Platforms.platform_id", onupdate="cascade")
    )
    sensor_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Sensors.sensor_id", onupdate="cascade")
    )
    _location = deferred(Column("location", Geometry(geometry_type="POINT", srid=4326)))
    _elevation = deferred(Column("elevation", DOUBLE_PRECISION))
    time = Column(TIMESTAMP)
    media_type_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.MediaTypes.media_type_id", onupdate="cascade"),
        nullable=False,
    )
    url = deferred(
        Column(String(150), CheckConstraint("url <> ''", name="ck_Media_url"), nullable=False)
    )
    source_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Datafiles.datafile_id", onupdate="cascade"),
        nullable=False,
    )
    privacy_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Privacies.privacy_id", onupdate="cascade")
    )
    remarks = Column(Text)
    created_date = Column(DateTime, default=datetime.utcnow)
