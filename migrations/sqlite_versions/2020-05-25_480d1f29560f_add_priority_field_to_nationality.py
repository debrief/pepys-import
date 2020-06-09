"""Add priority field to Nationality

Revision ID: 480d1f29560f
Revises: 07e4b725c547
Create Date: 2020-05-25 13:17:26.182876

"""
from datetime import datetime
from uuid import uuid4

import geoalchemy2
import sqlalchemy as sa
from alembic import op
from sqlalchemy import Column, DateTime, Integer, MetaData, String
from sqlalchemy.ext.declarative import declarative_base

import pepys_import
from pepys_import.core.store import constants
from pepys_import.core.store.db_base import sqlite_naming_convention
from pepys_import.core.store.db_status import TableTypes
from pepys_import.utils.sqlalchemy_utils import UUIDType

Metadata = MetaData(naming_convention=sqlite_naming_convention)
BaseSpatiaLite = declarative_base(metadata=Metadata)


class Nationality(BaseSpatiaLite):
    __tablename__ = constants.NATIONALITY
    table_type = TableTypes.REFERENCE
    table_type_id = 14

    nationality_id = Column(UUIDType, primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False, unique=True)
    priority = Column(Integer)
    created_date = Column(DateTime, default=datetime.utcnow)


# revision identifiers, used by Alembic.
revision = "480d1f29560f"
down_revision = "cd4a4f059f9e"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table(
        "Nationalities", schema=None, copy_from=Nationality.__table__
    ) as batch_op:
        batch_op.add_column(sa.Column("priority", sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table(
        "Nationalities", schema=None, copy_from=Nationality.__table__
    ) as batch_op:
        batch_op.drop_column("priority")
    # ### end Alembic commands ###
