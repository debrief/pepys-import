from datetime import datetime
from uuid import uuid4

from geoalchemy2 import Geometry
from sqlalchemy import DATE, Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, TIMESTAMP, UUID
from sqlalchemy.orm import (  # used to defer fetching attributes unless it's specifically called
    deferred,
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
    SensorMixin,
    StateMixin,
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
        UUID(as_uuid=True), ForeignKey("pepys.Platforms.platform_id"), nullable=False
    )
    host_id = Column(UUID(as_uuid=True), ForeignKey("pepys.Platforms.platform_id"), nullable=False)
    hosted_from = Column(DATE, nullable=False)
    host_to = Column(DATE, nullable=False)
    privacy_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Privacies.privacy_id"), nullable=False
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class Sensor(BasePostGIS, SensorMixin):
    __tablename__ = constants.SENSOR
    table_type = TableTypes.METADATA
    table_type_id = 2
    __table_args__ = {"schema": "pepys"}

    sensor_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False)
    sensor_type_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.SensorTypes.sensor_type_id"), nullable=False,
    )
    host = Column(UUID(as_uuid=True), ForeignKey("pepys.Platforms.platform_id"), nullable=False)
    privacy_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Privacies.privacy_id"), nullable=False
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class Platform(BasePostGIS, PlatformMixin):
    __tablename__ = constants.PLATFORM
    table_type = TableTypes.METADATA
    table_type_id = 3
    __table_args__ = {"schema": "pepys"}

    platform_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False)
    pennant = deferred(Column(String(10)))
    trigraph = deferred(Column(String(3)))
    quadgraph = deferred(Column(String(4)))
    nationality_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Nationalities.nationality_id"), nullable=False,
    )
    platform_type_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.PlatformTypes.platform_type_id"), nullable=False,
    )
    privacy_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Privacies.privacy_id"), nullable=False
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class Task(BasePostGIS, TaskMixin):
    __tablename__ = constants.TASK
    table_type = TableTypes.METADATA
    table_type_id = 4
    __table_args__ = {"schema": "pepys"}

    task_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("pepys.Tasks.task_id"), nullable=False)
    start = Column(TIMESTAMP, nullable=False)
    end = Column(TIMESTAMP, nullable=False)
    environment = deferred(Column(String(150)))
    location = deferred(Column(String(150)))
    privacy_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Privacies.privacy_id"), nullable=False
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class Participant(BasePostGIS, ParticipantMixin):
    __tablename__ = constants.PARTICIPANT
    table_type = TableTypes.METADATA
    table_type_id = 5
    __table_args__ = {"schema": "pepys"}

    participant_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    platform_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Platforms.platform_id"), nullable=False
    )
    task_id = Column(UUID(as_uuid=True), ForeignKey("pepys.Tasks.task_id"), nullable=False)
    start = Column(TIMESTAMP)
    end = Column(TIMESTAMP)
    force = Column(String(150))
    privacy_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Privacies.privacy_id"), nullable=False
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class Datafile(BasePostGIS, DatafileMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.measurements = dict()

    __tablename__ = constants.DATAFILE
    table_type = TableTypes.METADATA
    table_type_id = 6  # Only needed for tables referenced by Entry table
    __table_args__ = {"schema": "pepys"}

    datafile_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    simulated = deferred(Column(Boolean, nullable=False))
    privacy_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Privacies.privacy_id"), nullable=False
    )
    datafile_type_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.DatafileTypes.datafile_type_id"), nullable=False,
    )
    reference = Column(String(150))
    url = Column(String(150))
    size = Column(Integer, nullable=False)
    hash = deferred(Column(String(32), nullable=False))
    created_date = deferred(Column(DateTime, default=datetime.utcnow))


class Synonym(BasePostGIS):
    __tablename__ = constants.SYNONYM
    table_type = TableTypes.METADATA
    table_type_id = 7
    __table_args__ = {"schema": "pepys"}

    synonym_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    table = Column(String(150), nullable=False)
    entity = Column(UUID(as_uuid=True), nullable=False)
    synonym = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Change(BasePostGIS):
    __tablename__ = constants.CHANGE
    table_type = TableTypes.METADATA
    table_type_id = 8
    __table_args__ = {"schema": "pepys"}

    change_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user = Column(String(150), nullable=False)
    modified = Column(DATE, nullable=False)
    reason = Column(String(500), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Log(BasePostGIS, LogMixin):
    __tablename__ = constants.LOG
    table_type = TableTypes.METADATA
    table_type_id = 9
    __table_args__ = {"schema": "pepys"}

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    table = Column(String(150), nullable=False)
    id = Column(UUID(as_uuid=True), nullable=False)
    field = Column(String(150))
    new_value = Column(String(150))
    change_id = Column(UUID(as_uuid=True), ForeignKey("pepys.Changes.change_id"), nullable=False)
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
    tag_id = Column(UUID(as_uuid=True), ForeignKey("pepys.Tags.tag_id"), nullable=False)
    item_id = Column(UUID(as_uuid=True), nullable=False)
    tagged_by_id = Column(UUID(as_uuid=True), ForeignKey("pepys.Users.user_id"), nullable=False)
    private = Column(Boolean, nullable=False)
    tagged_on = Column(DATE, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


# Reference Tables
class PlatformType(BasePostGIS):
    __tablename__ = constants.PLATFORM_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 13
    __table_args__ = {"schema": "pepys"}

    platform_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class Nationality(BasePostGIS):
    __tablename__ = constants.NATIONALITY
    table_type = TableTypes.REFERENCE
    table_type_id = 14
    __table_args__ = {"schema": "pepys"}

    nationality_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class GeometryType(BasePostGIS):
    __tablename__ = constants.GEOMETRY_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 15
    __table_args__ = {"schema": "pepys"}

    geo_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class GeometrySubType(BasePostGIS):
    __tablename__ = constants.GEOMETRY_SUBTYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 16
    __table_args__ = {"schema": "pepys"}

    geo_sub_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    # parent = Column(UUID(as_uuid=True), ForeignKey("pepys.GeometryTypes.geometry_type_id"))
    parent = Column(UUID, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class User(BasePostGIS):
    __tablename__ = constants.USER
    table_type = TableTypes.REFERENCE
    table_type_id = 17
    __table_args__ = {"schema": "pepys"}

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class UnitType(BasePostGIS):
    __tablename__ = constants.UNIT_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 18
    __table_args__ = {"schema": "pepys"}

    unit_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    units = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class ClassificationType(BasePostGIS):
    __tablename__ = constants.CLASSIFICATION_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 19
    __table_args__ = {"schema": "pepys"}

    class_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class ContactType(BasePostGIS):
    __tablename__ = constants.CONTACT_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 20
    __table_args__ = {"schema": "pepys"}

    contact_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class SensorType(BasePostGIS):
    __tablename__ = constants.SENSOR_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 21
    __table_args__ = {"schema": "pepys"}

    sensor_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class Privacy(BasePostGIS):
    __tablename__ = constants.PRIVACY
    table_type = TableTypes.REFERENCE
    table_type_id = 22
    __table_args__ = {"schema": "pepys"}

    privacy_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class DatafileType(BasePostGIS):
    __tablename__ = constants.DATAFILE_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 23
    __table_args__ = {"schema": "pepys"}

    datafile_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class MediaType(BasePostGIS):
    __tablename__ = constants.MEDIA_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 24
    __table_args__ = {"schema": "pepys"}

    media_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class CommentType(BasePostGIS):
    __tablename__ = constants.COMMENT_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 25
    __table_args__ = {"schema": "pepys"}

    comment_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class CommodityType(BasePostGIS):
    __tablename__ = constants.COMMODITY_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 26
    __table_args__ = {"schema": "pepys"}

    commodity_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class ConfidenceLevel(BasePostGIS):
    __tablename__ = constants.CONFIDENCE_LEVEL
    table_type = TableTypes.REFERENCE
    table_type_id = 27  # Only needed for tables referenced by Entry table
    __table_args__ = {"schema": "pepys"}

    confidence_level_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


# Measurements Tables
class State(BasePostGIS, StateMixin, ElevationPropertyMixin, LocationPropertyMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sensor_name = None
        self.platform_name = None

    __tablename__ = constants.STATE
    table_type = TableTypes.MEASUREMENT
    table_type_id = 28
    __table_args__ = {"schema": "pepys"}

    state_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    time = Column(TIMESTAMP, nullable=False)
    sensor_id = Column(UUID(as_uuid=True), ForeignKey("pepys.Sensors.sensor_id"), nullable=False)
    _location = deferred(Column("location", Geometry(geometry_type="POINT", srid=4326)))
    _elevation = deferred(Column("elevation", DOUBLE_PRECISION))
    _heading = deferred(Column("heading", DOUBLE_PRECISION))
    _course = deferred(Column("course", DOUBLE_PRECISION))
    _speed = deferred(Column("speed", DOUBLE_PRECISION))
    source_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Datafiles.datafile_id"), nullable=False
    )
    privacy_id = Column(UUID(as_uuid=True), ForeignKey("pepys.Privacies.privacy_id"))
    created_date = Column(DateTime, default=datetime.utcnow)


class Contact(BasePostGIS, ContactMixin, LocationPropertyMixin, ElevationPropertyMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sensor_name = None
        self.platform_name = None

    __tablename__ = constants.CONTACT
    table_type = TableTypes.MEASUREMENT
    table_type_id = 29
    __table_args__ = {"schema": "pepys"}

    contact_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150))
    sensor_id = Column(UUID(as_uuid=True), ForeignKey("pepys.Sensors.sensor_id"), nullable=False)
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
    classification = deferred(Column(String(150)))
    confidence = deferred(Column(String(150)))
    contact_type = deferred(Column(String(150)))
    _mla = deferred(Column("mla", DOUBLE_PRECISION))
    _soa = deferred(Column("soa", DOUBLE_PRECISION))
    subject_id = Column(UUID(as_uuid=True), ForeignKey("pepys.Platforms.platform_id"))
    source_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Datafiles.datafile_id"), nullable=False
    )
    privacy_id = Column(UUID(as_uuid=True), ForeignKey("pepys.Privacies.privacy_id"))
    created_date = Column(DateTime, default=datetime.utcnow)


class Activation(BasePostGIS, ActivationMixin):
    __tablename__ = constants.ACTIVATION
    table_type = TableTypes.MEASUREMENT
    table_type_id = 30
    __table_args__ = {"schema": "pepys"}

    activation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False)
    sensor_id = Column(UUID(as_uuid=True), ForeignKey("pepys.Sensors.sensor_id"), nullable=False)
    start = deferred(Column(TIMESTAMP, nullable=False))
    end = deferred(Column(TIMESTAMP, nullable=False))
    _min_range = deferred(Column("min_range", DOUBLE_PRECISION))
    _max_range = deferred(Column("max_range", DOUBLE_PRECISION))
    _left_arc = deferred(Column("left_arc", DOUBLE_PRECISION))
    _right_arc = deferred(Column("right_arc", DOUBLE_PRECISION))
    source_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Datafiles.datafile_id"), nullable=False
    )
    privacy_id = Column(UUID(as_uuid=True), ForeignKey("pepys.Privacies.privacy_id"))
    created_date = Column(DateTime, default=datetime.utcnow)


class LogsHolding(BasePostGIS, LogsHoldingMixin):
    __tablename__ = constants.LOGS_HOLDING
    table_type = TableTypes.MEASUREMENT
    table_type_id = 31
    __table_args__ = {"schema": "pepys"}

    logs_holding_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    time = Column(TIMESTAMP, nullable=False)
    commodity_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.CommodityTypes.commodity_type_id"), nullable=False
    )
    quantity = Column(DOUBLE_PRECISION, nullable=False)
    unit_type_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.UnitTypes.unit_type_id"), nullable=False
    )
    platform_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Platforms.platform_id"), nullable=False
    )
    comment = Column(String(150), nullable=False)
    source_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Datafiles.datafile_id"), nullable=False
    )
    privacy_id = Column(UUID(as_uuid=True), ForeignKey("pepys.Privacies.privacy_id"))
    created_date = Column(DateTime, default=datetime.utcnow)


class Comment(BasePostGIS, CommentMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sensor_name = None
        self.platform_name = None

    __tablename__ = constants.COMMENT
    table_type = TableTypes.MEASUREMENT
    table_type_id = 32
    __table_args__ = {"schema": "pepys"}

    comment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    platform_id = Column(UUID(as_uuid=True), ForeignKey("pepys.Platforms.platform_id"))
    time = Column(TIMESTAMP, nullable=False)
    comment_type_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.CommentTypes.comment_type_id"), nullable=False
    )
    content = Column(String(150), nullable=False)
    source_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Datafiles.datafile_id"), nullable=False
    )
    privacy_id = Column(UUID(as_uuid=True), ForeignKey("pepys.Privacies.privacy_id"))
    created_date = Column(DateTime, default=datetime.utcnow)


class Geometry1(BasePostGIS, GeometryMixin):
    __tablename__ = constants.GEOMETRY
    table_type = TableTypes.MEASUREMENT
    table_type_id = 33
    __table_args__ = {"schema": "pepys"}

    geometry_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    geometry = Column(Geometry, nullable=False)
    name = Column(String(150), nullable=False)
    geo_type_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.GeometryTypes.geo_type_id"), nullable=False,
    )
    geo_sub_type_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.GeometrySubTypes.geo_sub_type_id"), nullable=False,
    )
    start = Column(TIMESTAMP)
    end = Column(TIMESTAMP)
    task_id = Column(UUID(as_uuid=True), ForeignKey("pepys.Tasks.task_id"))
    subject_platform_id = Column(UUID(as_uuid=True), ForeignKey("pepys.Platforms.platform_id"))
    sensor_platform_id = Column(UUID(as_uuid=True), ForeignKey("pepys.Platforms.platform_id"))
    source_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Datafiles.datafile_id"), nullable=False
    )
    privacy_id = Column(UUID(as_uuid=True), ForeignKey("pepys.Privacies.privacy_id"))
    created_date = Column(DateTime, default=datetime.utcnow)


class Media(BasePostGIS, MediaMixin, ElevationPropertyMixin, LocationPropertyMixin):
    __tablename__ = constants.MEDIA
    table_type = TableTypes.MEASUREMENT
    table_type_id = 34
    __table_args__ = {"schema": "pepys"}

    media_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    platform_id = Column(UUID(as_uuid=True), ForeignKey("pepys.Platforms.platform_id"))
    subject_id = Column(UUID(as_uuid=True), ForeignKey("pepys.Platforms.platform_id"))
    sensor_id = Column(UUID(as_uuid=True), ForeignKey("pepys.Sensors.sensor_id"))
    _location = deferred(Column("location", Geometry(geometry_type="POINT", srid=4326)))
    _elevation = deferred(Column("elevation", DOUBLE_PRECISION))
    time = Column(TIMESTAMP)
    media_type_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.MediaTypes.media_type_id"), nullable=False
    )
    url = deferred(Column(String(150), nullable=False))
    source_id = Column(
        UUID(as_uuid=True), ForeignKey("pepys.Datafiles.datafile_id"), nullable=False
    )
    privacy_id = Column(UUID(as_uuid=True), ForeignKey("pepys.Privacies.privacy_id"))
    created_date = Column(DateTime, default=datetime.utcnow)
