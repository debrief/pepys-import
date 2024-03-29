"""
Increase identifier

Revision ID: 80bc8b0d199b
Revises: 1be821cb7908
Create Date: 2021-02-23 09:52:41.589740+00:00

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "80bc8b0d199b"
down_revision = "1be821cb7908"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "Platforms",
        "identifier",
        existing_type=sa.VARCHAR(length=10),
        type_=sa.String(length=30),
        existing_nullable=False,
        schema="pepys",
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "Platforms",
        "identifier",
        existing_type=sa.String(length=30),
        type_=sa.VARCHAR(length=10),
        existing_nullable=False,
        schema="pepys",
    )
    # ### end Alembic commands ###
