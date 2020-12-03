"""Add datafile_id field to Changes table

Revision ID: d154cad9087f
Revises: f548a355e42c
Create Date: 2020-11-18 07:28:33.339471+00:00

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "d154cad9087f"
down_revision = "f548a355e42c"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "Changes",
        sa.Column("datafile_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema="pepys",
    )
    op.create_foreign_key(
        op.f("fk_Changes_datafile_id_Datafiles"),
        "Changes",
        "Datafiles",
        ["datafile_id"],
        ["datafile_id"],
        source_schema="pepys",
        referent_schema="pepys",
        onupdate="cascade",
        ondelete="SET NULL",
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(
        op.f("fk_Changes_datafile_id_Datafiles"), "Changes", schema="pepys", type_="foreignkey"
    )
    op.drop_column("Changes", "datafile_id", schema="pepys")
    # ### end Alembic commands ###