from datetime import datetime
from uuid import uuid4

from geoalchemy2 import Geometry
from sqlalchemy import DATE, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.sqlite import REAL, TIMESTAMP
from sqlalchemy.orm import (  # used to defer fetching attributes unless it's specifically called
    declared_attr,
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
    GeometrySubTypeMixin,
    HostedByMixin,
    LocationPropertyMixin,
    LogMixin,
    LogsHoldingMixin,
    MediaMixin,
    NationalityMixin,
    PlatformMixin,
    ReferenceDefaultFields,
    ReferenceRepr,
    SensorMixin,
    SerialMixin,
    SerialParticipantMixin,
    SeriesMixin,
    StateMixin,
    SynonymMixin,
    TaggedItemMixin,
    WargameMixin,
    WargameParticipantMixin,
)
from pepys_import.core.store.db_base import BaseSpatiaLite
from pepys_import.core.store.db_status import TableTypes
from pepys_import.utils.sqlalchemy_utils import UUIDType


# Metadata Tables
class ConfigOption(BaseSpatiaLite):
    __tablename__ = constants.CONFIG_OPTIONS
    table_type = TableTypes.METADATA
    table_type_id = 37
    _default_preview_fields = ["name", "value"]

    config_option_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_ConfigOption_name"),
        nullable=False,
        unique=True,
    )
    description = Column(Text())
    value = Column(Text(), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class HostedBy(BaseSpatiaLite, HostedByMixin):
    __tablename__ = constants.HOSTED_BY
    table_type = TableTypes.METADATA
    table_type_id = 1

    hosted_by_id = Column(UUIDType, primary_key=True, default=uuid4)
    subject_id = Column(
        UUIDType,
        ForeignKey("Platforms.platform_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    host_id = Column(
        UUIDType,
        ForeignKey("Platforms.platform_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    hosted_from = Column(DATE, nullable=False)
    host_to = Column(DATE, nullable=False)
    privacy_id = Column(
        UUIDType,
        ForeignKey("Privacies.privacy_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
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
        UUIDType,
        ForeignKey("SensorTypes.sensor_type_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    host = Column(
        UUIDType,
        ForeignKey("Platforms.platform_id", onupdate="cascade", ondelete="CASCADE"),
        nullable=False,
    )
    privacy_id = Column(
        UUIDType,
        ForeignKey("Privacies.privacy_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
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
    identifier = Column(
        String(30),
        CheckConstraint("identifier <> ''", name="ck_Platforms_identifier"),
        nullable=False,
    )
    trigraph = deferred(Column(String(3)))
    quadgraph = deferred(Column(String(4)))
    nationality_id = Column(
        UUIDType,
        ForeignKey("Nationalities.nationality_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    platform_type_id = Column(
        UUIDType,
        ForeignKey("PlatformTypes.platform_type_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    privacy_id = Column(
        UUIDType,
        ForeignKey("Privacies.privacy_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    created_date = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "name", "nationality_id", "identifier", name="uq_Platform_name_nat_identifier"
        ),
    )


class Series(BaseSpatiaLite, SeriesMixin):
    __tablename__ = constants.SERIES
    table_type = TableTypes.METADATA
    table_type_id = 36

    series_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), CheckConstraint("name <> ''", name="ck_Series_name"), nullable=False)
    privacy_id = Column(
        UUIDType,
        ForeignKey("Privacies.privacy_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class Wargame(BaseSpatiaLite, WargameMixin):
    __tablename__ = constants.WARGAME
    table_type = TableTypes.METADATA
    table_type_id = 37

    wargame_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(
        String(150), CheckConstraint("name <> ''", name="ck_Wargames_name"), nullable=False
    )
    series_id = Column(
        UUIDType,
        ForeignKey("Series.series_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    start = Column(TIMESTAMP, nullable=False)
    end = Column(TIMESTAMP, nullable=False)
    privacy_id = Column(
        UUIDType,
        ForeignKey("Privacies.privacy_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class Serial(BaseSpatiaLite, SerialMixin):
    __tablename__ = constants.SERIAL
    table_type = TableTypes.METADATA
    table_type_id = 37

    __table_args__ = (
        UniqueConstraint("serial_number", "wargame_id", name="uq_Serial_serial_number_wargame_id"),
    )

    serial_id = Column(UUIDType, primary_key=True, default=uuid4)
    wargame_id = Column(
        UUIDType,
        ForeignKey("Wargames.wargame_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    serial_number = Column(
        String(150),
        CheckConstraint("serial_number <> ''", name="ck_Serials_serial_number"),
        nullable=False,
    )
    start = Column(TIMESTAMP, nullable=False)
    end = Column(TIMESTAMP, nullable=False)
    exercise = Column(String(150))
    environment = Column(String(150))
    location = Column(String(150))
    include_in_timeline = Column(Boolean, default=True)
    privacy_id = Column(
        UUIDType,
        ForeignKey("Privacies.privacy_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class WargameParticipant(BaseSpatiaLite, WargameParticipantMixin):
    __tablename__ = constants.WARGAME_PARTICIPANT
    table_type = TableTypes.METADATA
    table_type_id = 38

    wargame_participant_id = Column(UUIDType, primary_key=True, default=uuid4)
    wargame_id = Column(
        UUIDType,
        ForeignKey("Wargames.wargame_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    platform_id = Column(
        UUIDType,
        ForeignKey("Platforms.platform_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    privacy_id = Column(
        UUIDType,
        ForeignKey("Privacies.privacy_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class SerialParticipant(BaseSpatiaLite, SerialParticipantMixin):
    __tablename__ = constants.SERIAL_PARTICIPANT
    table_type = TableTypes.METADATA
    table_type_id = 39

    serial_participant_id = Column(UUIDType, primary_key=True, default=uuid4)
    wargame_participant_id = Column(
        UUIDType,
        ForeignKey(
            "WargameParticipants.wargame_participant_id", onupdate="cascade", ondelete="cascade"
        ),
        nullable=False,
    )
    serial_id = Column(
        UUIDType,
        ForeignKey("Serials.serial_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    start = Column(TIMESTAMP)
    end = Column(TIMESTAMP)
    force_type_id = Column(
        UUIDType,
        ForeignKey("ForceTypes.force_type_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    privacy_id = Column(
        UUIDType,
        ForeignKey("Privacies.privacy_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class Datafile(BaseSpatiaLite, DatafileMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.measurements = dict()
        self.highlighted_file = None
        self.pending_extracted_tokens = []
        self.measurement_object_to_tokens_list = {}
        self.current_measurement_object = None

    __tablename__ = constants.DATAFILE
    table_type = TableTypes.METADATA
    table_type_id = 6

    datafile_id = Column(UUIDType, primary_key=True, default=uuid4)
    simulated = deferred(Column(Boolean, nullable=False))
    privacy_id = Column(
        UUIDType,
        ForeignKey("Privacies.privacy_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    datafile_type_id = Column(
        UUIDType,
        ForeignKey("DatafileTypes.datafile_type_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
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
    datafile_id = Column(
        UUIDType, ForeignKey("Datafiles.datafile_id", onupdate="cascade", ondelete="SET NULL")
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
    previous_value = Column(Text())
    change_id = Column(
        UUIDType,
        ForeignKey("Changes.change_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class Extraction(BaseSpatiaLite):
    __tablename__ = constants.EXTRACTION
    table_type = TableTypes.METADATA
    table_type_id = 10

    extraction_id = Column(UUIDType, primary_key=True, default=uuid4)
    destination_table = Column(String(150))
    entry_id = Column(UUIDType)
    field = Column(String(150), nullable=False)
    datafile_id = Column(
        UUIDType,
        ForeignKey("Datafiles.datafile_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    text = Column(Text(), nullable=False)
    text_location = Column(String(200), nullable=False)
    importer = Column(String(150), nullable=False)
    interpreted_value = Column(Text(), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Tag(BaseSpatiaLite, ReferenceDefaultFields):
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
    tag_id = Column(
        UUIDType, ForeignKey("Tags.tag_id", onupdate="cascade", ondelete="cascade"), nullable=False
    )
    item_id = Column(UUIDType, nullable=False)
    tagged_by_id = Column(
        UUIDType,
        ForeignKey("Users.user_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    private = Column(Boolean, nullable=False)
    tagged_on = Column(DATE, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


# Reference Tables
class ForceType(BaseSpatiaLite, ReferenceRepr, ReferenceDefaultFields):
    __tablename__ = constants.FORCE_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 40

    force_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_ForceTypes_name"),
        nullable=False,
        unique=True,
    )
    color = Column(String(10))
    created_date = Column(DateTime, default=datetime.utcnow)


class PlatformType(BaseSpatiaLite, ReferenceRepr, ReferenceDefaultFields):
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
    default_data_interval_secs = Column(Integer)
    created_date = Column(DateTime, default=datetime.utcnow)


class Nationality(BaseSpatiaLite, ReferenceRepr, NationalityMixin):
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


class GeometryType(BaseSpatiaLite, ReferenceRepr, ReferenceDefaultFields):
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


class GeometrySubType(BaseSpatiaLite, GeometrySubTypeMixin):
    __tablename__ = constants.GEOMETRY_SUBTYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 16

    geo_sub_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(
        String(150), CheckConstraint("name <> ''", name="ck_GeometrySubTypes_name"), nullable=False
    )
    parent = Column(
        UUIDType,
        ForeignKey("GeometryTypes.geo_type_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    created_date = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("name", "parent", name="uq_GeometrySubTypes_name_parent"),)


class User(BaseSpatiaLite, ReferenceRepr, ReferenceDefaultFields):
    __tablename__ = constants.USER
    table_type = TableTypes.REFERENCE
    table_type_id = 17
    _default_preview_fields = ["name"]

    user_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_Users_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class UnitType(BaseSpatiaLite, ReferenceRepr, ReferenceDefaultFields):
    __tablename__ = constants.UNIT_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 18
    _default_preview_fields = ["name"]

    unit_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_UnitTypes_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class ClassificationType(BaseSpatiaLite, ReferenceRepr, ReferenceDefaultFields):
    __tablename__ = constants.CLASSIFICATION_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 19
    _default_preview_fields = ["name"]

    class_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_ClassificationTypes_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class ContactType(BaseSpatiaLite, ReferenceRepr, ReferenceDefaultFields):
    __tablename__ = constants.CONTACT_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 20
    _default_preview_fields = ["name"]

    contact_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_ContactTypes_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class SensorType(BaseSpatiaLite, ReferenceRepr, ReferenceDefaultFields):
    __tablename__ = constants.SENSOR_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 21
    _default_preview_fields = ["name"]

    sensor_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_SensorTypes_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class Privacy(BaseSpatiaLite, ReferenceRepr, ReferenceDefaultFields):
    __tablename__ = constants.PRIVACY
    table_type = TableTypes.REFERENCE
    table_type_id = 22
    _default_preview_fields = ["name"]

    privacy_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_Privacies_name"),
        nullable=False,
        unique=True,
    )
    level = Column(Integer, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class DatafileType(BaseSpatiaLite, ReferenceRepr, ReferenceDefaultFields):
    __tablename__ = constants.DATAFILE_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 23
    _default_preview_fields = ["name"]

    datafile_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_DatafileTypes_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class MediaType(BaseSpatiaLite, ReferenceRepr, ReferenceDefaultFields):
    __tablename__ = constants.MEDIA_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 24
    _default_preview_fields = ["name"]

    media_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_MediaTypes_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class CommentType(BaseSpatiaLite, ReferenceRepr, ReferenceDefaultFields):
    __tablename__ = constants.COMMENT_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 25
    _default_preview_fields = ["name"]

    comment_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_CommentTypes_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class CommodityType(BaseSpatiaLite, ReferenceRepr, ReferenceDefaultFields):
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


class ConfidenceLevel(BaseSpatiaLite, ReferenceRepr, ReferenceDefaultFields):
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
        UUIDType,
        ForeignKey("Sensors.sensor_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    _location = deferred(
        Column("location", Geometry(geometry_type="POINT", srid=4326, management=True))
    )
    _elevation = deferred(Column("elevation", REAL))
    _heading = deferred(Column("heading", REAL))
    _course = deferred(Column("course", REAL))
    _speed = deferred(Column("speed", REAL))
    source_id = Column(
        UUIDType,
        ForeignKey("Datafiles.datafile_id", onupdate="cascade", ondelete="CASCADE"),
        nullable=False,
    )
    privacy_id = Column(
        UUIDType, ForeignKey("Privacies.privacy_id", onupdate="cascade", ondelete="cascade")
    )
    remarks = Column(Text)
    created_date = Column(DateTime, default=datetime.utcnow)

    # This relationship has to be defined here rather than in
    # common_db.py, as we're using the 'secondary' parameter,
    # which has to take a table name. With Postgres it requires a
    # full 'schema.table' name, and as SQLite doesn't have
    # schemas, this will fail for SQLite. Thus it is defined
    # in sqlite_db.py and postgres_db.py.
    @declared_attr
    def platform(self):
        return relationship(
            "Platform",
            secondary="Sensors",
            primaryjoin="State.sensor_id == Sensor.sensor_id",
            secondaryjoin="Platform.platform_id == Sensor.host",
            lazy="joined",
            uselist=False,
            viewonly=True,
            # This specifies that when trying to query on this relationship
            # this is the local column (well, assoc proxy actually) to filter on
            info={"local_column": "platform_id"},
        )


class Contact(BaseSpatiaLite, ContactMixin, LocationPropertyMixin, ElevationPropertyMixin):
    __tablename__ = constants.CONTACT
    table_type = TableTypes.MEASUREMENT
    table_type_id = 29

    contact_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150))
    sensor_id = Column(
        UUIDType,
        ForeignKey("Sensors.sensor_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
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
    subject_id = Column(
        UUIDType, ForeignKey("Platforms.platform_id", onupdate="cascade", ondelete="cascade")
    )
    source_id = Column(
        UUIDType,
        ForeignKey("Datafiles.datafile_id", onupdate="cascade", ondelete="CASCADE"),
        nullable=False,
    )
    privacy_id = Column(
        UUIDType, ForeignKey("Privacies.privacy_id", onupdate="cascade", ondelete="cascade")
    )
    remarks = Column(Text)
    created_date = deferred(Column(DateTime, default=datetime.utcnow))

    # This relationship has to be defined here rather than in
    # common_db.py, as we're using the 'secondary' parameter,
    # which has to take a table name. With Postgres it requires a
    # full 'schema.table' name, and as SQLite doesn't have
    # schemas, this will fail for SQLite. Thus it is defined
    # in sqlite_db.py and postgres_db.py.
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
            # This specifies that when trying to query on this relationship
            # this is the local column (well, assoc proxy actually) to filter on
            info={"local_column": "platform_id"},
        )


class Activation(BaseSpatiaLite, ActivationMixin):
    __tablename__ = constants.ACTIVATION
    table_type = TableTypes.MEASUREMENT
    table_type_id = 30

    activation_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150))
    sensor_id = Column(
        UUIDType,
        ForeignKey("Sensors.sensor_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    start = deferred(Column(TIMESTAMP))
    end = deferred(Column(TIMESTAMP))
    _min_range = deferred(Column("min_range", REAL))
    _max_range = deferred(Column("max_range", REAL))
    _left_arc = deferred(Column("left_arc", REAL))
    _right_arc = deferred(Column("right_arc", REAL))
    source_id = Column(
        UUIDType,
        ForeignKey("Datafiles.datafile_id", onupdate="cascade", ondelete="CASCADE"),
        nullable=False,
    )
    privacy_id = Column(
        UUIDType, ForeignKey("Privacies.privacy_id", onupdate="cascade", ondelete="cascade")
    )
    remarks = Column(Text)
    created_date = Column(DateTime, default=datetime.utcnow)


class LogsHolding(BaseSpatiaLite, LogsHoldingMixin):
    __tablename__ = constants.LOGS_HOLDING
    table_type = TableTypes.MEASUREMENT
    table_type_id = 31

    logs_holding_id = Column(UUIDType, primary_key=True, default=uuid4)
    time = Column(TIMESTAMP, nullable=False)
    commodity_id = Column(
        UUIDType,
        ForeignKey("CommodityTypes.commodity_type_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    quantity = Column(REAL, nullable=False)
    unit_type_id = Column(
        UUIDType,
        ForeignKey("UnitTypes.unit_type_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    platform_id = Column(
        UUIDType,
        ForeignKey("Platforms.platform_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    comment = Column(Text(), nullable=False)
    source_id = Column(
        UUIDType,
        ForeignKey("Datafiles.datafile_id", onupdate="cascade", ondelete="CASCADE"),
        nullable=False,
    )
    privacy_id = Column(
        UUIDType, ForeignKey("Privacies.privacy_id", onupdate="cascade", ondelete="cascade")
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
    platform_id = Column(
        UUIDType, ForeignKey("Platforms.platform_id", onupdate="cascade", ondelete="cascade")
    )
    time = Column(TIMESTAMP, nullable=False)
    comment_type_id = Column(
        UUIDType,
        ForeignKey("CommentTypes.comment_type_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    content = Column(
        Text, CheckConstraint("content <> ''", name="ck_Comments_content"), nullable=False
    )
    source_id = Column(
        UUIDType,
        ForeignKey("Datafiles.datafile_id", onupdate="cascade", ondelete="CASCADE"),
        nullable=False,
    )
    privacy_id = Column(
        UUIDType, ForeignKey("Privacies.privacy_id", onupdate="cascade", ondelete="cascade")
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class Geometry1(BaseSpatiaLite, GeometryMixin):
    __tablename__ = constants.GEOMETRY
    table_type = TableTypes.MEASUREMENT
    table_type_id = 33

    geometry_id = Column(UUIDType, primary_key=True, default=uuid4)
    _geometry = Column(
        "geometry",
        Geometry(geometry_type="GEOMETRY", srid=4326, management=True),
        nullable=False,
    )
    name = Column(String(150))
    geo_type_id = Column(
        UUIDType,
        ForeignKey("GeometryTypes.geo_type_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    geo_sub_type_id = Column(
        UUIDType,
        ForeignKey("GeometrySubTypes.geo_sub_type_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    start = Column(TIMESTAMP)
    end = Column(TIMESTAMP)
    serial_id = Column(
        UUIDType, ForeignKey("Serials.serial_id", onupdate="cascade", ondelete="cascade")
    )
    subject_platform_id = Column(
        UUIDType, ForeignKey("Platforms.platform_id", onupdate="cascade", ondelete="cascade")
    )
    sensor_platform_id = Column(
        UUIDType, ForeignKey("Platforms.platform_id", onupdate="cascade", ondelete="cascade")
    )
    source_id = Column(
        UUIDType,
        ForeignKey("Datafiles.datafile_id", onupdate="cascade", ondelete="CASCADE"),
        nullable=False,
    )
    privacy_id = Column(
        UUIDType, ForeignKey("Privacies.privacy_id", onupdate="cascade", ondelete="cascade")
    )
    remarks = Column(Text)
    created_date = Column(DateTime, default=datetime.utcnow)


class Media(BaseSpatiaLite, MediaMixin, ElevationPropertyMixin, LocationPropertyMixin):
    __tablename__ = constants.MEDIA
    table_type = TableTypes.MEASUREMENT
    table_type_id = 34

    media_id = Column(UUIDType, primary_key=True, default=uuid4)
    platform_id = Column(
        UUIDType, ForeignKey("Platforms.platform_id", onupdate="cascade", ondelete="cascade")
    )
    subject_id = Column(
        UUIDType, ForeignKey("Platforms.platform_id", onupdate="cascade", ondelete="cascade")
    )
    sensor_id = Column(
        UUIDType, ForeignKey("Sensors.sensor_id", onupdate="cascade", ondelete="cascade")
    )
    _location = deferred(
        Column("location", Geometry(geometry_type="POINT", srid=4326, management=True))
    )
    _elevation = deferred(Column("elevation", REAL))
    time = Column(TIMESTAMP)
    media_type_id = Column(
        UUIDType,
        ForeignKey("MediaTypes.media_type_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    url = deferred(
        Column(String(150), CheckConstraint("url <> ''", name="ck_Media_url"), nullable=False)
    )
    source_id = Column(
        UUIDType,
        ForeignKey("Datafiles.datafile_id", onupdate="cascade", ondelete="CASCADE"),
        nullable=False,
    )
    privacy_id = Column(
        UUIDType, ForeignKey("Privacies.privacy_id", onupdate="cascade", ondelete="cascade")
    )
    remarks = Column(Text)
    created_date = Column(DateTime, default=datetime.utcnow)


class HelpText(BaseSpatiaLite):
    __tablename__ = constants.HELP_TEXT
    table_type = TableTypes.REFERENCE
    table_type_id = 35

    help_text_id = Column(UUIDType, primary_key=True, default=uuid4)
    id = Column(String(50), nullable=False)
    guidance = Column(String(2000), nullable=False)
