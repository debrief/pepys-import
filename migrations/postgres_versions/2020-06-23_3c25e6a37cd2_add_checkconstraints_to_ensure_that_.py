"""Add CheckConstraints to ensure that empty strings cannot be set as the value for String fields that are used for uniqueness checks

Revision ID: 3c25e6a37cd2
Revises: 351e30ff45e6
Create Date: 2020-06-23 11:40:13.134003

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "3c25e6a37cd2"
down_revision = "351e30ff45e6"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("Sensors", schema="pepys") as batch_op:
        batch_op.create_check_constraint("ck_Sensors_name", condition="name <> ''")

    with op.batch_alter_table("Platforms", schema="pepys") as batch_op:
        batch_op.create_check_constraint("ck_Platforms_name", condition="name <> ''")
        batch_op.create_check_constraint("ck_Platforms_identifier", condition="identifier <> ''")

    with op.batch_alter_table("Datafiles", schema="pepys") as batch_op:
        batch_op.create_check_constraint("ck_Datafiles_hash", condition="hash <> ''")


def downgrade():
    with op.batch_alter_table("Sensors", schema="pepys") as batch_op:
        batch_op.drop_constraint("ck_Sensors_name", type_="check")

    with op.batch_alter_table("Platforms", schema="pepys") as batch_op:
        batch_op.drop_constraint("ck_Platforms_name", type_="check")
        batch_op.drop_constraint("ck_Platforms_identifier", type_="check")

    with op.batch_alter_table("Datafiles", schema="pepys") as batch_op:
        batch_op.drop_constraint("ck_Datafiles_hash", type_="check")
