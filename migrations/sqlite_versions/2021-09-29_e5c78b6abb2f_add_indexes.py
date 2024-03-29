"""Add indexes

Revision ID: e5c78b6abb2f
Revises: feb548c7c6c0
Create Date: 2021-09-29 15:41:46.231078+00:00

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "e5c78b6abb2f"
down_revision = "feb548c7c6c0"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("Activations", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_Activations_end"), ["end"], unique=False)
        batch_op.create_index(batch_op.f("ix_Activations_start"), ["start"], unique=False)

    with op.batch_alter_table("Comments", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_Comments_time"), ["time"], unique=False)

    with op.batch_alter_table("Contacts", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_Contacts_time"), ["time"], unique=False)

    with op.batch_alter_table("Geometries", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_Geometries_end"), ["end"], unique=False)
        batch_op.create_index(batch_op.f("ix_Geometries_start"), ["start"], unique=False)

    with op.batch_alter_table("Media", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_Media_time"), ["time"], unique=False)

    with op.batch_alter_table("States", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_States_time"), ["time"], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("States", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_States_time"))

    with op.batch_alter_table("Media", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_Media_time"))

    with op.batch_alter_table("Geometries", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_Geometries_start"))
        batch_op.drop_index(batch_op.f("ix_Geometries_end"))

    with op.batch_alter_table("Contacts", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_Contacts_time"))

    with op.batch_alter_table("Comments", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_Comments_time"))

    with op.batch_alter_table("Activations", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_Activations_start"))
        batch_op.drop_index(batch_op.f("ix_Activations_end"))

    # ### end Alembic commands ###
