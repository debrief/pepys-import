"""Add unique constraint for Serials

Revision ID: ff4215cb3d30
Revises: f17f01e2f2c5
Create Date: 2021-04-26 15:50:41.368518+00:00

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "ff4215cb3d30"
down_revision = "f17f01e2f2c5"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(
        "uq_Serial_serial_number_wargame_id",
        "Serials",
        ["serial_number", "wargame_id"],
        schema="pepys",
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(
        "uq_Serial_serial_number_wargame_id", "Serials", schema="pepys", type_="unique"
    )
    # ### end Alembic commands ###
