from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import DATE, Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.sqlite import REAL, TIMESTAMP
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import deferred, relationship

from pepys_import.core.store import constants
from pepys_import.core.store.common_db import (
    ActivationMixin,
    ContactMixin,
    DatafileMixin,
    ElevationPropertyMixin,
    LocationPropertyMixin,
    MediaMixin,
    PlatformMixin,
    SensorMixin,
    StateMixin,
)
from pepys_import.core.store.db_base import BaseSpatiaLite
from pepys_import.core.store.db_status import TableTypes


# Metadata Tables
class HostedBy(BaseSpatiaLite):
    __tablename__ = constants.HOSTED_BY
    table_type = TableTypes.METADATA
    table_type_id = 1

    hosted_by_id = Column(Integer, primary_key=True)
    subject_id = Column(Integer, ForeignKey("Platforms.platform_id"), nullable=False)
    host_id = Column(Integer, ForeignKey("Platforms.platform_id"), nullable=False)
    hosted_from = Column(DATE, nullable=False)
    host_to = Column(DATE, nullable=False)
    privacy_id = Column(Integer, ForeignKey("Privacies.privacy_id"), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Sensor(BaseSpatiaLite, SensorMixin):
    __tablename__ = constants.SENSOR
    table_type = TableTypes.METADATA
    table_type_id = 2

    sensor_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    sensor_type_id = Column(Integer, ForeignKey("SensorTypes.sensor_type_id"), nullable=False)
    host = Column(Integer, ForeignKey("Platforms.platform_id"), nullable=False)
    privacy_id = Column(Integer, ForeignKey("Privacies.privacy_id"), nullable=False)
    created_date = deferred(Column(DateTime, default=datetime.utcnow))

    sensor_type = relationship(
        "SensorType", lazy="joined", join_depth=1, innerjoin=True, uselist=False
    )
    sensor_type_name = association_proxy("sensor_type", "name")

    host_ = relationship("Platform", lazy="joined", join_depth=1, innerjoin=True, uselist=False)
    host__name = association_proxy("host_", "name")

    privacy = relationship("Privacy", lazy="joined", join_depth=1, innerjoin=True, uselist=False)
    privacy_name = association_proxy("privacy", "name")


class Platform(BaseSpatiaLite, PlatformMixin):
    __tablename__ = constants.PLATFORM
    table_type = TableTypes.METADATA
    table_type_id = 3

    platform_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    pennant = deferred(Column(String(10)))
    trigraph = deferred(Column(String(3)))
    quadgraph = deferred(Column(String(4)))
    nationality_id = Column(Integer, ForeignKey("Nationalities.nationality_id"), nullable=False)
    platform_type_id = Column(Integer, ForeignKey("PlatformTypes.platform_type_id"), nullable=False)
    privacy_id = Column(Integer, ForeignKey("Privacies.privacy_id"), nullable=False)
    created_date = deferred(Column(DateTime, default=datetime.utcnow))

    platform_type = relationship(
        "PlatformType", lazy="joined", join_depth=1, innerjoin=True, uselist=False
    )
    platform_type_name = association_proxy("platform_type", "name")

    nationality = relationship(
        "Nationality", lazy="joined", join_depth=1, innerjoin=True, uselist=False
    )
    nationality_name = association_proxy("nationality", "name")

    privacy = relationship("Privacy", lazy="joined", join_depth=1, innerjoin=True, uselist=False)
    privacy_name = association_proxy("privacy", "name")


class Task(BaseSpatiaLite):
    __tablename__ = constants.TASK
    table_type = TableTypes.METADATA
    table_type_id = 4

    task_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    parent_id = Column(Integer, ForeignKey("Tasks.task_id"), nullable=False)
    start = Column(TIMESTAMP, nullable=False)
    end = Column(TIMESTAMP, nullable=False)
    environment = Column(String(150))
    location = Column(String(150))
    privacy_id = Column(Integer, ForeignKey("Privacies.privacy_id"), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Participant(BaseSpatiaLite):
    __tablename__ = constants.PARTICIPANT
    table_type = TableTypes.METADATA
    table_type_id = 5

    participant_id = Column(Integer, primary_key=True)
    platform_id = Column(Integer, ForeignKey("Platforms.platform_id"), nullable=False)
    task_id = Column(Integer, ForeignKey("Tasks.task_id"), nullable=False)
    start = Column(TIMESTAMP)
    end = Column(TIMESTAMP)
    force = Column(String(150))
    privacy_id = Column(Integer, ForeignKey("Privacies.privacy_id"), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Datafile(BaseSpatiaLite, DatafileMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.measurements = dict()

    __tablename__ = constants.DATAFILE
    table_type = TableTypes.METADATA
    table_type_id = 6

    datafile_id = Column(Integer, primary_key=True)
    simulated = deferred(Column(Boolean, nullable=False))
    privacy_id = Column(Integer, ForeignKey("Privacies.privacy_id"), nullable=False)
    datafile_type_id = Column(Integer, ForeignKey("DatafileTypes.datafile_type_id"), nullable=False)
    reference = Column(String(150))
    url = Column(String(150))
    size = Column(Integer, nullable=False)
    hash = deferred(Column(String(32), nullable=False))
    created_date = deferred(Column(DateTime, default=datetime.utcnow))

    privacy = relationship("Privacy", lazy="joined", join_depth=1, innerjoin=True, uselist=False)
    privacy_name = association_proxy("privacy", "name")

    datafile_type = relationship(
        "DatafileType", lazy="joined", join_depth=1, innerjoin=True, uselist=False
    )
    datafile_type_name = association_proxy("datafile_type", "name")


class Synonym(BaseSpatiaLite):
    __tablename__ = constants.SYNONYM
    table_type = TableTypes.METADATA
    table_type_id = 7

    synonym_id = Column(Integer, primary_key=True)
    table = Column(String(150), nullable=False)
    entity = Column(Integer, nullable=False)
    synonym = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Change(BaseSpatiaLite):
    __tablename__ = constants.CHANGE
    table_type = TableTypes.METADATA
    table_type_id = 8

    change_id = Column(Integer, primary_key=True)
    user = Column(String(150), nullable=False)
    modified = Column(DATE, nullable=False)
    reason = Column(String(500), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Log(BaseSpatiaLite):
    __tablename__ = constants.LOG
    table_type = TableTypes.METADATA
    table_type_id = 9

    log_id = Column(Integer, primary_key=True)
    table = Column(String(150), nullable=False)
    id = Column(Integer, nullable=False)
    field = Column(String(150))
    new_value = Column(String(150))
    change_id = Column(Integer, ForeignKey("Changes.change_id"), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)

    change = relationship("Change", lazy="joined", join_depth=1, innerjoin=True, uselist=False)
    change_reason = association_proxy("change", "reason")


class Extraction(BaseSpatiaLite):
    __tablename__ = constants.EXTRACTION
    table_type = TableTypes.METADATA
    table_type_id = 10

    extraction_id = Column(Integer, primary_key=True)
    table = Column(String(150), nullable=False)
    field = Column(String(150), nullable=False)
    chars = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Tag(BaseSpatiaLite):
    __tablename__ = constants.TAG
    table_type = TableTypes.METADATA
    table_type_id = 11

    tag_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class TaggedItem(BaseSpatiaLite):
    __tablename__ = constants.TAGGED_ITEM
    table_type = TableTypes.METADATA
    table_type_id = 12

    tagged_item_id = Column(Integer, primary_key=True)
    tag_id = Column(Integer, ForeignKey("Tags.tag_id"), nullable=False)
    item_id = Column(Integer, nullable=False)
    tagged_by_id = Column(Integer, ForeignKey("Users.user_id"), nullable=False)
    private = Column(Boolean, nullable=False)
    tagged_on = Column(DATE, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


# Reference Tables
class PlatformType(BaseSpatiaLite):
    __tablename__ = constants.PLATFORM_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 13

    platform_type_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Nationality(BaseSpatiaLite):
    __tablename__ = constants.NATIONALITY
    table_type = TableTypes.REFERENCE
    table_type_id = 14

    nationality_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class GeometryType(BaseSpatiaLite):
    __tablename__ = constants.GEOMETRY_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 15

    geo_type_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class GeometrySubType(BaseSpatiaLite):
    __tablename__ = constants.GEOMETRY_SUBTYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 16

    geo_sub_type_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    parent = Column(Integer, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class User(BaseSpatiaLite):
    __tablename__ = constants.USER
    table_type = TableTypes.REFERENCE
    table_type_id = 17

    user_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class UnitType(BaseSpatiaLite):
    __tablename__ = constants.UNIT_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 18

    unit_type_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class ClassificationType(BaseSpatiaLite):
    __tablename__ = constants.CLASSIFICATION_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 19

    class_type_id = Column(Integer, primary_key=True)
    class_type = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class ContactType(BaseSpatiaLite):
    __tablename__ = constants.CONTACT_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 20

    contact_type_id = Column(Integer, primary_key=True)
    contact_type = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class SensorType(BaseSpatiaLite):
    __tablename__ = constants.SENSOR_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 21

    sensor_type_id = Column(Integer, primary_key=True)
    name = Column(String(150))
    created_date = Column(DateTime, default=datetime.utcnow)


class Privacy(BaseSpatiaLite):
    __tablename__ = constants.PRIVACY
    table_type = TableTypes.REFERENCE
    table_type_id = 22

    privacy_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class DatafileType(BaseSpatiaLite):
    __tablename__ = constants.DATAFILE_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 23

    datafile_type_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class MediaType(BaseSpatiaLite):
    __tablename__ = constants.MEDIA_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 24

    media_type_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class CommentType(BaseSpatiaLite):
    __tablename__ = constants.COMMENT_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 25

    comment_type_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class CommodityType(BaseSpatiaLite):
    __tablename__ = constants.COMMODITY_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 26

    commodity_type_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class ConfidenceLevel(BaseSpatiaLite):
    __tablename__ = constants.CONFIDENCE_LEVEL
    table_type = TableTypes.REFERENCE
    table_type_id = 27

    confidence_level_id = Column(Integer, primary_key=True)
    level = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


# Measurements Tables
class State(BaseSpatiaLite, StateMixin, ElevationPropertyMixin, LocationPropertyMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sensor_name = None
        self.platform_name = None

    __tablename__ = constants.STATE
    table_type = TableTypes.MEASUREMENT
    table_type_id = 28

    state_id = Column(Integer, primary_key=True)
    time = Column(TIMESTAMP, nullable=False)
    sensor_id = Column(Integer, ForeignKey("Sensors.sensor_id"), nullable=False)
    _location = Column("location", Geometry(geometry_type="POINT", srid=4326, management=True))
    _elevation = Column("elevation", REAL)
    _heading = Column("heading", REAL)
    _course = Column("course", REAL)
    _speed = Column("speed", REAL)
    source_id = Column(Integer, ForeignKey("Datafiles.datafile_id"), nullable=False)
    privacy_id = Column(Integer, ForeignKey("Privacies.privacy_id"))
    created_date = deferred(Column(DateTime, default=datetime.utcnow))

    sensor = relationship("Sensor", lazy="joined", join_depth=1, uselist=False)
    sensor_name = association_proxy("sensor", "name")

    source = relationship("Datafile", lazy="joined", join_depth=1, uselist=False)
    source_reference = association_proxy("source", "reference")

    privacy = relationship("Privacy", lazy="joined", join_depth=1, uselist=False)
    privacy_name = association_proxy("privacy", "name")


class Contact(BaseSpatiaLite, ContactMixin, LocationPropertyMixin, ElevationPropertyMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sensor_name = None
        self.platform_name = None

    __tablename__ = constants.CONTACT
    table_type = TableTypes.MEASUREMENT
    table_type_id = 29

    contact_id = Column(Integer, primary_key=True)
    name = Column(String(150))
    sensor_id = Column(Integer, ForeignKey("Sensors.sensor_id"), nullable=False)
    time = Column(TIMESTAMP, nullable=False)
    _bearing = Column("bearing", REAL)
    _rel_bearing = Column("rel_bearing", REAL)
    _ambig_bearing = Column("ambig_bearing", REAL)
    _freq = Column("freq", REAL)
    _range = Column("range", REAL)
    _location = Column("location", Geometry(geometry_type="POINT", srid=4326, management=True))
    _elevation = Column("elevation", REAL)
    _major = Column("major", REAL)
    _minor = Column("minor", REAL)
    _orientation = Column("orientation", REAL)
    classification = Column(String(150))
    confidence = Column(String(150))
    contact_type = Column(String(150))
    _mla = Column("mla", REAL)
    _soa = Column("soa", REAL)
    subject_id = Column(Integer, ForeignKey("Platforms.platform_id"))
    source_id = Column(Integer, ForeignKey("Datafiles.datafile_id"), nullable=False)
    privacy_id = Column(Integer, ForeignKey("Privacies.privacy_id"))
    created_date = deferred(Column(DateTime, default=datetime.utcnow))

    subject = relationship("Platform", lazy="joined", join_depth=1, uselist=False)
    subject_name = association_proxy("subject", "name")

    datafile = relationship("Datafile", lazy="joined", join_depth=1, uselist=False)
    datafile_reference = association_proxy("datafile", "reference")

    privacy = relationship("Privacy", lazy="joined", join_depth=1, uselist=False)
    privacy_name = association_proxy("privacy", "name")


class Activation(BaseSpatiaLite, ActivationMixin):
    __tablename__ = constants.ACTIVATION
    table_type = TableTypes.MEASUREMENT
    table_type_id = 30

    activation_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    sensor_id = Column(Integer, ForeignKey("Sensors.sensor_id"), nullable=False)
    start = Column(TIMESTAMP, nullable=False)
    end = Column(TIMESTAMP, nullable=False)
    _min_range = Column("min_range", REAL)
    _max_range = Column("max_range", REAL)
    _left_arc = Column("left_arc", REAL)
    _right_arc = Column("right_arc", REAL)
    source_id = Column(Integer, ForeignKey("Datafiles.datafile_id"), nullable=False)
    privacy_id = Column(Integer, ForeignKey("Privacies.privacy_id"))
    created_date = Column(DateTime, default=datetime.utcnow)


class LogsHolding(BaseSpatiaLite):
    __tablename__ = constants.LOGS_HOLDING
    table_type = TableTypes.MEASUREMENT
    table_type_id = 31

    logs_holding_id = Column(Integer, primary_key=True)
    time = Column(TIMESTAMP, nullable=False)
    commodity_id = Column(Integer, nullable=False)
    quantity = Column(REAL, nullable=False)
    unit_type_id = Column(Integer, ForeignKey("UnitTypes.unit_type_id"), nullable=False)
    platform_id = Column(Integer, ForeignKey("Platforms.platform_id"), nullable=False)
    comment = Column(String(150), nullable=False)
    source_id = Column(Integer, ForeignKey("Datafiles.datafile_id"), nullable=False)
    privacy_id = Column(Integer, ForeignKey("Privacies.privacy_id"))
    created_date = Column(DateTime, default=datetime.utcnow)


class Comment(BaseSpatiaLite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sensor_name = None
        self.platform_name = None

    __tablename__ = constants.COMMENT
    table_type = TableTypes.MEASUREMENT
    table_type_id = 32

    comment_id = Column(Integer, primary_key=True)
    platform_id = Column(Integer, ForeignKey("Platforms.platform_id"))
    time = Column(TIMESTAMP, nullable=False)
    comment_type_id = Column(Integer, ForeignKey("CommentTypes.comment_type_id"), nullable=False)
    content = Column(String(150), nullable=False)
    source_id = Column(Integer, ForeignKey("Datafiles.datafile_id"), nullable=False)
    privacy_id = Column(Integer, ForeignKey("Privacies.privacy_id"))
    created_date = deferred(Column(DateTime, default=datetime.utcnow))

    platform = relationship("Platform", lazy="joined", join_depth=1, innerjoin=True, uselist=False)
    platform_name = association_proxy("platform", "name")

    comment_type = relationship(
        "CommentType", lazy="joined", join_depth=1, innerjoin=True, uselist=False
    )
    comment_type_name = association_proxy("comment_type", "name")

    source = relationship("Datafile", lazy="joined", join_depth=1, uselist=False)
    source_reference = association_proxy("source", "reference")

    privacy = relationship("Privacy", lazy="joined", join_depth=1, uselist=False)
    privacy_name = association_proxy("privacy", "name")


class Geometry1(BaseSpatiaLite):
    __tablename__ = constants.GEOMETRY
    table_type = TableTypes.MEASUREMENT
    table_type_id = 33

    geometry_id = Column(Integer, primary_key=True)
    geometry = Column(Geometry(geometry_type="GEOMETRY", management=True), nullable=False)
    name = Column(String(150), nullable=False)
    geo_type_id = Column(Integer, ForeignKey("GeometryTypes.geo_type_id"), nullable=False)
    geo_sub_type_id = Column(
        Integer, ForeignKey("GeometrySubTypes.geo_sub_type_id"), nullable=False
    )
    start = Column(TIMESTAMP)
    end = Column(TIMESTAMP)
    task_id = Column(Integer)
    subject_platform_id = Column(Integer, ForeignKey("Platforms.platform_id"))
    sensor_platform_id = Column(Integer, ForeignKey("Platforms.platform_id"))
    source_id = Column(Integer, ForeignKey("Datafiles.datafile_id"), nullable=False)
    privacy_id = Column(Integer, ForeignKey("Privacies.privacy_id"))
    created_date = Column(DateTime, default=datetime.utcnow)


class Media(BaseSpatiaLite, MediaMixin, ElevationPropertyMixin, LocationPropertyMixin):
    __tablename__ = constants.MEDIA
    table_type = TableTypes.MEASUREMENT
    table_type_id = 34

    media_id = Column(Integer, primary_key=True)
    platform_id = Column(Integer, ForeignKey("Platforms.platform_id"))
    subject_id = Column(Integer, ForeignKey("Platforms.platform_id"))
    sensor_id = Column(Integer, ForeignKey("Sensors.sensor_id"))
    _location = Column("location", Geometry(geometry_type="POINT", srid=4326, management=True))
    _elevation = Column("elevation", REAL)
    time = Column(TIMESTAMP)
    media_type_id = Column(Integer, nullable=False)
    url = Column(String(150), nullable=False)
    source_id = Column(Integer, ForeignKey("Datafiles.datafile_id"), nullable=False)
    privacy_id = Column(Integer, ForeignKey("Privacies.privacy_id"))
    created_date = Column(DateTime, default=datetime.utcnow)
