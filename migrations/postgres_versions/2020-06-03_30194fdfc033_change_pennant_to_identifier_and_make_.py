"""Change pennant to identifier and make required

Revision ID: 30194fdfc033
Revises: 91d0713df209
Create Date: 2020-06-03 14:59:57.050296

"""
import geoalchemy2
import sqlalchemy as sa
from alembic import op

import pepys_import

# revision identifiers, used by Alembic.
revision = "30194fdfc033"
down_revision = "91d0713df209"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("Platforms", schema="pepys") as batch_op:
        batch_op.alter_column(column_name="pennant", new_column_name="identifier", nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("Platforms", schema="pepys") as batch_op:
        batch_op.alter_column(column_name="identifier", new_column_name="pennant", nullable=True)

    # ### end Alembic commands ###
