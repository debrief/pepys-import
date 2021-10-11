"""Alter Extractions table

Revision ID: feb548c7c6c0
Revises: a7f75ead6204
Create Date: 2021-09-20 12:38:20.179908+00:00

"""
import sqlalchemy as sa
from alembic import op

import pepys_import

# revision identifiers, used by Alembic.
revision = "feb548c7c6c0"
down_revision = "a7f75ead6204"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("Extractions", schema=None) as batch_op:
        batch_op.add_column(sa.Column("destination_table", sa.String(length=150), nullable=True))
        batch_op.add_column(
            sa.Column(
                "entry_id", pepys_import.utils.sqlalchemy_utils.UUIDType(length=16), nullable=True
            )
        )
        batch_op.add_column(
            sa.Column(
                "datafile_id",
                pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
                nullable=False,
            )
        )
        batch_op.add_column(sa.Column("text", sa.Text(), nullable=False))
        batch_op.add_column(sa.Column("text_location", sa.String(length=200), nullable=False))
        batch_op.add_column(sa.Column("importer", sa.String(length=150), nullable=False))
        batch_op.add_column(sa.Column("interpreted_value", sa.Text(), nullable=False))
        batch_op.create_foreign_key(
            batch_op.f("fk_Extractions_datafile_id_Datafiles"),
            "Datafiles",
            ["datafile_id"],
            ["datafile_id"],
            onupdate="cascade",
            ondelete="cascade",
        )
        batch_op.drop_column("table")
        batch_op.drop_column("chars")

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("Extractions", schema=None) as batch_op:
        batch_op.add_column(sa.Column("chars", sa.VARCHAR(length=150), nullable=False))
        batch_op.add_column(sa.Column("table", sa.VARCHAR(length=150), nullable=False))
        batch_op.drop_constraint(
            batch_op.f("fk_Extractions_datafile_id_Datafiles"), type_="foreignkey"
        )
        batch_op.drop_column("interpreted_value")
        batch_op.drop_column("importer")
        batch_op.drop_column("text_location")
        batch_op.drop_column("text")
        batch_op.drop_column("datafile_id")
        batch_op.drop_column("entry_id")
        batch_op.drop_column("destination_table")

    # ### end Alembic commands ###