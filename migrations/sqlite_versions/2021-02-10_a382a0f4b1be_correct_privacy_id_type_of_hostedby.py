"""Correct privacy_id type of HostedBy

Revision ID: a382a0f4b1be
Revises: cb9a5f93f0aa
Create Date: 2021-02-10 16:20:41.425779+00:00

"""
import sqlalchemy as sa
from alembic import op

import pepys_import

# revision identifiers, used by Alembic.
revision = "a382a0f4b1be"
down_revision = "cb9a5f93f0aa"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("HostedBy", schema=None) as batch_op:
        batch_op.alter_column(
            "privacy_id",
            existing_type=sa.INTEGER(),
            type_=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            existing_nullable=False,
        )


def downgrade():
    with op.batch_alter_table("HostedBy", schema=None) as batch_op:
        batch_op.alter_column(
            "privacy_id",
            existing_type=pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
            type_=sa.INTEGER(),
            existing_nullable=False,
        )
