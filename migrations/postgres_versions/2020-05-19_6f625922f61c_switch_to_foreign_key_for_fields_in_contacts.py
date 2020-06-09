"""Switch to foreign keys for fields in Contacts

Revision ID: 6f625922f61c
Revises: 2a91be2822a1
Create Date: 2020-05-19 18:29:49.615957

"""
import geoalchemy2
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

import pepys_import

# revision identifiers, used by Alembic.
revision = "6f625922f61c"
down_revision = "2a91be2822a1"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("Contacts", schema="pepys") as batch_op:
        batch_op.alter_column(
            "classification",
            existing_type=sa.VARCHAR(length=150),
            type_=postgresql.UUID(as_uuid=True),
            existing_nullable=True,
            postgresql_using="classification::uuid",
        )
        batch_op.alter_column(
            "confidence",
            existing_type=sa.VARCHAR(length=150),
            type_=postgresql.UUID(as_uuid=True),
            existing_nullable=True,
            postgresql_using="confidence::uuid",
        )
        batch_op.alter_column(
            "contact_type",
            existing_type=sa.VARCHAR(length=150),
            type_=postgresql.UUID(as_uuid=True),
            existing_nullable=True,
            postgresql_using="contact_type::uuid",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Contacts_contact_type_ContactTypes"),
            "ContactTypes",
            ["contact_type"],
            ["contact_type_id"],
            referent_schema="pepys",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Contacts_classification_ClassificationTypes"),
            "ClassificationTypes",
            ["classification"],
            ["class_type_id"],
            referent_schema="pepys",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Contacts_confidence_ConfidenceLevels"),
            "ConfidenceLevels",
            ["confidence"],
            ["confidence_level_id"],
            referent_schema="pepys",
        )

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("Contacts", schema="pepys") as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_Contacts_confidence_ConfidenceLevels"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("fk_Contacts_classification_ClassificationTypes"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("fk_Contacts_contact_type_ContactTypes"), type_="foreignkey"
        )
        batch_op.alter_column(
            "contact_type",
            existing_type=postgresql.UUID(as_uuid=True),
            type_=sa.VARCHAR(length=150),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "confidence",
            existing_type=postgresql.UUID(as_uuid=True),
            type_=sa.VARCHAR(length=150),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "classification",
            existing_type=postgresql.UUID(as_uuid=True),
            type_=sa.VARCHAR(length=150),
            existing_nullable=True,
        )

    # ### end Alembic commands ###
