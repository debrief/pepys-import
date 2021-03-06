"""base

Revision ID: bcff0ccb4fbd
Revises:
Create Date: 2020-04-23 12:25:08.210628

"""
import geoalchemy2
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "bcff0ccb4fbd"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "Activations",
        sa.Column("activation_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("sensor_id", sa.Integer(), nullable=False),
        sa.Column("start", sa.TIMESTAMP(), nullable=False),
        sa.Column("end", sa.TIMESTAMP(), nullable=False),
        sa.Column("min_range", sa.REAL(), nullable=True),
        sa.Column("max_range", sa.REAL(), nullable=True),
        sa.Column("left_arc", sa.REAL(), nullable=True),
        sa.Column("right_arc", sa.REAL(), nullable=True),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("privacy_id", sa.Integer(), nullable=True),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("activation_id"),
    )
    op.create_table(
        "Changes",
        sa.Column("change_id", sa.Integer(), nullable=False),
        sa.Column("user", sa.String(length=150), nullable=False),
        sa.Column("modified", sa.DATE(), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("change_id"),
    )
    op.create_table(
        "ClassificationTypes",
        sa.Column("class_type_id", sa.Integer(), nullable=False),
        sa.Column("class_type", sa.String(length=150), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("class_type_id"),
    )
    op.create_table(
        "CommentTypes",
        sa.Column("comment_type_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("comment_type_id"),
    )
    op.create_table(
        "Comments",
        sa.Column("comment_id", sa.Integer(), nullable=False),
        sa.Column("platform_id", sa.Integer(), nullable=True),
        sa.Column("time", sa.TIMESTAMP(), nullable=False),
        sa.Column("comment_type_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.String(length=150), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("privacy_id", sa.Integer(), nullable=True),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("comment_id"),
    )
    op.create_table(
        "CommodityTypes",
        sa.Column("commodity_type_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("commodity_type_id"),
    )
    op.create_table(
        "ConfidenceLevels",
        sa.Column("confidence_level_id", sa.Integer(), nullable=False),
        sa.Column("level", sa.String(length=150), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("confidence_level_id"),
    )
    op.create_table(
        "ContactTypes",
        sa.Column("contact_type_id", sa.Integer(), nullable=False),
        sa.Column("contact_type", sa.String(length=150), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("contact_type_id"),
    )
    op.create_table(
        "Contacts",
        sa.Column("contact_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=True),
        sa.Column("sensor_id", sa.Integer(), nullable=False),
        sa.Column("time", sa.TIMESTAMP(), nullable=False),
        sa.Column("bearing", sa.REAL(), nullable=True),
        sa.Column("rel_bearing", sa.REAL(), nullable=True),
        sa.Column("ambig_bearing", sa.REAL(), nullable=True),
        sa.Column("freq", sa.REAL(), nullable=True),
        sa.Column("range", sa.REAL(), nullable=True),
        sa.Column(
            "location",
            geoalchemy2.types.Geometry(geometry_type="POINT", srid=4326, management=True),
            nullable=True,
        ),
        sa.Column("elevation", sa.REAL(), nullable=True),
        sa.Column("major", sa.REAL(), nullable=True),
        sa.Column("minor", sa.REAL(), nullable=True),
        sa.Column("orientation", sa.REAL(), nullable=True),
        sa.Column("classification", sa.String(length=150), nullable=True),
        sa.Column("confidence", sa.String(length=150), nullable=True),
        sa.Column("contact_type", sa.String(length=150), nullable=True),
        sa.Column("mla", sa.REAL(), nullable=True),
        sa.Column("soa", sa.REAL(), nullable=True),
        sa.Column("subject_id", sa.Integer(), nullable=True),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("privacy_id", sa.Integer(), nullable=True),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("contact_id"),
    )
    op.create_table(
        "DatafileTypes",
        sa.Column("datafile_type_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("datafile_type_id"),
    )
    op.create_table(
        "Datafiles",
        sa.Column("datafile_id", sa.Integer(), nullable=False),
        sa.Column("simulated", sa.Boolean(), nullable=False),
        sa.Column("privacy_id", sa.Integer(), nullable=False),
        sa.Column("datafile_type_id", sa.Integer(), nullable=False),
        sa.Column("reference", sa.String(length=150), nullable=True),
        sa.Column("url", sa.String(length=150), nullable=True),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("hash", sa.String(length=32), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("datafile_id"),
    )
    op.create_table(
        "Extractions",
        sa.Column("extraction_id", sa.Integer(), nullable=False),
        sa.Column("table", sa.String(length=150), nullable=False),
        sa.Column("field", sa.String(length=150), nullable=False),
        sa.Column("chars", sa.String(length=150), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("extraction_id"),
    )
    op.create_table(
        "Geometries",
        sa.Column("geometry_id", sa.Integer(), nullable=False),
        sa.Column("geometry", geoalchemy2.types.Geometry(management=True), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("geo_type_id", sa.Integer(), nullable=False),
        sa.Column("geo_sub_type_id", sa.Integer(), nullable=False),
        sa.Column("start", sa.TIMESTAMP(), nullable=True),
        sa.Column("end", sa.TIMESTAMP(), nullable=True),
        sa.Column("task_id", sa.Integer(), nullable=True),
        sa.Column("subject_platform_id", sa.Integer(), nullable=True),
        sa.Column("sensor_platform_id", sa.Integer(), nullable=True),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("privacy_id", sa.Integer(), nullable=True),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("geometry_id"),
    )
    op.create_table(
        "GeometrySubTypes",
        sa.Column("geo_sub_type_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("parent", sa.Integer(), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("geo_sub_type_id"),
    )
    op.create_table(
        "GeometryTypes",
        sa.Column("geo_type_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("geo_type_id"),
    )
    op.create_table(
        "HostedBy",
        sa.Column("hosted_by_id", sa.Integer(), nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("host_id", sa.Integer(), nullable=False),
        sa.Column("hosted_from", sa.DATE(), nullable=False),
        sa.Column("host_to", sa.DATE(), nullable=False),
        sa.Column("privacy_id", sa.Integer(), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("hosted_by_id"),
    )
    op.create_table(
        "Logs",
        sa.Column("log_id", sa.Integer(), nullable=False),
        sa.Column("table", sa.String(length=150), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("field", sa.String(length=150), nullable=True),
        sa.Column("new_value", sa.String(length=150), nullable=True),
        sa.Column("change_id", sa.Integer(), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("log_id"),
    )
    op.create_table(
        "LogsHoldings",
        sa.Column("logs_holding_id", sa.Integer(), nullable=False),
        sa.Column("time", sa.TIMESTAMP(), nullable=False),
        sa.Column("commodity_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.REAL(), nullable=False),
        sa.Column("unit_type_id", sa.Integer(), nullable=False),
        sa.Column("platform_id", sa.Integer(), nullable=False),
        sa.Column("comment", sa.String(length=150), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("privacy_id", sa.Integer(), nullable=True),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("logs_holding_id"),
    )
    op.create_table(
        "Media",
        sa.Column("media_id", sa.Integer(), nullable=False),
        sa.Column("platform_id", sa.Integer(), nullable=True),
        sa.Column("subject_id", sa.Integer(), nullable=True),
        sa.Column("sensor_id", sa.Integer(), nullable=True),
        sa.Column(
            "location",
            geoalchemy2.types.Geometry(geometry_type="POINT", srid=4326, management=True),
            nullable=True,
        ),
        sa.Column("elevation", sa.REAL(), nullable=True),
        sa.Column("time", sa.TIMESTAMP(), nullable=True),
        sa.Column("media_type_id", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(length=150), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("privacy_id", sa.Integer(), nullable=True),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("media_id"),
    )
    op.create_table(
        "MediaTypes",
        sa.Column("media_type_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("media_type_id"),
    )
    op.create_table(
        "Nationalities",
        sa.Column("nationality_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("nationality_id"),
    )
    op.create_table(
        "Participants",
        sa.Column("participant_id", sa.Integer(), nullable=False),
        sa.Column("platform_id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("start", sa.TIMESTAMP(), nullable=True),
        sa.Column("end", sa.TIMESTAMP(), nullable=True),
        sa.Column("force", sa.String(length=150), nullable=True),
        sa.Column("privacy_id", sa.Integer(), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("participant_id"),
    )
    op.create_table(
        "PlatformTypes",
        sa.Column("platform_type_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=True),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("platform_type_id"),
    )
    op.create_table(
        "Platforms",
        sa.Column("platform_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("pennant", sa.String(length=10), nullable=True),
        sa.Column("trigraph", sa.String(length=3), nullable=True),
        sa.Column("quadgraph", sa.String(length=4), nullable=True),
        sa.Column("nationality_id", sa.Integer(), nullable=False),
        sa.Column("platform_type_id", sa.Integer(), nullable=False),
        sa.Column("privacy_id", sa.Integer(), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("platform_id"),
    )
    op.create_table(
        "Privacies",
        sa.Column("privacy_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("privacy_id"),
    )
    op.create_table(
        "SensorTypes",
        sa.Column("sensor_type_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=True),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("sensor_type_id"),
    )
    op.create_table(
        "Sensors",
        sa.Column("sensor_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("sensor_type_id", sa.Integer(), nullable=False),
        sa.Column("host", sa.Integer(), nullable=False),
        sa.Column("privacy_id", sa.Integer(), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("sensor_id"),
    )
    op.create_table(
        "States",
        sa.Column("state_id", sa.Integer(), nullable=False),
        sa.Column("time", sa.TIMESTAMP(), nullable=False),
        sa.Column("sensor_id", sa.Integer(), nullable=False),
        sa.Column(
            "location",
            geoalchemy2.types.Geometry(geometry_type="POINT", srid=4326, management=True),
            nullable=True,
        ),
        sa.Column("elevation", sa.REAL(), nullable=True),
        sa.Column("heading", sa.REAL(), nullable=True),
        sa.Column("course", sa.REAL(), nullable=True),
        sa.Column("speed", sa.REAL(), nullable=True),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("privacy_id", sa.Integer(), nullable=True),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("state_id"),
    )
    op.create_table(
        "Synonyms",
        sa.Column("synonym_id", sa.Integer(), nullable=False),
        sa.Column("table", sa.String(length=150), nullable=False),
        sa.Column("entity", sa.Integer(), nullable=False),
        sa.Column("synonym", sa.String(length=150), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("synonym_id"),
    )
    op.create_table(
        "TaggedItems",
        sa.Column("tagged_item_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("tagged_by_id", sa.Integer(), nullable=False),
        sa.Column("private", sa.Boolean(), nullable=False),
        sa.Column("tagged_on", sa.DATE(), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("tagged_item_id"),
    )
    op.create_table(
        "Tags",
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("tag_id"),
    )
    op.create_table(
        "Tasks",
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=False),
        sa.Column("start", sa.TIMESTAMP(), nullable=False),
        sa.Column("end", sa.TIMESTAMP(), nullable=False),
        sa.Column("environment", sa.String(length=150), nullable=True),
        sa.Column("location", sa.String(length=150), nullable=True),
        sa.Column("privacy_id", sa.Integer(), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("task_id"),
    )
    op.create_table(
        "UnitTypes",
        sa.Column("unit_type_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("unit_type_id"),
    )
    op.create_table(
        "Users",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("user_id"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("Users")
    op.drop_table("UnitTypes")
    op.drop_table("Tasks")
    op.drop_table("Tags")
    op.drop_table("TaggedItems")
    op.drop_table("Synonyms")
    op.drop_table("States")
    op.drop_table("Sensors")
    op.drop_table("SensorTypes")
    op.drop_table("Privacies")
    op.drop_table("Platforms")
    op.drop_table("PlatformTypes")
    op.drop_table("Participants")
    op.drop_table("Nationalities")
    op.drop_table("MediaTypes")
    op.drop_table("Media")
    op.drop_table("LogsHoldings")
    op.drop_table("Logs")
    op.drop_table("HostedBy")
    op.drop_table("GeometryTypes")
    op.drop_table("GeometrySubTypes")
    op.drop_table("Geometries")
    op.drop_table("Extractions")
    op.drop_table("Datafiles")
    op.drop_table("DatafileTypes")
    op.drop_table("Contacts")
    op.drop_table("ContactTypes")
    op.drop_table("ConfidenceLevels")
    op.drop_table("CommodityTypes")
    op.drop_table("Comments")
    op.drop_table("CommentTypes")
    op.drop_table("ClassificationTypes")
    op.drop_table("Changes")
    op.drop_table("Activations")
    # ### end Alembic commands ###
