from datetime import datetime
from uuid import uuid4

from geoalchemy2 import Geometry
from sqlalchemy import DATE, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, TIMESTAMP, UUID
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
    ExtractionMixin,
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
from pepys_import.core.store.db_base import BasePostGIS
from pepys_import.core.store.db_status import TableTypes


# Metadata Tables
class ConfigOption(BasePostGIS):
    __tablename__ = constants.CONFIG_OPTIONS
    table_type = TableTypes.METADATA
    table_type_id = 37
    _default_preview_fields = ["name", "value"]

    config_option_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_ConfigOption_name"),
        nullable=False,
        unique=True,
    )
    description = Column(Text())
    value = Column(Text(), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class HostedBy(BasePostGIS, HostedByMixin):
    __tablename__ = constants.HOSTED_BY
    table_type = TableTypes.METADATA
    table_type_id = 1

    hosted_by_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    subject_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Platforms.platform_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    host_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Platforms.platform_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    hosted_from = Column(DATE, nullable=False)
    host_to = Column(DATE, nullable=False)
    privacy_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Privacies.privacy_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class Sensor(BasePostGIS, SensorMixin):
    __tablename__ = constants.SENSOR
    table_type = TableTypes.METADATA
    table_type_id = 2
    __table_args__ = (UniqueConstraint("name", "host", name="uq_sensors_name_host"),)

    sensor_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(
        String(150), CheckConstraint("name <> ''", name="ck_Sensors_name"), nullable=False
    )
    sensor_type_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.SensorTypes.sensor_type_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    host = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Platforms.platform_id", onupdate="cascade", ondelete="CASCADE"),
        nullable=False,
    )
    privacy_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Privacies.privacy_id", onupdate="cascade", ondelete="cascade"),
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
    )

    platform_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(
        String(150), CheckConstraint("name <> ''", name="ck_Platforms_name"), nullable=False
    )
    identifier = Column(
        String(50),
        CheckConstraint("identifier <> ''", name="ck_Platforms_identifier"),
        nullable=False,
    )
    trigraph = deferred(Column(String(3)))
    quadgraph = deferred(Column(String(4)))
    nationality_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Nationalities.nationality_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    platform_type_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.PlatformTypes.platform_type_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    privacy_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Privacies.privacy_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class Series(BasePostGIS, SeriesMixin):
    __tablename__ = constants.SERIES
    table_type = TableTypes.METADATA
    table_type_id = 36

    series_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150), CheckConstraint("name <> ''", name="ck_Series_name"), nullable=False)
    privacy_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Privacies.privacy_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class Wargame(BasePostGIS, WargameMixin):
    __tablename__ = constants.WARGAME
    table_type = TableTypes.METADATA
    table_type_id = 37

    wargame_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(
        String(150), CheckConstraint("name <> ''", name="ck_Wargames_name"), nullable=False
    )
    series_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Series.series_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    start = Column(TIMESTAMP, nullable=False)
    end = Column(TIMESTAMP, nullable=False)
    privacy_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Privacies.privacy_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class Serial(BasePostGIS, SerialMixin):
    __tablename__ = constants.SERIAL
    table_type = TableTypes.METADATA
    table_type_id = 37

    __table_args__ = (
        UniqueConstraint("serial_number", "wargame_id", name="uq_Serial_serial_number_wargame_id"),
    )

    serial_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    wargame_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Wargames.wargame_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    serial_number = Column(
        String(150),
        CheckConstraint("serial_number <> ''", name="ck_Serials_serial_number"),
        nullable=False,
    )
    start = Column(TIMESTAMP, nullable=False)
    end = Column(TIMESTAMP, nullable=False)
    environment = Column(String(150))
    location = Column(String(150))
    exercise = Column(String(150))
    include_in_timeline = Column(Boolean, default=True)
    privacy_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Privacies.privacy_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class WargameParticipant(BasePostGIS, WargameParticipantMixin):
    __tablename__ = constants.WARGAME_PARTICIPANT
    table_type = TableTypes.METADATA
    table_type_id = 38

    wargame_participant_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    wargame_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Wargames.wargame_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    platform_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Platforms.platform_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    privacy_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Privacies.privacy_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class SerialParticipant(BasePostGIS, SerialParticipantMixin):
    __tablename__ = constants.SERIAL_PARTICIPANT
    table_type = TableTypes.METADATA
    table_type_id = 39

    serial_participant_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    wargame_participant_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "pepys.WargameParticipants.wargame_participant_id",
            onupdate="cascade",
            ondelete="cascade",
        ),
        nullable=False,
    )
    serial_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Serials.serial_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    start = Column(TIMESTAMP)
    end = Column(TIMESTAMP)
    force_type_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.ForceTypes.force_type_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    privacy_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Privacies.privacy_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class Datafile(BasePostGIS, DatafileMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.measurements = dict()
        self.highlighted_file = None
        self.pending_extracted_tokens = []
        self.measurement_object_to_tokens_list = {}
        self.current_measurement_object = None

    __tablename__ = constants.DATAFILE
    table_type = TableTypes.METADATA
    table_type_id = 6  # Only needed for tables referenced by Entry table
    __table_args__ = (UniqueConstraint("size", "hash", name="uq_Datafile_size_hash"),)

    datafile_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    simulated = deferred(Column(Boolean, nullable=False))
    privacy_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Privacies.privacy_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    datafile_type_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.DatafileTypes.datafile_type_id", onupdate="cascade", ondelete="cascade"),
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

    change_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user = Column(
        String(150), CheckConstraint("user <> ''", name="ck_Changes_user"), nullable=False
    )
    modified = Column(DATE, nullable=False)
    reason = Column(
        Text(), CheckConstraint("reason <> ''", name="ck_Changes_reason"), nullable=False
    )
    datafile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Datafiles.datafile_id", onupdate="cascade", ondelete="SET NULL"),
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class Log(BasePostGIS, LogMixin):
    __tablename__ = constants.LOG
    table_type = TableTypes.METADATA
    table_type_id = 9

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    table = Column(
        String(150), CheckConstraint("\"table\" <> ''", name="ck_Logs_table"), nullable=False
    )
    id = Column(UUID(as_uuid=True), nullable=False)
    field = Column(String(150))
    previous_value = Column(Text())
    change_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Changes.change_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class Extraction(BasePostGIS, ExtractionMixin):
    __tablename__ = constants.EXTRACTION
    table_type = TableTypes.METADATA
    table_type_id = 10

    extraction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    destination_table = Column(String(150))
    entry_id = Column(UUID(as_uuid=True))
    field = Column(String(150), nullable=False)
    datafile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("Datafiles.datafile_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    text = Column(Text(), nullable=False)
    text_location = Column(String(200), nullable=False)
    importer = Column(String(150), nullable=False)
    interpreted_value = Column(Text(), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Tag(BasePostGIS, ReferenceDefaultFields):
    __tablename__ = constants.TAG
    table_type = TableTypes.METADATA
    table_type_id = 11

    tag_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class TaggedItem(BasePostGIS, TaggedItemMixin):
    __tablename__ = constants.TAGGED_ITEM
    table_type = TableTypes.METADATA
    table_type_id = 12

    tagged_item_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tag_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Tags.tag_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    item_id = Column(UUID(as_uuid=True), nullable=False)
    tagged_by_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Users.user_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    private = Column(Boolean, nullable=False)
    tagged_on = Column(DATE, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


# Reference Tables
class ForceType(BasePostGIS, ReferenceRepr, ReferenceDefaultFields):
    __tablename__ = constants.FORCE_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 40

    force_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_ForceTypes_name"),
        nullable=False,
        unique=True,
    )
    color = Column(String(10))
    created_date = Column(DateTime, default=datetime.utcnow)


class PlatformType(BasePostGIS, ReferenceRepr, ReferenceDefaultFields):
    __tablename__ = constants.PLATFORM_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 13

    platform_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_PlatformTypes_name"),
        nullable=False,
        unique=True,
    )
    default_data_interval_secs = Column(Integer)
    created_date = Column(DateTime, default=datetime.utcnow)


class Nationality(BasePostGIS, ReferenceRepr, NationalityMixin):
    __tablename__ = constants.NATIONALITY
    table_type = TableTypes.REFERENCE
    table_type_id = 14

    nationality_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_Nationalities_name"),
        nullable=False,
        unique=True,
    )
    priority = Column(Integer)
    created_date = Column(DateTime, default=datetime.utcnow)


class GeometryType(BasePostGIS, ReferenceRepr, ReferenceDefaultFields):
    __tablename__ = constants.GEOMETRY_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 15

    geo_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_GeometryTypes_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class GeometrySubType(BasePostGIS, GeometrySubTypeMixin):
    __tablename__ = constants.GEOMETRY_SUBTYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 16
    __table_args__ = (UniqueConstraint("name", "parent", name="uq_GeometrySubType_name_parent"),)

    geo_sub_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(
        String(150), CheckConstraint("name <> ''", name="ck_GeometrySubTypes_name"), nullable=False
    )
    parent = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.GeometryTypes.geo_type_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class User(BasePostGIS, ReferenceRepr, ReferenceDefaultFields):
    __tablename__ = constants.USER
    table_type = TableTypes.REFERENCE
    table_type_id = 17

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_Users_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class UnitType(BasePostGIS, ReferenceRepr, ReferenceDefaultFields):
    __tablename__ = constants.UNIT_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 18

    unit_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_UnitTypes_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class ClassificationType(BasePostGIS, ReferenceRepr, ReferenceDefaultFields):
    __tablename__ = constants.CLASSIFICATION_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 19

    class_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_ClassificationTypes_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class ContactType(BasePostGIS, ReferenceRepr, ReferenceDefaultFields):
    __tablename__ = constants.CONTACT_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 20

    contact_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_ContactTypes_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class SensorType(BasePostGIS, ReferenceRepr, ReferenceDefaultFields):
    __tablename__ = constants.SENSOR_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 21

    sensor_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_SensorTypes_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class Privacy(BasePostGIS, ReferenceRepr, ReferenceDefaultFields):
    __tablename__ = constants.PRIVACY
    table_type = TableTypes.REFERENCE
    table_type_id = 22

    privacy_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    level = Column(Integer, nullable=False)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_Privacies_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class DatafileType(BasePostGIS, ReferenceRepr, ReferenceDefaultFields):
    __tablename__ = constants.DATAFILE_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 23

    datafile_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_DatafileTypes_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class MediaType(BasePostGIS, ReferenceRepr, ReferenceDefaultFields):
    __tablename__ = constants.MEDIA_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 24

    media_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_MediaTypes_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class CommentType(BasePostGIS, ReferenceRepr, ReferenceDefaultFields):
    __tablename__ = constants.COMMENT_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 25

    comment_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_CommentTypes_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class CommodityType(BasePostGIS, ReferenceRepr, ReferenceDefaultFields):
    __tablename__ = constants.COMMODITY_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 26

    commodity_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(
        String(150),
        CheckConstraint("name <> ''", name="ck_CommodityTypes_name"),
        nullable=False,
        unique=True,
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class ConfidenceLevel(BasePostGIS, ReferenceRepr, ReferenceDefaultFields):
    __tablename__ = constants.CONFIDENCE_LEVEL
    table_type = TableTypes.REFERENCE
    table_type_id = 27  # Only needed for tables referenced by Entry table

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

    state_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    time = Column(TIMESTAMP, nullable=False, index=True)
    sensor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Sensors.sensor_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    _location = deferred(Column("location", Geometry(geometry_type="POINT", srid=4326)))
    _elevation = deferred(Column("elevation", DOUBLE_PRECISION))
    _heading = deferred(Column("heading", DOUBLE_PRECISION))
    _course = deferred(Column("course", DOUBLE_PRECISION))
    _speed = deferred(Column("speed", DOUBLE_PRECISION))
    source_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Datafiles.datafile_id", onupdate="cascade", ondelete="CASCADE"),
        nullable=False,
    )
    privacy_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Privacies.privacy_id", onupdate="cascade", ondelete="cascade"),
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
            secondary="pepys.Sensors",
            primaryjoin="State.sensor_id == Sensor.sensor_id",
            secondaryjoin="Platform.platform_id == Sensor.host",
            lazy="joined",
            uselist=False,
            viewonly=True,
            # This specifies that when trying to query on this relationship
            # this is the local column (well, assoc proxy actually) to filter on
            info={"local_column": "platform_id"},
        )


class Contact(BasePostGIS, ContactMixin, LocationPropertyMixin, ElevationPropertyMixin):
    __tablename__ = constants.CONTACT
    table_type = TableTypes.MEASUREMENT
    table_type_id = 29

    contact_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150))
    sensor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Sensors.sensor_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    time = Column(TIMESTAMP, nullable=False, index=True)
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
    track_number = Column(String(40))
    subject_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Platforms.platform_id", onupdate="cascade", ondelete="cascade"),
    )
    source_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Datafiles.datafile_id", onupdate="cascade", ondelete="CASCADE"),
        nullable=False,
    )
    privacy_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Privacies.privacy_id", onupdate="cascade", ondelete="cascade"),
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
            secondary="pepys.Sensors",
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


class Activation(BasePostGIS, ActivationMixin):
    __tablename__ = constants.ACTIVATION
    table_type = TableTypes.MEASUREMENT
    table_type_id = 30

    activation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150))
    sensor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Sensors.sensor_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    start = deferred(Column(TIMESTAMP, index=True))
    end = deferred(Column(TIMESTAMP, index=True))
    _min_range = deferred(Column("min_range", DOUBLE_PRECISION))
    _max_range = deferred(Column("max_range", DOUBLE_PRECISION))
    _left_arc = deferred(Column("left_arc", DOUBLE_PRECISION))
    _right_arc = deferred(Column("right_arc", DOUBLE_PRECISION))
    source_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Datafiles.datafile_id", onupdate="cascade", ondelete="CASCADE"),
        nullable=False,
    )
    privacy_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Privacies.privacy_id", onupdate="cascade", ondelete="cascade"),
    )
    remarks = Column(Text)
    created_date = Column(DateTime, default=datetime.utcnow)


class LogsHolding(BasePostGIS, LogsHoldingMixin):
    __tablename__ = constants.LOGS_HOLDING
    table_type = TableTypes.MEASUREMENT
    table_type_id = 31

    logs_holding_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    time = Column(TIMESTAMP, nullable=False)
    commodity_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "pepys.CommodityTypes.commodity_type_id", onupdate="cascade", ondelete="cascade"
        ),
        nullable=False,
    )
    quantity = Column(DOUBLE_PRECISION, nullable=False)
    unit_type_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.UnitTypes.unit_type_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    platform_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Platforms.platform_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    comment = Column(Text, nullable=False)
    source_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Datafiles.datafile_id", onupdate="cascade", ondelete="CASCADE"),
        nullable=False,
    )
    privacy_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Privacies.privacy_id", onupdate="cascade", ondelete="cascade"),
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class Comment(BasePostGIS, CommentMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sensor_name = "N/A"

    __tablename__ = constants.COMMENT
    table_type = TableTypes.MEASUREMENT
    table_type_id = 32

    comment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    platform_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Platforms.platform_id", onupdate="cascade", ondelete="cascade"),
    )
    time = Column(TIMESTAMP, nullable=False, index=True)
    comment_type_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.CommentTypes.comment_type_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    content = Column(
        Text, CheckConstraint("content <> ''", name="ck_Comment_content"), nullable=False
    )
    source_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Datafiles.datafile_id", onupdate="cascade", ondelete="CASCADE"),
        nullable=False,
    )
    privacy_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Privacies.privacy_id", onupdate="cascade", ondelete="cascade"),
    )
    created_date = Column(DateTime, default=datetime.utcnow)


class Geometry1(BasePostGIS, GeometryMixin):
    __tablename__ = constants.GEOMETRY
    table_type = TableTypes.MEASUREMENT
    table_type_id = 33

    geometry_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    _geometry = Column("geometry", Geometry(srid=4326), nullable=False)
    name = Column(String(150))
    geo_type_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.GeometryTypes.geo_type_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    geo_sub_type_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "pepys.GeometrySubTypes.geo_sub_type_id", onupdate="cascade", ondelete="cascade"
        ),
        nullable=False,
    )
    start = Column(TIMESTAMP, index=True)
    end = Column(TIMESTAMP, index=True)
    serial_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Serials.serial_id", onupdate="cascade", ondelete="cascade"),
    )
    subject_platform_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Platforms.platform_id", onupdate="cascade", ondelete="cascade"),
    )
    sensor_platform_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Platforms.platform_id", onupdate="cascade", ondelete="cascade"),
    )
    source_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Datafiles.datafile_id", onupdate="cascade", ondelete="CASCADE"),
        nullable=False,
    )
    privacy_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Privacies.privacy_id", onupdate="cascade", ondelete="cascade"),
    )
    remarks = Column(Text)
    created_date = Column(DateTime, default=datetime.utcnow)


class Media(BasePostGIS, MediaMixin, ElevationPropertyMixin, LocationPropertyMixin):
    __tablename__ = constants.MEDIA
    table_type = TableTypes.MEASUREMENT
    table_type_id = 34

    media_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    platform_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Platforms.platform_id", onupdate="cascade", ondelete="cascade"),
    )
    subject_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Platforms.platform_id", onupdate="cascade", ondelete="cascade"),
    )
    sensor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Sensors.sensor_id", onupdate="cascade", ondelete="cascade"),
    )
    _location = deferred(Column("location", Geometry(geometry_type="POINT", srid=4326)))
    _elevation = deferred(Column("elevation", DOUBLE_PRECISION))
    time = Column(TIMESTAMP, index=True)
    media_type_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.MediaTypes.media_type_id", onupdate="cascade", ondelete="cascade"),
        nullable=False,
    )
    url = deferred(
        Column(String(150), CheckConstraint("url <> ''", name="ck_Media_url"), nullable=False)
    )
    source_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Datafiles.datafile_id", onupdate="cascade", ondelete="CASCADE"),
        nullable=False,
    )
    privacy_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pepys.Privacies.privacy_id", onupdate="cascade", ondelete="cascade"),
    )
    remarks = Column(Text)
    created_date = Column(DateTime, default=datetime.utcnow)


class HelpText(BasePostGIS):
    __tablename__ = constants.HELP_TEXT
    table_type = TableTypes.REFERENCE
    table_type_id = 35

    help_text_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    id = Column(String(50), nullable=False)
    guidance = Column(String(2000), nullable=False)
