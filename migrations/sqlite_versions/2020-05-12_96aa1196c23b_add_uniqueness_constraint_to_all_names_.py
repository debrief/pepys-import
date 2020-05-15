"""Add uniqueness constraint to all names in reference tables

Revision ID: 96aa1196c23b
Revises: 7df9dcbd47e7
Create Date: 2020-05-12 10:34:21.151949

"""
import geoalchemy2
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "96aa1196c23b"
down_revision = "7df9dcbd47e7"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("ClassificationTypes", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            batch_op.f("uq_ClassificationTypes_class_type"), ["class_type"]
        )

    with op.batch_alter_table("CommentTypes", schema=None) as batch_op:
        batch_op.create_unique_constraint(batch_op.f("uq_CommentTypes_name"), ["name"])

    with op.batch_alter_table("CommodityTypes", schema=None) as batch_op:
        batch_op.create_unique_constraint(batch_op.f("uq_CommodityTypes_name"), ["name"])

    with op.batch_alter_table("ConfidenceLevels", schema=None) as batch_op:
        batch_op.create_unique_constraint(batch_op.f("uq_ConfidenceLevels_level"), ["level"])

    with op.batch_alter_table("ContactTypes", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            batch_op.f("uq_ContactTypes_contact_type"), ["contact_type"]
        )

    with op.batch_alter_table("DatafileTypes", schema=None) as batch_op:
        batch_op.create_unique_constraint(batch_op.f("uq_DatafileTypes_name"), ["name"])

    with op.batch_alter_table("GeometrySubTypes", schema=None) as batch_op:
        batch_op.create_unique_constraint(batch_op.f("uq_GeometrySubTypes_name"), ["name"])

    with op.batch_alter_table("GeometryTypes", schema=None) as batch_op:
        batch_op.create_unique_constraint(batch_op.f("uq_GeometryTypes_name"), ["name"])

    with op.batch_alter_table("MediaTypes", schema=None) as batch_op:
        batch_op.create_unique_constraint(batch_op.f("uq_MediaTypes_name"), ["name"])

    with op.batch_alter_table("Nationalities", schema=None) as batch_op:
        batch_op.create_unique_constraint(batch_op.f("uq_Nationalities_name"), ["name"])

    with op.batch_alter_table("PlatformTypes", schema=None) as batch_op:
        batch_op.alter_column("name", existing_type=sa.VARCHAR(length=150), nullable=False)
        batch_op.create_unique_constraint(batch_op.f("uq_PlatformTypes_name"), ["name"])

    with op.batch_alter_table("Privacies", schema=None) as batch_op:
        batch_op.create_unique_constraint(batch_op.f("uq_Privacies_name"), ["name"])

    with op.batch_alter_table("SensorTypes", schema=None) as batch_op:
        batch_op.alter_column("name", existing_type=sa.VARCHAR(length=150), nullable=False)
        batch_op.create_unique_constraint(batch_op.f("uq_SensorTypes_name"), ["name"])

    with op.batch_alter_table("UnitTypes", schema=None) as batch_op:
        batch_op.create_unique_constraint(batch_op.f("uq_UnitTypes_name"), ["name"])

    with op.batch_alter_table("Users", schema=None) as batch_op:
        batch_op.create_unique_constraint(batch_op.f("uq_Users_name"), ["name"])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("Users", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_Users_name"), type_="unique")

    with op.batch_alter_table("UnitTypes", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_UnitTypes_name"), type_="unique")

    with op.batch_alter_table("SensorTypes", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_SensorTypes_name"), type_="unique")
        batch_op.alter_column("name", existing_type=sa.VARCHAR(length=150), nullable=True)

    with op.batch_alter_table("Privacies", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_Privacies_name"), type_="unique")

    with op.batch_alter_table("PlatformTypes", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_PlatformTypes_name"), type_="unique")
        batch_op.alter_column("name", existing_type=sa.VARCHAR(length=150), nullable=True)

    with op.batch_alter_table("Nationalities", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_Nationalities_name"), type_="unique")

    with op.batch_alter_table("MediaTypes", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_MediaTypes_name"), type_="unique")

    with op.batch_alter_table("GeometryTypes", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_GeometryTypes_name"), type_="unique")

    with op.batch_alter_table("GeometrySubTypes", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_GeometrySubTypes_name"), type_="unique")

    with op.batch_alter_table("DatafileTypes", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_DatafileTypes_name"), type_="unique")

    with op.batch_alter_table("ContactTypes", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_ContactTypes_contact_type"), type_="unique")

    with op.batch_alter_table("ConfidenceLevels", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_ConfidenceLevels_level"), type_="unique")

    with op.batch_alter_table("CommodityTypes", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_CommodityTypes_name"), type_="unique")

    with op.batch_alter_table("CommentTypes", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_CommentTypes_name"), type_="unique")

    with op.batch_alter_table("ClassificationTypes", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_ClassificationTypes_class_type"), type_="unique")

    # ### end Alembic commands ###
