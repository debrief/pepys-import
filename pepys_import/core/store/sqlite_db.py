from datetime import datetime
from uuid import uuid4

from geoalchemy2 import Geometry
from sqlalchemy import DATE, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.sqlite import REAL, TIMESTAMP
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
from pepys_import.core.store.db_base import BaseSpatiaLite
from pepys_import.core.store.db_status import TableTypes
from pepys_import.utils.sqlalchemy_utils import UUIDType


# Metadata Tables
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


class Task(BaseSpatiaLite, TaskMixin):
    __tablename__ = constants.TASK
    table_type = TableTypes.METADATA
    table_type_id = 4

    task_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), CheckConstraint("name <> ''", name="ck_Tasks_name"), nullable=False)
    parent_id = Column(UUIDType, ForeignKey("Tasks.task_id", onupdate="cascade"), nullable=False)
    start = Column(TIMESTAMP, nullable=False)
    end = Column(TIMESTAMP, nullable=False)
    environment = deferred(Column(String(150)))
    location = deferred(Column(String(150)))
    privacy_id = Column(
        UUIDType, ForeignKey("Privacies.privacy_id", onupdate="cascade"), nullable=False
    )
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


class Synonym(BaseSpatiaLite, SynonymMixin):
    __tablename__ = constants.SYNONYM
    table_type = TableTypes.METADATA
    table_type_id = 7

    synonym_id = Column(UUIDType, primary_key=True, default=uuid4)
    table = Column(
        String(150), CheckConstraint("\"table\" <> ''", name="ck_Synonyms_table"), nullable=False
    )
    entity = Column(UUIDType, nullable=False)
    synonym = Column(
        String(150), CheckConstraint("synonym <> ''", name="ck_Synonyms_synonym"), nullable=False
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class Change(BaseSpatiaLite):
    __tablename__ = constants.CHANGE
    table_type = TableTypes.METADATA
    table_type_id = 8

    change_id = Column(UUIDType, primary_key=True, default=uuid4)
    user = Column(
        String(150), CheckConstraint("user <> ''", name="ck_Changes_user"), nullable=False
    )
    modified = Column(DATE, nullable=False)
    reason = Column(
        String(500), CheckConstraint("reason <> ''", name="ck_Changes_reason"), nullable=False
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class Log(BaseSpatiaLite, LogMixin):
    __tablename__ = constants.LOG
    table_type = TableTypes.METADATA
    table_type_id = 9

    log_id = Column(UUIDType, primary_key=True, default=uuid4)
    table = Column(
        String(150), CheckConstraint("\"table\" <> ''", name="ck_Logs_table"), nullable=False
    )
    id = Column(UUIDType, nullable=False)
    field = Column(String(150))
    new_value = Column(String(150))
    change_id = Column(
        UUIDType, ForeignKey("Changes.change_id", onupdate="cascade"), nullable=False
    )
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


class Tag(BaseSpatiaLite):
    __tablename__ = constants.TAG
    table_type = TableTypes.METADATA
    table_type_id = 11

    tag_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False)
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


# Reference Tables
class PlatformType(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.PLATFORM_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 13

    platform_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_PlatformTypes_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class Nationality(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.NATIONALITY
    table_type = TableTypes.REFERENCE
    table_type_id = 14

    nationality_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_Nationalities_name"),
        nullable=False,
        unique=True,
    )
    priority = Column(Integer)
    created_date = Column(DateTime, default=datetime.utcnow)


class GeometryType(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.GEOMETRY_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 15

    geo_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_GeometryTypes_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class GeometrySubType(BaseSpatiaLite):
    __tablename__ = constants.GEOMETRY_SUBTYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 16

    geo_sub_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(
        String(150), CheckConstraint("name <> ''", name="ck_GeometrySubTypes_name"), nullable=False
    )
    parent = Column(
        UUIDType, ForeignKey("GeometryTypes.geo_type_id", onupdate="cascade"), nullable=False
    )
    created_date = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("name", "parent", name="uq_GeometrySubTypes_name_parent"),)


class User(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.USER
    table_type = TableTypes.REFERENCE
    table_type_id = 17

    user_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_Users_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class UnitType(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.UNIT_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 18

    unit_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_UnitTypes_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class ClassificationType(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.CLASSIFICATION_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 19

    class_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_ClassificationTypes_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class ContactType(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.CONTACT_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 20

    contact_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_ContactTypes_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class SensorType(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.SENSOR_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 21

    sensor_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_SensorTypes_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class Privacy(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.PRIVACY
    table_type = TableTypes.REFERENCE
    table_type_id = 22

    privacy_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_Privacies_name"),
        nullable=False,
        unique=True,
    )
    level = Column(Integer, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class DatafileType(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.DATAFILE_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 23

    datafile_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_DatafileTypes_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class MediaType(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.MEDIA_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 24

    media_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_MediaTypes_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class CommentType(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.COMMENT_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 25

    comment_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_CommentTypes_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class CommodityType(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.COMMODITY_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 26

    commodity_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_CommodityTypes_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class ConfidenceLevel(BaseSpatiaLite, ReferenceRepr):
    __tablename__ = constants.CONFIDENCE_LEVEL
    table_type = TableTypes.REFERENCE
    table_type_id = 27

    confidence_level_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_ConfidenceLevels_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


# Measurements Tables
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
        Column("location", Geometry(geometry_type="POINT", srid=4326, management=True))
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
    content = Column(
        Text, CheckConstraint("content <> ''", name="ck_Comments_content"), nullable=False
    )
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
        "geometry", Geometry(geometry_type="GEOMETRY", srid=4326, management=True), nullable=False,
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


class Media(BaseSpatiaLite, MediaMixin, ElevationPropertyMixin, LocationPropertyMixin):
    __tablename__ = constants.MEDIA
    table_type = TableTypes.MEASUREMENT
    table_type_id = 34

    media_id = Column(UUIDType, primary_key=True, default=uuid4)
    platform_id = Column(UUIDType, ForeignKey("Platforms.platform_id", onupdate="cascade"))
    subject_id = Column(UUIDType, ForeignKey("Platforms.platform_id", onupdate="cascade"))
    sensor_id = Column(UUIDType, ForeignKey("Sensors.sensor_id", onupdate="cascade"))
    _location = deferred(
        Column("location", Geometry(geometry_type="POINT", srid=4326, management=True))
    )
    _elevation = deferred(Column("elevation", REAL))
    time = Column(TIMESTAMP)
    media_type_id = Column(
        UUIDType, ForeignKey("MediaTypes.media_type_id", onupdate="cascade"), nullable=False
    )
    url = deferred(
        Column(String(150), CheckConstraint("url <> ''", name="ck_Media_url"), nullable=False)
    )
    source_id = Column(
        UUIDType, ForeignKey("Datafiles.datafile_id", onupdate="cascade"), nullable=False
    )
    privacy_id = Column(UUIDType, ForeignKey("Privacies.privacy_id", onupdate="cascade"))
    remarks = Column(Text)
    created_date = Column(DateTime, default=datetime.utcnow)
