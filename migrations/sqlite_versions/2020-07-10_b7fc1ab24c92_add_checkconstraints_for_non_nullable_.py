"""Add CheckConstraints for non-nullable string cols

Revision ID: b7fc1ab24c92
Revises: d5d740c76aa3
Create Date: 2020-07-10 13:24:56.007611

"""
from datetime import datetime
from uuid import uuid4

from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy import DATE, Column, DateTime, ForeignKey, Integer, MetaData, String, Text
from sqlalchemy.dialects.sqlite import REAL, TIMESTAMP
from sqlalchemy.orm import declarative_base, deferred
from sqlalchemy.sql.schema import CheckConstraint, UniqueConstraint

from pepys_import.core.store import constants
from pepys_import.core.store.common_db import (
    CommentMixin,
    ElevationPropertyMixin,
    LocationPropertyMixin,
    LogMixin,
    MediaMixin,
    ReferenceRepr,
    SynonymMixin,
)
from pepys_import.core.store.db_base import sqlite_naming_convention
from pepys_import.core.store.db_status import TableTypes
from pepys_import.utils.sqlalchemy_utils import UUIDType

# revision identifiers, used by Alembic.
revision = "b7fc1ab24c92"
down_revision = "d5d740c76aa3"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("Tasks", schema=None) as batch_op:
        batch_op.create_check_constraint("ck_Tasks_name", condition="name <> ''")

    with op.batch_alter_table("Synonyms", schema=None) as batch_op:
        batch_op.create_check_constraint("ck_Synonyms_table", condition="\"table\" <> ''")
        batch_op.create_check_constraint("ck_Synonyms_synonym", condition="synonym <> ''")

    with op.batch_alter_table("Changes", schema=None) as batch_op:
        batch_op.create_check_constraint("ck_Changes_user", condition="user <> ''")
        batch_op.create_check_constraint("ck_Changes_reason", condition="reason <> ''")

    with op.batch_alter_table("Logs", schema=None) as batch_op:
        batch_op.create_check_constraint("ck_Logs_table", condition="\"table\" <> ''")

    with op.batch_alter_table("PlatformTypes", schema=None) as batch_op:
        batch_op.create_check_constraint("ck_PlatformTypes_name", condition="name <> ''")

    with op.batch_alter_table("Nationalities", schema=None) as batch_op:
        batch_op.create_check_constraint("ck_Nationalities_name", condition="name <> ''")

    with op.batch_alter_table("GeometryTypes", schema=None) as batch_op:
        batch_op.create_check_constraint("ck_GeometryTypes_name", condition="name <> ''")

    with op.batch_alter_table("GeometrySubTypes", schema=None) as batch_op:
        batch_op.create_check_constraint("ck_GeometrySubTypes_name", condition="name <> ''")

    with op.batch_alter_table("Users", schema=None) as batch_op:
        batch_op.create_check_constraint("ck_Users_name", condition="name <> ''")

    with op.batch_alter_table("UnitTypes", schema=None) as batch_op:
        batch_op.create_check_constraint("ck_UnitTypes_name", condition="name <> ''")

    with op.batch_alter_table("ClassificationTypes", schema=None) as batch_op:
        batch_op.create_check_constraint("ck_ClassificationTypes_name", condition="name <> ''")

    with op.batch_alter_table("ContactTypes", schema=None) as batch_op:
        batch_op.create_check_constraint("ck_ContactTypes_name", condition="name <> ''")

    with op.batch_alter_table("SensorTypes", schema=None) as batch_op:
        batch_op.create_check_constraint("ck_SensorTypes_name", condition="name <> ''")

    with op.batch_alter_table("Privacies", schema=None) as batch_op:
        batch_op.create_check_constraint("ck_Privacies_name", condition="name <> ''")

    with op.batch_alter_table("DatafileTypes", schema=None) as batch_op:
        batch_op.create_check_constraint("ck_DatafileTypes_name", condition="name <> ''")

    with op.batch_alter_table("MediaTypes", schema=None) as batch_op:
        batch_op.create_check_constraint("ck_MediaTypes_name", condition="name <> ''")

    with op.batch_alter_table("CommentTypes", schema=None) as batch_op:
        batch_op.create_check_constraint("ck_CommentTypes_name", condition="name <> ''")

    with op.batch_alter_table("CommodityTypes", schema=None) as batch_op:
        batch_op.create_check_constraint("ck_CommodityTypes_name", condition="name <> ''")

    with op.batch_alter_table("ConfidenceLevels", schema=None) as batch_op:
        batch_op.create_check_constraint("ck_ConfidenceLevels_name", condition="name <> ''")

    with op.batch_alter_table("Comments", schema=None) as batch_op:
        batch_op.create_check_constraint("ck_Comments_content", condition="content <> ''")

    with op.batch_alter_table("Media", schema=None) as batch_op:
        batch_op.create_check_constraint("ck_Media_url", condition="url <> ''")


def downgrade():
    Metadata = MetaData(naming_convention=sqlite_naming_convention)
    BaseSpatiaLite = declarative_base(metadata=Metadata)

    class Task(BaseSpatiaLite):
        __tablename__ = constants.TASK
        table_type = TableTypes.METADATA
        table_type_id = 4

        task_id = Column(UUIDType, primary_key=True, default=uuid4)
        name = Column(String(150), nullable=False)
        parent_id = Column(
            UUIDType, ForeignKey("Tasks.task_id", onupdate="cascade"), nullable=False
        )
        start = Column(TIMESTAMP, nullable=False)
        end = Column(TIMESTAMP, nullable=False)
        environment = deferred(Column(String(150)))
        location = deferred(Column(String(150)))
        privacy_id = Column(
            UUIDType, ForeignKey("Privacies.privacy_id", onupdate="cascade"), nullable=False
        )
        created_date = Column(DateTime, default=datetime.utcnow)

        __table_args__ = (CheckConstraint("name <> ''", name="ck_Tasks_name"),)

    class Synonym(BaseSpatiaLite, SynonymMixin):
        __tablename__ = constants.SYNONYM
        table_type = TableTypes.METADATA
        table_type_id = 7

        synonym_id = Column(UUIDType, primary_key=True, default=uuid4)
        table = Column(String(150), nullable=False)
        entity = Column(UUIDType, nullable=False)
        synonym = Column(String(150), nullable=False)
        created_date = Column(DateTime, default=datetime.utcnow)

        __table_args__ = (
            CheckConstraint("\"table\" <> ''", name="ck_Synonyms_table"),
            CheckConstraint("synonym <> ''", name="ck_Synonyms_synonym"),
        )

    class Change(BaseSpatiaLite):
        __tablename__ = constants.CHANGE
        table_type = TableTypes.METADATA
        table_type_id = 8

        change_id = Column(UUIDType, primary_key=True, default=uuid4)
        user = Column(String(150), nullable=False)
        modified = Column(DATE, nullable=False)
        reason = Column(String(500), nullable=False)
        created_date = Column(DateTime, default=datetime.utcnow)

        __table_args__ = (
            CheckConstraint("user <> ''", name="ck_Changes_user"),
            CheckConstraint("reason <> ''", name="ck_Changes_reason"),
        )

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

        __table_args__ = (CheckConstraint("\"table\" <> ''", name="ck_Logs_table"),)

    class PlatformType(BaseSpatiaLite, ReferenceRepr):
        __tablename__ = constants.PLATFORM_TYPE
        table_type = TableTypes.REFERENCE
        table_type_id = 13

        platform_type_id = Column(UUIDType, primary_key=True, default=uuid4)
        name = Column(
            String(150),
            nullable=False,
            unique=True,
        )
        created_date = Column(DateTime, default=datetime.utcnow)

        __table_args__ = (CheckConstraint("name <> ''", name="ck_PlatformTypes_name"),)

    class Nationality(BaseSpatiaLite, ReferenceRepr):
        __tablename__ = constants.NATIONALITY
        table_type = TableTypes.REFERENCE
        table_type_id = 14

        nationality_id = Column(UUIDType, primary_key=True, default=uuid4)
        name = Column(
            String(150),
            nullable=False,
            unique=True,
        )
        priority = Column(Integer)
        created_date = Column(DateTime, default=datetime.utcnow)

        __table_args__ = (CheckConstraint("name <> ''", name="ck_Nationalities_name"),)

    class GeometryType(BaseSpatiaLite, ReferenceRepr):
        __tablename__ = constants.GEOMETRY_TYPE
        table_type = TableTypes.REFERENCE
        table_type_id = 15

        geo_type_id = Column(UUIDType, primary_key=True, default=uuid4)
        name = Column(
            String(150),
            nullable=False,
            unique=True,
        )
        created_date = Column(DateTime, default=datetime.utcnow)

        __table_args__ = (CheckConstraint("name <> ''", name="ck_GeometryTypes_name"),)

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

        __table_args__ = (
            UniqueConstraint("name", "parent", name="uq_GeometrySubTypes_name_parent"),
            CheckConstraint("name <> ''", name="ck_GeometrySubTypes_name"),
        )

    class User(BaseSpatiaLite, ReferenceRepr):
        __tablename__ = constants.USER
        table_type = TableTypes.REFERENCE
        table_type_id = 17

        user_id = Column(UUIDType, primary_key=True, default=uuid4)
        name = Column(
            String(150),
            nullable=False,
            unique=True,
        )
        created_date = Column(DateTime, default=datetime.utcnow)

        __table_args__ = (CheckConstraint("name <> ''", name="ck_Users_name"),)

    class UnitType(BaseSpatiaLite, ReferenceRepr):
        __tablename__ = constants.UNIT_TYPE
        table_type = TableTypes.REFERENCE
        table_type_id = 18

        unit_type_id = Column(UUIDType, primary_key=True, default=uuid4)
        name = Column(
            String(150),
            nullable=False,
            unique=True,
        )
        created_date = Column(DateTime, default=datetime.utcnow)

        __table_args__ = (CheckConstraint("name <> ''", name="ck_UnitTypes_name"),)

    class ClassificationType(BaseSpatiaLite, ReferenceRepr):
        __tablename__ = constants.CLASSIFICATION_TYPE
        table_type = TableTypes.REFERENCE
        table_type_id = 19

        class_type_id = Column(UUIDType, primary_key=True, default=uuid4)
        name = Column(
            String(150),
            nullable=False,
            unique=True,
        )
        created_date = Column(DateTime, default=datetime.utcnow)

        __table_args__ = (CheckConstraint("name <> ''", name="ck_ClassificationTypes_name"),)

    class ContactType(BaseSpatiaLite, ReferenceRepr):
        __tablename__ = constants.CONTACT_TYPE
        table_type = TableTypes.REFERENCE
        table_type_id = 20

        contact_type_id = Column(UUIDType, primary_key=True, default=uuid4)
        name = Column(
            String(150),
            nullable=False,
            unique=True,
        )
        created_date = Column(DateTime, default=datetime.utcnow)

        __table_args__ = (CheckConstraint("name <> ''", name="ck_ContactTypes_name"),)

    class SensorType(BaseSpatiaLite, ReferenceRepr):
        __tablename__ = constants.SENSOR_TYPE
        table_type = TableTypes.REFERENCE
        table_type_id = 21

        sensor_type_id = Column(UUIDType, primary_key=True, default=uuid4)
        name = Column(
            String(150),
            nullable=False,
            unique=True,
        )
        created_date = Column(DateTime, default=datetime.utcnow)

        __table_args__ = (CheckConstraint("name <> ''", name="ck_SensorTypes_name"),)

    class Privacy(BaseSpatiaLite, ReferenceRepr):
        __tablename__ = constants.PRIVACY
        table_type = TableTypes.REFERENCE
        table_type_id = 22

        privacy_id = Column(UUIDType, primary_key=True, default=uuid4)
        name = Column(
            String(150),
            nullable=False,
            unique=True,
        )
        level = Column(Integer, nullable=False)
        created_date = Column(DateTime, default=datetime.utcnow)

        __table_args__ = (CheckConstraint("name <> ''", name="ck_Privacies_name"),)

    class DatafileType(BaseSpatiaLite, ReferenceRepr):
        __tablename__ = constants.DATAFILE_TYPE
        table_type = TableTypes.REFERENCE
        table_type_id = 23

        datafile_type_id = Column(UUIDType, primary_key=True, default=uuid4)
        name = Column(
            String(150),
            nullable=False,
            unique=True,
        )
        created_date = Column(DateTime, default=datetime.utcnow)

        __table_args__ = (CheckConstraint("name <> ''", name="ck_DatafileTypes_name"),)

    class MediaType(BaseSpatiaLite, ReferenceRepr):
        __tablename__ = constants.MEDIA_TYPE
        table_type = TableTypes.REFERENCE
        table_type_id = 24

        media_type_id = Column(UUIDType, primary_key=True, default=uuid4)
        name = Column(
            String(150),
            nullable=False,
            unique=True,
        )
        created_date = Column(DateTime, default=datetime.utcnow)

        __table_args__ = (CheckConstraint("name <> ''", name="ck_MediaTypes_name"),)

    class CommentType(BaseSpatiaLite, ReferenceRepr):
        __tablename__ = constants.COMMENT_TYPE
        table_type = TableTypes.REFERENCE
        table_type_id = 25

        comment_type_id = Column(UUIDType, primary_key=True, default=uuid4)
        name = Column(
            String(150),
            nullable=False,
            unique=True,
        )
        created_date = Column(DateTime, default=datetime.utcnow)

        __table_args__ = (CheckConstraint("name <> ''", name="ck_CommentTypes_name"),)

    class CommodityType(BaseSpatiaLite, ReferenceRepr):
        __tablename__ = constants.COMMODITY_TYPE
        table_type = TableTypes.REFERENCE
        table_type_id = 26

        commodity_type_id = Column(UUIDType, primary_key=True, default=uuid4)
        name = Column(
            String(150),
            nullable=False,
            unique=True,
        )
        created_date = Column(DateTime, default=datetime.utcnow)

        __table_args__ = (CheckConstraint("name <> ''", name="ck_CommodityTypes_name"),)

    class ConfidenceLevel(BaseSpatiaLite, ReferenceRepr):
        __tablename__ = constants.CONFIDENCE_LEVEL
        table_type = TableTypes.REFERENCE
        table_type_id = 27

        confidence_level_id = Column(UUIDType, primary_key=True, default=uuid4)
        name = Column(
            String(150),
            nullable=False,
            unique=True,
        )
        created_date = Column(DateTime, default=datetime.utcnow)

        __table_args__ = (CheckConstraint("name <> ''", name="ck_ConfidenceLevels_name"),)

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

        __table_args__ = (CheckConstraint("content <> ''", name="ck_Comments_content"),)

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

        __table_args__ = (CheckConstraint("url <> ''", name="ck_Media_url"),)

    with op.batch_alter_table("Tasks", schema=None, copy_from=Task.__table__) as batch_op:
        batch_op.drop_constraint("ck_Tasks_name", type_="check")

    with op.batch_alter_table("Synonyms", schema=None, copy_from=Synonym.__table__) as batch_op:
        batch_op.drop_constraint("ck_Synonyms_table", type_="check")
        batch_op.drop_constraint("ck_Synonyms_synonym", type_="check")

    with op.batch_alter_table("Changes", schema=None, copy_from=Change.__table__) as batch_op:
        batch_op.drop_constraint("ck_Changes_user", type_="check")
        batch_op.drop_constraint("ck_Changes_reason", type_="check")

    with op.batch_alter_table("Logs", schema=None, copy_from=Log.__table__) as batch_op:
        batch_op.drop_constraint("ck_Logs_table", type_="check")

    with op.batch_alter_table(
        "PlatformTypes", schema=None, copy_from=PlatformType.__table__
    ) as batch_op:
        batch_op.drop_constraint("ck_PlatformTypes_name", type_="check")

    with op.batch_alter_table(
        "Nationalities", schema=None, copy_from=Nationality.__table__
    ) as batch_op:
        batch_op.drop_constraint("ck_Nationalities_name", type_="check")

    with op.batch_alter_table(
        "GeometryTypes", schema=None, copy_from=GeometryType.__table__
    ) as batch_op:
        batch_op.drop_constraint("ck_GeometryTypes_name", type_="check")

    with op.batch_alter_table(
        "GeometrySubTypes", schema=None, copy_from=GeometrySubType.__table__
    ) as batch_op:
        batch_op.drop_constraint("ck_GeometrySubTypes_name", type_="check")

    with op.batch_alter_table("Users", schema=None, copy_from=User.__table__) as batch_op:
        batch_op.drop_constraint("ck_Users_name", type_="check")

    with op.batch_alter_table("UnitTypes", schema=None, copy_from=UnitType.__table__) as batch_op:
        batch_op.drop_constraint("ck_UnitTypes_name", type_="check")

    with op.batch_alter_table(
        "ClassificationTypes", schema=None, copy_from=ClassificationType.__table__
    ) as batch_op:
        batch_op.drop_constraint("ck_ClassificationTypes_name", type_="check")

    with op.batch_alter_table(
        "ContactTypes", schema=None, copy_from=ContactType.__table__
    ) as batch_op:
        batch_op.drop_constraint("ck_ContactTypes_name", type_="check")

    with op.batch_alter_table(
        "SensorTypes", schema=None, copy_from=SensorType.__table__
    ) as batch_op:
        batch_op.drop_constraint("ck_SensorTypes_name", type_="check")

    with op.batch_alter_table("Privacies", schema=None, copy_from=Privacy.__table__) as batch_op:
        batch_op.drop_constraint("ck_Privacies_name", type_="check")

    with op.batch_alter_table(
        "DatafileTypes", schema=None, copy_from=DatafileType.__table__
    ) as batch_op:
        batch_op.drop_constraint("ck_DatafileTypes_name", type_="check")

    with op.batch_alter_table("MediaTypes", schema=None, copy_from=MediaType.__table__) as batch_op:
        batch_op.drop_constraint("ck_MediaTypes_name", type_="check")

    with op.batch_alter_table(
        "CommentTypes", schema=None, copy_from=CommentType.__table__
    ) as batch_op:
        batch_op.drop_constraint("ck_CommentTypes_name", type_="check")

    with op.batch_alter_table(
        "CommodityTypes", schema=None, copy_from=CommodityType.__table__
    ) as batch_op:
        batch_op.drop_constraint("ck_CommodityTypes_name", type_="check")

    with op.batch_alter_table(
        "ConfidenceLevels", schema=None, copy_from=ConfidenceLevel.__table__
    ) as batch_op:
        batch_op.drop_constraint("ck_ConfidenceLevels_name", type_="check")

    with op.batch_alter_table("Comments", schema=None, copy_from=Comment.__table__) as batch_op:
        batch_op.drop_constraint("ck_Comments_content", type_="check")

    with op.batch_alter_table("Media", schema=None, copy_from=Media.__table__) as batch_op:
        batch_op.drop_constraint("ck_Media_url", type_="check")
