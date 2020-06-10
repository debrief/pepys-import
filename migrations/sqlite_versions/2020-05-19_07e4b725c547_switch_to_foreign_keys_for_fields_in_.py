"""Switch to foreign keys for fields in Contacts

Revision ID: 07e4b725c547
Revises: e752bda39400
Create Date: 2020-05-19 11:34:17.060199

"""
from datetime import datetime
from uuid import uuid4

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, MetaData, String
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
    ContactMixin,
    DatafileMixin,
    ElevationPropertyMixin,
    LocationPropertyMixin,
    PlatformMixin,
    SensorMixin,
)
from pepys_import.core.store.db_base import sqlite_naming_convention
from pepys_import.core.store.db_status import TableTypes
from pepys_import.utils.sqlalchemy_utils import UUIDType

Metadata = MetaData(naming_convention=sqlite_naming_convention)
BaseSpatiaLite = declarative_base(metadata=Metadata)


class Privacy(BaseSpatiaLite):
    __tablename__ = constants.PRIVACY
    table_type = TableTypes.REFERENCE
    table_type_id = 22

    privacy_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class ConfidenceLevel(BaseSpatiaLite):
    __tablename__ = constants.CONFIDENCE_LEVEL
    table_type = TableTypes.REFERENCE
    table_type_id = 27

    confidence_level_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class SensorType(BaseSpatiaLite):
    __tablename__ = constants.SENSOR_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 21

    sensor_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class ClassificationType(BaseSpatiaLite):
    __tablename__ = constants.CLASSIFICATION_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 19

    class_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class Platform(BaseSpatiaLite, PlatformMixin):
    __tablename__ = constants.PLATFORM
    table_type = TableTypes.METADATA
    table_type_id = 3

    platform_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False)
    pennant = deferred(Column(String(10), nullable=False))
    trigraph = deferred(Column(String(3)))
    quadgraph = deferred(Column(String(4)))
    nationality_id = Column(UUIDType, ForeignKey("Nationalities.nationality_id"), nullable=False)
    platform_type_id = Column(
        UUIDType, ForeignKey("PlatformTypes.platform_type_id"), nullable=False
    )
    privacy_id = Column(UUIDType, ForeignKey("Privacies.privacy_id"), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


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


class ContactType(BaseSpatiaLite):
    __tablename__ = constants.CONTACT_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 20

    contact_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class PlatformType(BaseSpatiaLite):
    __tablename__ = constants.PLATFORM_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 13

    platform_type_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)


class Nationality(BaseSpatiaLite):
    __tablename__ = constants.NATIONALITY
    table_type = TableTypes.REFERENCE
    table_type_id = 14

    nationality_id = Column(UUIDType, primary_key=True, default=uuid4)
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


class DatafileType(BaseSpatiaLite):
    __tablename__ = constants.DATAFILE_TYPE
    table_type = TableTypes.REFERENCE
    table_type_id = 23

    datafile_type_id = Column(UUIDType, primary_key=True, default=uuid4)
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


# revision identifiers, used by Alembic.
revision = "07e4b725c547"
down_revision = "e752bda39400"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table(
        "ClassificationTypes", schema=None, copy_from=ClassificationType.__table__
    ) as batch_op:
        batch_op.create_unique_constraint(batch_op.f("uq_ClassificationTypes_name"), ["name"])

    with op.batch_alter_table(
        "ConfidenceLevels", schema=None, copy_from=ConfidenceLevel.__table__
    ) as batch_op:
        batch_op.create_unique_constraint(batch_op.f("uq_ConfidenceLevels_name"), ["name"])

    with op.batch_alter_table(
        "ContactTypes", schema=None, copy_from=ContactType.__table__
    ) as batch_op:
        batch_op.create_unique_constraint(batch_op.f("uq_ContactTypes_name"), ["name"])

    with op.batch_alter_table("Contacts", schema=None, copy_from=Contact.__table__) as batch_op:
        batch_op.alter_column(
            "classification",
            existing_type=sa.VARCHAR(length=150),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "confidence",
            existing_type=sa.VARCHAR(length=150),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "contact_type",
            existing_type=sa.VARCHAR(length=150),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=True,
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Contacts_classification_ClassificationTypes"),
            "ClassificationTypes",
            ["classification"],
            ["class_type_id"],
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Contacts_contact_type_ContactTypes"),
            "ContactTypes",
            ["contact_type"],
            ["contact_type_id"],
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Contacts_confidence_ConfidenceLevels"),
            "ConfidenceLevels",
            ["confidence"],
            ["confidence_level_id"],
        )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("Contacts", schema=None, copy_from=Contact.__table__) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_Contacts_confidence_ConfidenceLevels"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("fk_Contacts_contact_type_ContactTypes"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("fk_Contacts_classification_ClassificationTypes"), type_="foreignkey"
        )
        batch_op.alter_column(
            "contact_type",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.VARCHAR(length=150),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "confidence",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.VARCHAR(length=150),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "classification",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.VARCHAR(length=150),
            existing_nullable=True,
        )

    with op.batch_alter_table(
        "ContactTypes", schema=None, copy_from=ContactType.__table__
    ) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_ContactTypes_name"), type_="unique")

    with op.batch_alter_table(
        "ConfidenceLevels", schema=None, copy_from=ConfidenceLevel.__table__
    ) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_ConfidenceLevels_name"), type_="unique")

    with op.batch_alter_table(
        "ClassificationTypes", schema=None, copy_from=ClassificationType.__table__
    ) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_ClassificationTypes_name"), type_="unique")

    # ### end Alembic commands ###
