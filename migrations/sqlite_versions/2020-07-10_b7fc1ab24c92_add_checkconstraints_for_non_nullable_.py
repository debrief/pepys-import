"""Add CheckConstraints for non-nullable string cols

Revision ID: b7fc1ab24c92
Revises: d5d740c76aa3
Create Date: 2020-07-10 13:24:56.007611

"""
from datetime import datetime
from uuid import uuid4

import geoalchemy2
import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy import DATE, Boolean, Column, DateTime, ForeignKey, Integer, MetaData, String, Text
from sqlalchemy.dialects.sqlite import REAL, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import deferred
from sqlalchemy.sql.schema import CheckConstraint

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
    ReferenceRepr,
    SensorMixin,
    StateMixin,
    SynonymMixin,
    TaggedItemMixin,
    TaskMixin,
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

    class Task(BaseSpatiaLite, TaskMixin):
        __tablename__ = constants.TASK
        table_type = TableTypes.METADATA
        table_type_id = 4

        task_id = Column(UUIDType, primary_key=True, default=uuid4)
        name = Column(
            String(150), CheckConstraint("name <> ''", name="ck_Tasks_name"), nullable=False
        )
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

    with op.batch_alter_table("Tasks", schema=None, copy_from=Task.__table__) as batch_op:
        batch_op.drop_constraint("ck_Tasks_name", type_="check")

    with op.batch_alter_table("Synonyms", schema=None) as batch_op:
        batch_op.drop_constraint("ck_Synonyms_table", type_="check")
        batch_op.drop_constraint("ck_Synonyms_synonym", type_="check")

    with op.batch_alter_table("Changes", schema=None) as batch_op:
        batch_op.drop_constraint("ck_Changes_user", type_="check")
        batch_op.drop_constraint("ck_Changes_reason", type_="check")

    with op.batch_alter_table("Logs", schema=None) as batch_op:
        batch_op.drop_constraint("ck_Logs_table", type_="check")

    with op.batch_alter_table("PlatformTypes", schema=None) as batch_op:
        batch_op.drop_constraint("ck_PlatformTypes_name", type_="check")

    with op.batch_alter_table("Nationalities", schema=None) as batch_op:
        batch_op.drop_constraint("ck_Nationalities_name", type_="check")

    with op.batch_alter_table("GeometryTypes", schema=None) as batch_op:
        batch_op.drop_constraint("ck_GeometryTypes_name", type_="check")

    with op.batch_alter_table("GeometrySubTypes", schema=None) as batch_op:
        batch_op.drop_constraint("ck_GeometrySubTypes_name", type_="check")

    with op.batch_alter_table("Users", schema=None) as batch_op:
        batch_op.drop_constraint("ck_Users_name", type_="check")

    with op.batch_alter_table("UnitTypes", schema=None) as batch_op:
        batch_op.drop_constraint("ck_UnitTypes_name", type_="check")

    with op.batch_alter_table("ClassificationTypes", schema=None) as batch_op:
        batch_op.drop_constraint("ck_ClassificationTypes_name", type_="check")

    with op.batch_alter_table("ContactTypes", schema=None) as batch_op:
        batch_op.drop_constraint("ck_ContactTypes_name", type_="check")

    with op.batch_alter_table("SensorTypes", schema=None) as batch_op:
        batch_op.drop_constraint("ck_SensorTypes_name", type_="check")

    with op.batch_alter_table("Privacies", schema=None) as batch_op:
        batch_op.drop_constraint("ck_Privacies_name", type_="check")

    with op.batch_alter_table("DatafileTypes", schema=None) as batch_op:
        batch_op.drop_constraint("ck_DatafileTypes_name", type_="check")

    with op.batch_alter_table("MediaTypes", schema=None) as batch_op:
        batch_op.drop_constraint("ck_MediaTypes_name", type_="check")

    with op.batch_alter_table("CommentTypes", schema=None) as batch_op:
        batch_op.drop_constraint("ck_CommentTypes_name", type_="check")

    with op.batch_alter_table("CommodityTypes", schema=None) as batch_op:
        batch_op.drop_constraint("ck_CommodityTypes_name", type_="check")

    with op.batch_alter_table("ConfidenceLevels", schema=None) as batch_op:
        batch_op.drop_constraint("ck_ConfidenceLevels_name", type_="check")

    with op.batch_alter_table("Comments", schema=None) as batch_op:
        batch_op.drop_constraint("ck_Comments_content", type_="check")

    with op.batch_alter_table("Media", schema=None) as batch_op:
        batch_op.drop_constraint("ck_Media_url", type_="check")
