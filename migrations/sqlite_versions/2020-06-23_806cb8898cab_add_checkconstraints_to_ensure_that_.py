"""Add CheckConstraints to ensure that empty strings cannot be set as the value for String fields that are used for uniqueness checks

Revision ID: 806cb8898cab
Revises:
Create Date: 2020-06-23 11:38:46.654985

"""
import sqlalchemy as sa
from alembic import op

import pepys_import

# revision identifiers, used by Alembic.
revision = "806cb8898cab"
down_revision = "f2c9f346f305"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("Sensors", schema=None) as batch_op:
        batch_op.create_check_constraint("ck_Sensors_name", condition="name <> ''")

    with op.batch_alter_table("Platforms", schema=None) as batch_op:
        batch_op.create_check_constraint("ck_Platforms_name", condition="name <> ''")
        batch_op.create_check_constraint("ck_Platforms_identifier", condition="identifier <> ''")

    with op.batch_alter_table("Datafiles", schema=None) as batch_op:
        batch_op.create_check_constraint("ck_Datafiles_hash", condition="hash <> ''")


def downgrade():
    with op.batch_alter_table("Sensors", schema=None) as batch_op:
        batch_op.drop_constraint("ck_Sensors_name", type_="check")

    with op.batch_alter_table("Platforms", schema=None) as batch_op:
        batch_op.drop_constraint("ck_Platforms_name", type_="check")
        batch_op.drop_constraint("ck_Platforms_identifier", type_="check")

    with op.batch_alter_table("Datafiles", schema=None) as batch_op:
        batch_op.drop_constraint("ck_Datafiles_hash", type_="check")
