"""base

Revision ID: 5154f7db278d
Revises:
Create Date: 2020-04-23 12:23:01.219218

"""
import geoalchemy2
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "5154f7db278d"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "Changes",
        sa.Column("change_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user", sa.String(length=150), nullable=False),
        sa.Column("modified", sa.DATE(), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("change_id"),
        schema="pepys",
    )
    op.create_table(
        "ClassificationTypes",
        sa.Column("class_type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("class_type", sa.String(length=150), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("class_type_id"),
        schema="pepys",
    )
    op.create_table(
        "CommentTypes",
        sa.Column("comment_type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("comment_type_id"),
        schema="pepys",
    )
    op.create_table(
        "CommodityTypes",
        sa.Column("commodity_type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("commodity_type_id"),
        schema="pepys",
    )
    op.create_table(
        "ConfidenceLevels",
        sa.Column("confidence_level_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("level", sa.String(length=150), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("confidence_level_id"),
        schema="pepys",
    )
    op.create_table(
        "ContactTypes",
        sa.Column("contact_type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("contact_type", sa.String(length=150), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("contact_type_id"),
        schema="pepys",
    )
    op.create_table(
        "DatafileTypes",
        sa.Column("datafile_type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("datafile_type_id"),
        schema="pepys",
    )
    op.create_table(
        "Extractions",
        sa.Column("extraction_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("table", sa.String(length=150), nullable=False),
        sa.Column("field", sa.String(length=150), nullable=False),
        sa.Column("chars", sa.String(length=150), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("extraction_id"),
        schema="pepys",
    )
    op.create_table(
        "GeometrySubTypes",
        sa.Column("geo_sub_type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("parent", postgresql.UUID(), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("geo_sub_type_id"),
        schema="pepys",
    )
    op.create_table(
        "GeometryTypes",
        sa.Column("geo_type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("geo_type_id"),
        schema="pepys",
    )
    op.create_table(
        "MediaTypes",
        sa.Column("media_type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("media_type_id"),
        schema="pepys",
    )
    op.create_table(
        "Nationalities",
        sa.Column("nationality_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("nationality_id"),
        schema="pepys",
    )
    op.create_table(
        "PlatformTypes",
        sa.Column("platform_type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("platform_type_id"),
        schema="pepys",
    )
    op.create_table(
        "Privacies",
        sa.Column("privacy_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("privacy_id"),
        schema="pepys",
    )
    op.create_table(
        "SensorTypes",
        sa.Column("sensor_type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("sensor_type_id"),
        schema="pepys",
    )
    op.create_table(
        "Synonyms",
        sa.Column("synonym_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("table", sa.String(length=150), nullable=False),
        sa.Column("entity", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("synonym", sa.String(length=150), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("synonym_id"),
        schema="pepys",
    )
    op.create_table(
        "Tags",
        sa.Column("tag_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("tag_id"),
        schema="pepys",
    )
    op.create_table(
        "UnitTypes",
        sa.Column("unit_type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("units", sa.String(length=150), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("unit_type_id"),
        schema="pepys",
    )
    op.create_table(
        "Users",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("user_id"),
        schema="pepys",
    )
    op.create_table(
        "Datafiles",
        sa.Column("datafile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("simulated", sa.Boolean(), nullable=True),
        sa.Column("privacy_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("datafile_type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reference", sa.String(length=150), nullable=True),
        sa.Column("url", sa.String(length=150), nullable=True),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("hash", sa.String(length=32), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["datafile_type_id"],
            ["pepys.DatafileTypes.datafile_type_id"],
        ),
        sa.ForeignKeyConstraint(
            ["privacy_id"],
            ["pepys.Privacies.privacy_id"],
        ),
        sa.PrimaryKeyConstraint("datafile_id"),
        schema="pepys",
    )
    op.create_table(
        "Logs",
        sa.Column("log_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("table", sa.String(length=150), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("field", sa.String(length=150), nullable=True),
        sa.Column("new_value", sa.String(length=150), nullable=True),
        sa.Column("change_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["change_id"],
            ["pepys.Changes.change_id"],
        ),
        sa.PrimaryKeyConstraint("log_id"),
        schema="pepys",
    )
    op.create_table(
        "Platforms",
        sa.Column("platform_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("pennant", sa.String(length=10), nullable=True),
        sa.Column("trigraph", sa.String(length=3), nullable=True),
        sa.Column("quadgraph", sa.String(length=4), nullable=True),
        sa.Column("nationality_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("platform_type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("privacy_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["nationality_id"],
            ["pepys.Nationalities.nationality_id"],
        ),
        sa.ForeignKeyConstraint(
            ["platform_type_id"],
            ["pepys.PlatformTypes.platform_type_id"],
        ),
        sa.ForeignKeyConstraint(
            ["privacy_id"],
            ["pepys.Privacies.privacy_id"],
        ),
        sa.PrimaryKeyConstraint("platform_id"),
        schema="pepys",
    )
    op.create_table(
        "TaggedItems",
        sa.Column("tagged_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tag_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tagged_by_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("private", sa.Boolean(), nullable=False),
        sa.Column("tagged_on", sa.DATE(), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["tag_id"],
            ["pepys.Tags.tag_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tagged_by_id"],
            ["pepys.Users.user_id"],
        ),
        sa.PrimaryKeyConstraint("tagged_item_id"),
        schema="pepys",
    )
    op.create_table(
        "Tasks",
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("start", postgresql.TIMESTAMP(), nullable=False),
        sa.Column("end", postgresql.TIMESTAMP(), nullable=False),
        sa.Column("environment", sa.String(length=150), nullable=True),
        sa.Column("location", sa.String(length=150), nullable=True),
        sa.Column("privacy_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["pepys.Tasks.task_id"],
        ),
        sa.ForeignKeyConstraint(
            ["privacy_id"],
            ["pepys.Privacies.privacy_id"],
        ),
        sa.PrimaryKeyConstraint("task_id"),
        schema="pepys",
    )
    op.create_table(
        "Comments",
        sa.Column("comment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("platform_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("time", postgresql.TIMESTAMP(), nullable=False),
        sa.Column("comment_type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content", sa.String(length=150), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("privacy_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["platform_id"],
            ["pepys.Platforms.platform_id"],
        ),
        sa.ForeignKeyConstraint(
            ["privacy_id"],
            ["pepys.Privacies.privacy_id"],
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["pepys.Datafiles.datafile_id"],
        ),
        sa.PrimaryKeyConstraint("comment_id"),
        schema="pepys",
    )
    op.create_table(
        "Geometries",
        sa.Column("geometry_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("geometry", geoalchemy2.types.Geometry(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("geo_type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("geo_sub_type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("start", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("end", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("subject_platform_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("sensor_platform_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("privacy_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["geo_sub_type_id"],
            ["pepys.GeometrySubTypes.geo_sub_type_id"],
        ),
        sa.ForeignKeyConstraint(
            ["geo_type_id"],
            ["pepys.GeometryTypes.geo_type_id"],
        ),
        sa.ForeignKeyConstraint(
            ["privacy_id"],
            ["pepys.Privacies.privacy_id"],
        ),
        sa.ForeignKeyConstraint(
            ["sensor_platform_id"],
            ["pepys.Platforms.platform_id"],
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["pepys.Datafiles.datafile_id"],
        ),
        sa.ForeignKeyConstraint(
            ["subject_platform_id"],
            ["pepys.Platforms.platform_id"],
        ),
        sa.PrimaryKeyConstraint("geometry_id"),
        schema="pepys",
    )
    op.create_table(
        "HostedBy",
        sa.Column("hosted_by_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("host_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("hosted_from", sa.DATE(), nullable=False),
        sa.Column("host_to", sa.DATE(), nullable=False),
        sa.Column("privacy_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["host_id"],
            ["pepys.Platforms.platform_id"],
        ),
        sa.ForeignKeyConstraint(
            ["privacy_id"],
            ["pepys.Privacies.privacy_id"],
        ),
        sa.ForeignKeyConstraint(
            ["subject_id"],
            ["pepys.Platforms.platform_id"],
        ),
        sa.PrimaryKeyConstraint("hosted_by_id"),
        schema="pepys",
    )
    op.create_table(
        "LogsHoldings",
        sa.Column("logs_holding_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("time", postgresql.TIMESTAMP(), nullable=False),
        sa.Column("quantity", postgresql.DOUBLE_PRECISION(), nullable=False),
        sa.Column("unit_type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("platform_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("comment", sa.String(length=150), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("privacy_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["platform_id"],
            ["pepys.Platforms.platform_id"],
        ),
        sa.ForeignKeyConstraint(
            ["privacy_id"],
            ["pepys.Privacies.privacy_id"],
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["pepys.Datafiles.datafile_id"],
        ),
        sa.ForeignKeyConstraint(
            ["unit_type_id"],
            ["pepys.UnitTypes.unit_type_id"],
        ),
        sa.PrimaryKeyConstraint("logs_holding_id"),
        schema="pepys",
    )
    op.create_table(
        "Participants",
        sa.Column("participant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("platform_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("start", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("end", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("force", sa.String(length=150), nullable=True),
        sa.Column("privacy_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["platform_id"],
            ["pepys.Platforms.platform_id"],
        ),
        sa.ForeignKeyConstraint(
            ["privacy_id"],
            ["pepys.Privacies.privacy_id"],
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["pepys.Tasks.task_id"],
        ),
        sa.PrimaryKeyConstraint("participant_id"),
        schema="pepys",
    )
    op.create_table(
        "Sensors",
        sa.Column("sensor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("sensor_type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("host", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("privacy_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["host"],
            ["pepys.Platforms.platform_id"],
        ),
        sa.ForeignKeyConstraint(
            ["privacy_id"],
            ["pepys.Privacies.privacy_id"],
        ),
        sa.ForeignKeyConstraint(
            ["sensor_type_id"],
            ["pepys.SensorTypes.sensor_type_id"],
        ),
        sa.PrimaryKeyConstraint("sensor_id"),
        schema="pepys",
    )
    op.create_table(
        "Activations",
        sa.Column("activation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("sensor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("start", postgresql.TIMESTAMP(), nullable=False),
        sa.Column("end", postgresql.TIMESTAMP(), nullable=False),
        sa.Column("min_range", postgresql.DOUBLE_PRECISION(), nullable=True),
        sa.Column("max_range", postgresql.DOUBLE_PRECISION(), nullable=True),
        sa.Column("left_arc", postgresql.DOUBLE_PRECISION(), nullable=True),
        sa.Column("right_arc", postgresql.DOUBLE_PRECISION(), nullable=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("privacy_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["privacy_id"],
            ["pepys.Privacies.privacy_id"],
        ),
        sa.ForeignKeyConstraint(
            ["sensor_id"],
            ["pepys.Sensors.sensor_id"],
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["pepys.Datafiles.datafile_id"],
        ),
        sa.PrimaryKeyConstraint("activation_id"),
        schema="pepys",
    )
    op.create_table(
        "Contacts",
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=True),
        sa.Column("sensor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("time", postgresql.TIMESTAMP(), nullable=False),
        sa.Column("bearing", postgresql.DOUBLE_PRECISION(), nullable=True),
        sa.Column("rel_bearing", postgresql.DOUBLE_PRECISION(), nullable=True),
        sa.Column("ambig_bearing", postgresql.DOUBLE_PRECISION(), nullable=True),
        sa.Column("freq", postgresql.DOUBLE_PRECISION(), nullable=True),
        sa.Column("range", postgresql.DOUBLE_PRECISION(), nullable=True),
        sa.Column(
            "location", geoalchemy2.types.Geometry(geometry_type="POINT", srid=4326), nullable=True
        ),
        sa.Column("elevation", postgresql.DOUBLE_PRECISION(), nullable=True),
        sa.Column("major", postgresql.DOUBLE_PRECISION(), nullable=True),
        sa.Column("minor", postgresql.DOUBLE_PRECISION(), nullable=True),
        sa.Column("orientation", postgresql.DOUBLE_PRECISION(), nullable=True),
        sa.Column("classification", sa.String(length=150), nullable=True),
        sa.Column("confidence", sa.String(length=150), nullable=True),
        sa.Column("contact_type", sa.String(length=150), nullable=True),
        sa.Column("mla", postgresql.DOUBLE_PRECISION(), nullable=True),
        sa.Column("soa", postgresql.DOUBLE_PRECISION(), nullable=True),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("privacy_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["privacy_id"],
            ["pepys.Privacies.privacy_id"],
        ),
        sa.ForeignKeyConstraint(
            ["sensor_id"],
            ["pepys.Sensors.sensor_id"],
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["pepys.Datafiles.datafile_id"],
        ),
        sa.ForeignKeyConstraint(
            ["subject_id"],
            ["pepys.Platforms.platform_id"],
        ),
        sa.PrimaryKeyConstraint("contact_id"),
        schema="pepys",
    )
    op.create_table(
        "Media",
        sa.Column("media_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("platform_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("sensor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "location", geoalchemy2.types.Geometry(geometry_type="POINT", srid=4326), nullable=True
        ),
        sa.Column("elevation", postgresql.DOUBLE_PRECISION(), nullable=True),
        sa.Column("time", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("media_type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("url", sa.String(length=150), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("privacy_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["platform_id"],
            ["pepys.Platforms.platform_id"],
        ),
        sa.ForeignKeyConstraint(
            ["privacy_id"],
            ["pepys.Privacies.privacy_id"],
        ),
        sa.ForeignKeyConstraint(
            ["sensor_id"],
            ["pepys.Sensors.sensor_id"],
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["pepys.Datafiles.datafile_id"],
        ),
        sa.ForeignKeyConstraint(
            ["subject_id"],
            ["pepys.Platforms.platform_id"],
        ),
        sa.PrimaryKeyConstraint("media_id"),
        schema="pepys",
    )
    op.create_table(
        "States",
        sa.Column("state_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("time", postgresql.TIMESTAMP(), nullable=False),
        sa.Column("sensor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "location", geoalchemy2.types.Geometry(geometry_type="POINT", srid=4326), nullable=True
        ),
        sa.Column("elevation", postgresql.DOUBLE_PRECISION(), nullable=True),
        sa.Column("heading", postgresql.DOUBLE_PRECISION(), nullable=True),
        sa.Column("course", postgresql.DOUBLE_PRECISION(), nullable=True),
        sa.Column("speed", postgresql.DOUBLE_PRECISION(), nullable=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("privacy_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["privacy_id"],
            ["pepys.Privacies.privacy_id"],
        ),
        sa.ForeignKeyConstraint(
            ["sensor_id"],
            ["pepys.Sensors.sensor_id"],
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["pepys.Datafiles.datafile_id"],
        ),
        sa.PrimaryKeyConstraint("state_id"),
        schema="pepys",
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("States", schema="pepys")
    op.drop_table("Media", schema="pepys")
    op.drop_table("Contacts", schema="pepys")
    op.drop_table("Activations", schema="pepys")
    op.drop_table("Sensors", schema="pepys")
    op.drop_table("Participants", schema="pepys")
    op.drop_table("LogsHoldings", schema="pepys")
    op.drop_table("HostedBy", schema="pepys")
    op.drop_table("Geometries", schema="pepys")
    op.drop_table("Comments", schema="pepys")
    op.drop_table("Tasks", schema="pepys")
    op.drop_table("TaggedItems", schema="pepys")
    op.drop_table("Platforms", schema="pepys")
    op.drop_table("Logs", schema="pepys")
    op.drop_table("Datafiles", schema="pepys")
    op.drop_table("Users", schema="pepys")
    op.drop_table("UnitTypes", schema="pepys")
    op.drop_table("Tags", schema="pepys")
    op.drop_table("Synonyms", schema="pepys")
    op.drop_table("SensorTypes", schema="pepys")
    op.drop_table("Privacies", schema="pepys")
    op.drop_table("PlatformTypes", schema="pepys")
    op.drop_table("Nationalities", schema="pepys")
    op.drop_table("MediaTypes", schema="pepys")
    op.drop_table("GeometryTypes", schema="pepys")
    op.drop_table("GeometrySubTypes", schema="pepys")
    op.drop_table("Extractions", schema="pepys")
    op.drop_table("DatafileTypes", schema="pepys")
    op.drop_table("ContactTypes", schema="pepys")
    op.drop_table("ConfidenceLevels", schema="pepys")
    op.drop_table("CommodityTypes", schema="pepys")
    op.drop_table("CommentTypes", schema="pepys")
    op.drop_table("ClassificationTypes", schema="pepys")
    op.drop_table("Changes", schema="pepys")
    # ### end Alembic commands ###
