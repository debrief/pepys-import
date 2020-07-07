"""update, add constraints

Revision ID: e2f70908043d
Revises: ce68ca5be4cd
Create Date: 2020-05-15 13:56:52.009533

"""
import geoalchemy2
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "e2f70908043d"
down_revision = "ce68ca5be4cd"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("Comments", schema="pepys") as batch_op:
        batch_op.alter_column("platform_id", existing_type=postgresql.UUID(), nullable=True)
        batch_op.create_foreign_key(
            batch_op.f("fk_Comments_comment_type_id_CommentTypes"),
            "CommentTypes",
            ["comment_type_id"],
            ["comment_type_id"],
            referent_schema="pepys",
        )

    with op.batch_alter_table("Datafiles", schema="pepys") as batch_op:
        batch_op.alter_column("simulated", existing_type=sa.BOOLEAN(), nullable=False)

    with op.batch_alter_table("Geometries", schema="pepys") as batch_op:
        batch_op.create_foreign_key(
            batch_op.f("fk_Geometries_task_id_Tasks"),
            "Tasks",
            ["task_id"],
            ["task_id"],
            referent_schema="pepys",
        )

    with op.batch_alter_table("LogsHoldings", schema="pepys") as batch_op:
        batch_op.add_column(
            sa.Column("commodity_id", postgresql.UUID(as_uuid=True), nullable=False)
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_LogsHoldings_commodity_id_CommodityTypes"),
            "CommodityTypes",
            ["commodity_id"],
            ["commodity_type_id"],
            referent_schema="pepys",
        )

    with op.batch_alter_table("Media", schema="pepys") as batch_op:
        batch_op.create_foreign_key(
            batch_op.f("fk_Media_media_type_id_MediaTypes"),
            "MediaTypes",
            ["media_type_id"],
            ["media_type_id"],
            referent_schema="pepys",
        )

    with op.batch_alter_table("Tasks", schema="pepys") as batch_op:
        batch_op.add_column(sa.Column("name", sa.String(length=150), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("Tasks", schema="pepys") as batch_op:
        batch_op.drop_column("name")

    with op.batch_alter_table("Media", schema="pepys") as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_Media_media_type_id_MediaTypes"), type_="foreignkey"
        )

    with op.batch_alter_table("LogsHoldings", schema="pepys") as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_LogsHoldings_commodity_id_CommodityTypes"), type_="foreignkey"
        )
        batch_op.drop_column("commodity_id")

    with op.batch_alter_table("Geometries", schema="pepys") as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_Geometries_task_id_Tasks"), type_="foreignkey")

    with op.batch_alter_table("Datafiles", schema="pepys") as batch_op:
        batch_op.alter_column("simulated", existing_type=sa.BOOLEAN(), nullable=True)

    with op.batch_alter_table("Comments", schema="pepys") as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_Comments_comment_type_id_CommentTypes"), type_="foreignkey"
        )
        batch_op.alter_column("platform_id", existing_type=postgresql.UUID(), nullable=False)

    # ### end Alembic commands ###
