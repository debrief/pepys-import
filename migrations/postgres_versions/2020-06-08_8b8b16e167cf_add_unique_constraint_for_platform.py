"""Add unique constraint for Platform

Revision ID: 8b8b16e167cf
Revises: 2a91be2822a1
Create Date: 2020-05-29 16:40:08.842023

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "8b8b16e167cf"
down_revision = "d96db9a0620f"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("Datafiles", schema="pepys") as batch_op:
        batch_op.create_unique_constraint("uq_Datafile_size_hash", ["size", "hash"])

    with op.batch_alter_table("GeometrySubTypes", schema="pepys") as batch_op:
        batch_op.create_unique_constraint("uq_GeometrySubType_name_parent", ["name", "parent"])

    with op.batch_alter_table("Platforms", schema="pepys") as batch_op:
        batch_op.create_unique_constraint(
            "uq_Platform_name_nat_identifier", ["name", "nationality_id", "identifier"]
        )

    with op.batch_alter_table("Sensors", schema="pepys") as batch_op:
        batch_op.create_unique_constraint("uq_sensors_name_host", ["name", "host"])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("Sensors", schema="pepys") as batch_op:
        batch_op.drop_constraint("uq_sensors_name_host", type_="unique")

    with op.batch_alter_table("Platforms", schema="pepys") as batch_op:
        batch_op.drop_constraint("uq_Platform_name_nat_identifier", type_="unique")

    with op.batch_alter_table("GeometrySubTypes", schema="pepys") as batch_op:
        batch_op.drop_constraint("uq_GeometrySubType_name_parent", type_="unique")

    with op.batch_alter_table("Datafiles", schema="pepys") as batch_op:
        batch_op.drop_constraint("uq_Datafile_size_hash", type_="unique")

    # ### end Alembic commands ###
