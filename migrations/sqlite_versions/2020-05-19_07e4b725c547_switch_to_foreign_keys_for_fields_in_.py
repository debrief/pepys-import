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
from sqlalchemy import REAL, TIMESTAMP, Column, DateTime, ForeignKey, MetaData, String
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import declarative_base, declared_attr, deferred, relationship

import pepys_import
from pepys_import.core.store import constants
from pepys_import.core.store.common_db import (
    ContactMixin,
    ElevationPropertyMixin,
    LocationPropertyMixin,
)
from pepys_import.core.store.db_base import sqlite_naming_convention
from pepys_import.core.store.db_status import TableTypes
from pepys_import.utils.sqlalchemy_utils import UUIDType

# revision identifiers, used by Alembic.
revision = "07e4b725c547"
down_revision = "e752bda39400"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("ClassificationTypes", schema=None) as batch_op:
        batch_op.create_unique_constraint(batch_op.f("uq_ClassificationTypes_name"), ["name"])

    with op.batch_alter_table("ConfidenceLevels", schema=None) as batch_op:
        batch_op.create_unique_constraint(batch_op.f("uq_ConfidenceLevels_name"), ["name"])

    with op.batch_alter_table("ContactTypes", schema=None) as batch_op:
        batch_op.create_unique_constraint(batch_op.f("uq_ContactTypes_name"), ["name"])

    with op.batch_alter_table("Contacts", schema=None) as batch_op:
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
    Metadata = MetaData(naming_convention=sqlite_naming_convention)
    BaseSpatiaLite = declarative_base(metadata=Metadata)

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
            Column(
                "location",
                Geometry(geometry_type="POINT", srid=4326, management=True, spatial_index=False),
            )
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
        subject_id = Column(UUIDType, ForeignKey("Platforms.platform_id", onupdate="cascade"))
        source_id = Column(
            UUIDType, ForeignKey("Datafiles.datafile_id", onupdate="cascade"), nullable=False
        )
        privacy_id = Column(UUIDType, ForeignKey("Privacies.privacy_id", onupdate="cascade"))
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
        "ContactTypes", schema=None, naming_convention=sqlite_naming_convention
    ) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_ContactTypes_name"), type_="unique")

    with op.batch_alter_table(
        "ConfidenceLevels", schema=None, naming_convention=sqlite_naming_convention
    ) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_ConfidenceLevels_name"), type_="unique")

    with op.batch_alter_table(
        "ClassificationTypes", schema=None, naming_convention=sqlite_naming_convention
    ) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_ClassificationTypes_name"), type_="unique")

    # ### end Alembic commands ###
