"""Rename new_value to previous_value

Revision ID: e9049ca0338a
Revises: e3a836917a21
Create Date: 2021-03-01 10:08:33.489136+00:00

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e9049ca0338a"
down_revision = "e3a836917a21"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("Logs", schema=None) as batch_op:
        batch_op.add_column(sa.Column("previous_value", sa.String(length=150), nullable=True))
        batch_op.drop_column("new_value")

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("Logs", schema=None) as batch_op:
        batch_op.add_column(sa.Column("new_value", sa.VARCHAR(length=150), nullable=True))
        batch_op.drop_column("previous_value")

    # ### end Alembic commands ###
