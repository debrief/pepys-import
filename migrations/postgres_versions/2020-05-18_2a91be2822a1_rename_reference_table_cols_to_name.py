"""Rename reference table cols to name

Revision ID: 2a91be2822a1
Revises: e2f70908043d
Create Date: 2020-05-18 12:06:16.764877

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "2a91be2822a1"
down_revision = "e2f70908043d"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("ClassificationTypes", schema="pepys") as batch_op:
        batch_op.alter_column(column_name="class_type", new_column_name="name")
        batch_op.create_unique_constraint(batch_op.f("uq_ClassificationTypes_name"), ["name"])
        batch_op.drop_constraint("uq_ClassificationTypes_class_type", type_="unique")

    with op.batch_alter_table("ConfidenceLevels", schema="pepys") as batch_op:
        batch_op.alter_column(column_name="level", new_column_name="name")
        batch_op.create_unique_constraint(batch_op.f("uq_ConfidenceLevels_name"), ["name"])
        batch_op.drop_constraint("uq_ConfidenceLevels_level", type_="unique")

    with op.batch_alter_table("ContactTypes", schema="pepys") as batch_op:
        batch_op.alter_column(column_name="contact_type", new_column_name="name")
        batch_op.create_unique_constraint(batch_op.f("uq_ContactTypes_name"), ["name"])
        batch_op.drop_constraint("uq_ContactTypes_contact_type", type_="unique")

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("ContactTypes", schema="pepys") as batch_op:
        batch_op.alter_column(column_name="name", new_column_name="contact_type")
        batch_op.create_unique_constraint("uq_ContactTypes_contact_type", ["contact_type"])
        batch_op.drop_constraint(batch_op.f("uq_ContactTypes_name"), type_="unique")

    with op.batch_alter_table("ConfidenceLevels", schema="pepys") as batch_op:
        batch_op.alter_column(column_name="name", new_column_name="level")
        batch_op.create_unique_constraint("uq_ConfidenceLevels_level", ["level"])
        batch_op.drop_constraint(batch_op.f("uq_ConfidenceLevels_name"), type_="unique")

    with op.batch_alter_table("ClassificationTypes", schema="pepys") as batch_op:
        batch_op.alter_column(column_name="name", new_column_name="class_type")
        batch_op.create_unique_constraint("uq_ClassificationTypes_class_type", ["class_type"])
        batch_op.drop_constraint(batch_op.f("uq_ClassificationTypes_name"), type_="unique")

    # ### end Alembic commands ###
