"""Add datafile_id field to Changes table

Revision ID: 5a909b3cec9d
Revises: b7fc1ab24c92
Create Date: 2020-11-18 07:24:32.188580+00:00

"""
import sqlalchemy as sa
from alembic import op

import pepys_import

# revision identifiers, used by Alembic.
revision = "5a909b3cec9d"
down_revision = "b7fc1ab24c92"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("Changes", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "datafile_id",
                pepys_import.utils.sqlalchemy_utils.UUIDType(length=16),
                nullable=True,
            )
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Changes_datafile_id_Datafiles"),
            "Datafiles",
            ["datafile_id"],
            ["datafile_id"],
            onupdate="cascade",
        )

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("Changes", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_Changes_datafile_id_Datafiles"), type_="foreignkey")
        batch_op.drop_column("datafile_id")

    # ### end Alembic commands ###
