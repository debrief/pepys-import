"""Convert Logs.previous_value to unlimited TEXT data type

Revision ID: 1cdc1050b92f
Revises: 2fbdbf54abaf
Create Date: 2021-04-19 09:00:51.219159+00:00

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "1cdc1050b92f"
down_revision = "2fbdbf54abaf"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("Logs", schema=None) as batch_op:
        batch_op.alter_column(
            "previous_value",
            existing_type=sa.VARCHAR(length=150),
            type_=sa.Text(),
            existing_nullable=True,
        )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("Logs", schema=None) as batch_op:
        batch_op.alter_column(
            "previous_value",
            existing_type=sa.Text(),
            type_=sa.VARCHAR(length=150),
            existing_nullable=True,
        )
    # ### end Alembic commands ###