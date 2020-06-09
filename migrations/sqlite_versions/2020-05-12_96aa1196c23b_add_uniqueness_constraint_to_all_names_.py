"""Add uniqueness constraint to all names in reference tables

Revision ID: 96aa1196c23b
Revises: 7df9dcbd47e7
Create Date: 2020-05-12 10:34:21.151949

"""
from datetime import datetime
from uuid import uuid4

import geoalchemy2
import sqlalchemy as sa
from alembic import op
from sqlalchemy import Column, DateTime, ForeignKey, MetaData, String
from sqlalchemy.ext.declarative import declarative_base

from pepys_import.core.store import constants
from pepys_import.core.store.db_base import sqlite_naming_convention
from pepys_import.core.store.db_status import TableTypes
from pepys_import.utils.sqlalchemy_utils import UUIDType

Metadata = MetaData(naming_convention=sqlite_naming_convention)
BaseSpatiaLite = declarative_base(metadata=Metadata)


class ClassificationType(BaseSpatiaLite):
    __tablename__ = constants.CLASSIFICATION_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 19

    class_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    class_type = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class CommentType(BaseSpatiaLite):
    __tablename__ = constants.COMMENT_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 25

    comment_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class CommodityType(BaseSpatiaLite):
    __tablename__ = constants.COMMODITY_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 26

    commodity_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class ContactType(BaseSpatiaLite):
    __tablename__ = constants.CONTACT_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 20

    contact_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    contact_type = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class UnitType(BaseSpatiaLite):
    __tablename__ = constants.UNIT_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 18

    unit_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class SensorType(BaseSpatiaLite):
    __tablename__ = constants.SENSOR_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 21

    sensor_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class ConfidenceLevel(BaseSpatiaLite):
    __tablename__ = constants.CONFIDENCE_LEVEL
    table_type = TableTypes.REFERENCE
    table_type_id = 27

    confidence_level_id = Column(UUIDType, primary_key=True, default=uuid4)
    level = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class Nationality(BaseSpatiaLite):
    __tablename__ = constants.NATIONALITY
    table_type = TableTypes.REFERENCE
    table_type_id = 14

    nationality_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)

    created_date = Column(DateTime, default=datetime.utcnow)


class MediaType(BaseSpatiaLite):
    __tablename__ = constants.MEDIA_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 24

    media_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class Privacy(BaseSpatiaLite):
    __tablename__ = constants.PRIVACY
    table_type = TableTypes.REFERENCE
    table_type_id = 22

    privacy_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)

    created_date = Column(DateTime, default=datetime.utcnow)


class User(BaseSpatiaLite):
    __tablename__ = constants.USER
    table_type = TableTypes.REFERENCE
    table_type_id = 17

    user_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
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


class GeometryType(BaseSpatiaLite):
    __tablename__ = constants.GEOMETRY_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 15

    geo_type_id = Column(UUIDType, primary_key=True, default=uuid4)
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
revision = "96aa1196c23b"
down_revision = "7df9dcbd47e7"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table(
        "ClassificationTypes", schema=None, copy_from=ClassificationType.__table__
    ) as batch_op:
        batch_op.create_unique_constraint(
            batch_op.f("uq_ClassificationTypes_class_type"), ["class_type"]
        )

    with op.batch_alter_table(
        "CommentTypes", schema=None, copy_from=CommentType.__table__
    ) as batch_op:
        batch_op.create_unique_constraint(batch_op.f("uq_CommentTypes_name"), ["name"])

    with op.batch_alter_table(
        "CommodityTypes", schema=None, copy_from=CommodityType.__table__
    ) as batch_op:
        batch_op.create_unique_constraint(batch_op.f("uq_CommodityTypes_name"), ["name"])

    with op.batch_alter_table(
        "ConfidenceLevels", schema=None, copy_from=ConfidenceLevel.__table__
    ) as batch_op:
        batch_op.create_unique_constraint(batch_op.f("uq_ConfidenceLevels_level"), ["level"])

    with op.batch_alter_table(
        "ContactTypes", schema=None, copy_from=ContactType.__table__
    ) as batch_op:
        batch_op.create_unique_constraint(
            batch_op.f("uq_ContactTypes_contact_type"), ["contact_type"]
        )

    with op.batch_alter_table(
        "DatafileTypes", schema=None, copy_from=DatafileType.__table__
    ) as batch_op:
        batch_op.create_unique_constraint(batch_op.f("uq_DatafileTypes_name"), ["name"])

    with op.batch_alter_table(
        "GeometrySubTypes", schema=None, copy_from=GeometrySubType.__table__
    ) as batch_op:
        batch_op.create_unique_constraint(batch_op.f("uq_GeometrySubTypes_name"), ["name"])

    with op.batch_alter_table(
        "GeometryTypes", schema=None, copy_from=GeometryType.__table__
    ) as batch_op:
        batch_op.create_unique_constraint(batch_op.f("uq_GeometryTypes_name"), ["name"])

    with op.batch_alter_table("MediaTypes", schema=None, copy_from=MediaType.__table__) as batch_op:
        batch_op.create_unique_constraint(batch_op.f("uq_MediaTypes_name"), ["name"])

    with op.batch_alter_table(
        "Nationalities", schema=None, copy_from=Nationality.__table__
    ) as batch_op:
        batch_op.create_unique_constraint(batch_op.f("uq_Nationalities_name"), ["name"])

    with op.batch_alter_table(
        "PlatformTypes", schema=None, copy_from=PlatformType.__table__
    ) as batch_op:
        batch_op.alter_column("name", existing_type=sa.VARCHAR(length=150), nullable=False)
        batch_op.create_unique_constraint(batch_op.f("uq_PlatformTypes_name"), ["name"])

    with op.batch_alter_table("Privacies", schema=None, copy_from=Privacy.__table__) as batch_op:
        batch_op.create_unique_constraint(batch_op.f("uq_Privacies_name"), ["name"])

    with op.batch_alter_table(
        "SensorTypes", schema=None, copy_from=SensorType.__table__
    ) as batch_op:
        batch_op.alter_column("name", existing_type=sa.VARCHAR(length=150), nullable=False)
        batch_op.create_unique_constraint(batch_op.f("uq_SensorTypes_name"), ["name"])

    with op.batch_alter_table("UnitTypes", schema=None, copy_from=UnitType.__table__) as batch_op:
        batch_op.create_unique_constraint(batch_op.f("uq_UnitTypes_name"), ["name"])

    with op.batch_alter_table("Users", schema=None, copy_from=User.__table__) as batch_op:
        batch_op.create_unique_constraint(batch_op.f("uq_Users_name"), ["name"])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("Users", schema=None, copy_from=User.__table__) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_Users_name"), type_="unique")

    with op.batch_alter_table("UnitTypes", schema=None, copy_from=UnitType.__table__) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_UnitTypes_name"), type_="unique")

    with op.batch_alter_table(
        "SensorTypes", schema=None, copy_from=SensorType.__table__
    ) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_SensorTypes_name"), type_="unique")
        batch_op.alter_column("name", existing_type=sa.VARCHAR(length=150), nullable=True)

    with op.batch_alter_table("Privacies", schema=None, copy_from=Privacy.__table__) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_Privacies_name"), type_="unique")

    with op.batch_alter_table(
        "PlatformTypes", schema=None, copy_from=PlatformType.__table__
    ) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_PlatformTypes_name"), type_="unique")
        batch_op.alter_column("name", existing_type=sa.VARCHAR(length=150), nullable=True)

    with op.batch_alter_table(
        "Nationalities", schema=None, copy_from=Nationality.__table__
    ) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_Nationalities_name"), type_="unique")

    with op.batch_alter_table("MediaTypes", schema=None, copy_from=MediaType.__table__) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_MediaTypes_name"), type_="unique")

    with op.batch_alter_table(
        "GeometryTypes", schema=None, copy_from=GeometryType.__table__
    ) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_GeometryTypes_name"), type_="unique")

    with op.batch_alter_table(
        "GeometrySubTypes", schema=None, copy_from=GeometrySubType.__table__
    ) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_GeometrySubTypes_name"), type_="unique")

    with op.batch_alter_table(
        "DatafileTypes", schema=None, copy_from=DatafileType.__table__
    ) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_DatafileTypes_name"), type_="unique")

    with op.batch_alter_table(
        "ContactTypes", schema=None, copy_from=ContactType.__table__
    ) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_ContactTypes_contact_type"), type_="unique")

    with op.batch_alter_table(
        "ConfidenceLevels", schema=None, copy_from=ConfidenceLevel.__table__
    ) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_ConfidenceLevels_level"), type_="unique")

    with op.batch_alter_table(
        "CommodityTypes", schema=None, copy_from=CommodityType.__table__
    ) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_CommodityTypes_name"), type_="unique")

    with op.batch_alter_table(
        "CommentTypes", schema=None, copy_from=CommentType.__table__
    ) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_CommentTypes_name"), type_="unique")

    with op.batch_alter_table(
        "ClassificationTypes", schema=None, copy_from=ClassificationType.__table__
    ) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_ClassificationTypes_class_type"), type_="unique")

    # ### end Alembic commands ###
