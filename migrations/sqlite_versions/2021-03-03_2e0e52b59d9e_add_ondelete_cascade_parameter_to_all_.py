"""Add ondelete=cascade parameter to all foreign key relationships

Revision ID: 2e0e52b59d9e
Revises: e9049ca0338a
Create Date: 2021-03-03 10:16:04.672346+00:00

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "2e0e52b59d9e"
down_revision = "e9049ca0338a"
branch_labels = None
depends_on = None

naming_convention = {
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
}


def upgrade():
    with op.batch_alter_table(
        "Activations", schema=None, naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint("fk_Activations_sensor_id_Sensors", type_="foreignkey")
        batch_op.drop_constraint("fk_Activations_privacy_id_Privacies", type_="foreignkey")
        batch_op.drop_constraint("fk_Activations_source_id_Datafiles", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_Activations_sensor_id_Sensors"),
            "Sensors",
            ["sensor_id"],
            ["sensor_id"],
            onupdate="cascade",
            ondelete="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Activations_privacy_id_Privacies"),
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            onupdate="cascade",
            ondelete="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Activations_source_id_Datafiles"),
            "Datafiles",
            ["source_id"],
            ["datafile_id"],
            onupdate="cascade",
            ondelete="cascade",
        )

    with op.batch_alter_table(
        "Comments", schema=None, naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint("fk_Comments_privacy_id_Privacies", type_="foreignkey")
        batch_op.drop_constraint("fk_Comments_platform_id_Platforms", type_="foreignkey")
        batch_op.drop_constraint("fk_Comments_comment_type_id_CommentTypes", type_="foreignkey")
        batch_op.drop_constraint("fk_Comments_source_id_Datafiles", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_Comments_privacy_id_Privacies"),
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            onupdate="cascade",
            ondelete="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Comments_platform_id_Platforms"),
            "Platforms",
            ["platform_id"],
            ["platform_id"],
            onupdate="cascade",
            ondelete="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Comments_comment_type_id_CommentTypes"),
            "CommentTypes",
            ["comment_type_id"],
            ["comment_type_id"],
            onupdate="cascade",
            ondelete="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Comments_source_id_Datafiles"),
            "Datafiles",
            ["source_id"],
            ["datafile_id"],
            onupdate="cascade",
            ondelete="cascade",
        )

    with op.batch_alter_table(
        "Contacts", schema=None, naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint("fk_Contacts_subject_id_Platforms", type_="foreignkey")
        batch_op.drop_constraint("fk_Contacts_privacy_id_Privacies", type_="foreignkey")
        batch_op.drop_constraint("fk_Contacts_sensor_id_Sensors", type_="foreignkey")
        batch_op.drop_constraint("fk_Contacts_source_id_Datafiles", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_Contacts_subject_id_Platforms"),
            "Platforms",
            ["subject_id"],
            ["platform_id"],
            onupdate="cascade",
            ondelete="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Contacts_privacy_id_Privacies"),
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            onupdate="cascade",
            ondelete="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Contacts_sensor_id_Sensors"),
            "Sensors",
            ["sensor_id"],
            ["sensor_id"],
            onupdate="cascade",
            ondelete="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Contacts_source_id_Datafiles"),
            "Datafiles",
            ["source_id"],
            ["datafile_id"],
            onupdate="cascade",
            ondelete="cascade",
        )

    with op.batch_alter_table(
        "Datafiles", schema=None, naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint("fk_Datafiles_privacy_id_Privacies", type_="foreignkey")
        batch_op.drop_constraint("fk_Datafiles_datafile_type_id_DatafileTypes", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_Datafiles_privacy_id_Privacies"),
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            onupdate="cascade",
            ondelete="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Datafiles_datafile_type_id_DatafileTypes"),
            "DatafileTypes",
            ["datafile_type_id"],
            ["datafile_type_id"],
            onupdate="cascade",
            ondelete="cascade",
        )

    with op.batch_alter_table(
        "Geometries", schema=None, naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint("fk_Geometries_privacy_id_Privacies", type_="foreignkey")
        batch_op.drop_constraint("fk_Geometries_geo_type_id_GeometryTypes", type_="foreignkey")
        batch_op.drop_constraint(
            "fk_Geometries_geo_sub_type_id_GeometrySubTypes", type_="foreignkey"
        )
        batch_op.drop_constraint("fk_Geometries_sensor_platform_id_Platforms", type_="foreignkey")
        batch_op.drop_constraint("fk_Geometries_task_id_Tasks", type_="foreignkey")
        batch_op.drop_constraint("fk_Geometries_subject_platform_id_Platforms", type_="foreignkey")
        batch_op.drop_constraint("fk_Geometries_source_id_Datafiles", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_Geometries_privacy_id_Privacies"),
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            onupdate="cascade",
            ondelete="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Geometries_geo_type_id_GeometryTypes"),
            "GeometryTypes",
            ["geo_type_id"],
            ["geo_type_id"],
            onupdate="cascade",
            ondelete="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Geometries_geo_sub_type_id_GeometrySubTypes"),
            "GeometrySubTypes",
            ["geo_sub_type_id"],
            ["geo_sub_type_id"],
            onupdate="cascade",
            ondelete="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Geometries_sensor_platform_id_Platforms"),
            "Platforms",
            ["sensor_platform_id"],
            ["platform_id"],
            onupdate="cascade",
            ondelete="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Geometries_task_id_Tasks"),
            "Tasks",
            ["task_id"],
            ["task_id"],
            onupdate="cascade",
            ondelete="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Geometries_subject_platform_id_Platforms"),
            "Platforms",
            ["subject_platform_id"],
            ["platform_id"],
            onupdate="cascade",
            ondelete="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Geometries_source_id_Datafiles"),
            "Datafiles",
            ["source_id"],
            ["datafile_id"],
            onupdate="cascade",
            ondelete="cascade",
        )

    with op.batch_alter_table(
        "GeometrySubTypes", schema=None, naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint("fk_GeometrySubTypes_parent_GeometryTypes", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_GeometrySubTypes_parent_GeometryTypes"),
            "GeometryTypes",
            ["parent"],
            ["geo_type_id"],
            onupdate="cascade",
            ondelete="cascade",
        )

    with op.batch_alter_table(
        "HostedBy", schema=None, naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint("fk_HostedBy_privacy_id_Privacies", type_="foreignkey")
        batch_op.drop_constraint("fk_HostedBy_host_id_Platforms", type_="foreignkey")
        batch_op.drop_constraint("fk_HostedBy_subject_id_Platforms", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_HostedBy_privacy_id_Privacies"),
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            onupdate="cascade",
            ondelete="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_HostedBy_host_id_Platforms"),
            "Platforms",
            ["host_id"],
            ["platform_id"],
            onupdate="cascade",
            ondelete="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_HostedBy_subject_id_Platforms"),
            "Platforms",
            ["subject_id"],
            ["platform_id"],
            onupdate="cascade",
            ondelete="cascade",
        )

    with op.batch_alter_table("Logs", schema=None, naming_convention=naming_convention) as batch_op:
        batch_op.drop_constraint("fk_Logs_change_id_Changes", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_Logs_change_id_Changes"),
            "Changes",
            ["change_id"],
            ["change_id"],
            onupdate="cascade",
            ondelete="cascade",
        )

    with op.batch_alter_table(
        "LogsHoldings", schema=None, naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint("fk_LogsHoldings_commodity_id_CommodityTypes", type_="foreignkey")
        batch_op.drop_constraint("fk_LogsHoldings_unit_type_id_UnitTypes", type_="foreignkey")
        batch_op.drop_constraint("fk_LogsHoldings_platform_id_Platforms", type_="foreignkey")
        batch_op.drop_constraint("fk_LogsHoldings_privacy_id_Privacies", type_="foreignkey")
        batch_op.drop_constraint("fk_LogsHoldings_source_id_Datafiles", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_LogsHoldings_commodity_id_CommodityTypes"),
            "CommodityTypes",
            ["commodity_id"],
            ["commodity_type_id"],
            onupdate="cascade",
            ondelete="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_LogsHoldings_unit_type_id_UnitTypes"),
            "UnitTypes",
            ["unit_type_id"],
            ["unit_type_id"],
            onupdate="cascade",
            ondelete="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_LogsHoldings_platform_id_Platforms"),
            "Platforms",
            ["platform_id"],
            ["platform_id"],
            onupdate="cascade",
            ondelete="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_LogsHoldings_privacy_id_Privacies"),
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            onupdate="cascade",
            ondelete="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_LogsHoldings_source_id_Datafiles"),
            "Datafiles",
            ["source_id"],
            ["datafile_id"],
            onupdate="cascade",
            ondelete="cascade",
        )

    with op.batch_alter_table(
        "Media", schema=None, naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint("fk_Media_subject_id_Platforms", type_="foreignkey")
        batch_op.drop_constraint("fk_Media_media_type_id_MediaTypes", type_="foreignkey")
        batch_op.drop_constraint("fk_Media_privacy_id_Privacies", type_="foreignkey")
        batch_op.drop_constraint("fk_Media_platform_id_Platforms", type_="foreignkey")
        batch_op.drop_constraint("fk_Media_sensor_id_Sensors", type_="foreignkey")
        batch_op.drop_constraint("fk_Media_source_id_Datafiles", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_Media_subject_id_Platforms"),
            "Platforms",
            ["subject_id"],
            ["platform_id"],
            onupdate="cascade",
            ondelete="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Media_media_type_id_MediaTypes"),
            "MediaTypes",
            ["media_type_id"],
            ["media_type_id"],
            onupdate="cascade",
            ondelete="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Media_privacy_id_Privacies"),
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            onupdate="cascade",
            ondelete="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Media_platform_id_Platforms"),
            "Platforms",
            ["platform_id"],
            ["platform_id"],
            onupdate="cascade",
            ondelete="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Media_sensor_id_Sensors"),
            "Sensors",
            ["sensor_id"],
            ["sensor_id"],
            onupdate="cascade",
            ondelete="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Media_source_id_Datafiles"),
            "Datafiles",
            ["source_id"],
            ["datafile_id"],
            onupdate="cascade",
            ondelete="cascade",
        )

    with op.batch_alter_table(
        "Participants", schema=None, naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint("fk_Participants_task_id_Tasks", type_="foreignkey")
        batch_op.drop_constraint("fk_Participants_privacy_id_Privacies", type_="foreignkey")
        batch_op.drop_constraint("fk_Participants_platform_id_Platforms", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_Participants_task_id_Tasks"),
            "Tasks",
            ["task_id"],
            ["task_id"],
            onupdate="cascade",
            ondelete="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Participants_privacy_id_Privacies"),
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            onupdate="cascade",
            ondelete="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Participants_platform_id_Platforms"),
            "Platforms",
            ["platform_id"],
            ["platform_id"],
            onupdate="cascade",
            ondelete="cascade",
        )

    with op.batch_alter_table(
        "Platforms", schema=None, naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint("fk_Platforms_nationality_id_Nationalities", type_="foreignkey")
        batch_op.drop_constraint("fk_Platforms_privacy_id_Privacies", type_="foreignkey")
        batch_op.drop_constraint("fk_Platforms_platform_type_id_PlatformTypes", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_Platforms_nationality_id_Nationalities"),
            "Nationalities",
            ["nationality_id"],
            ["nationality_id"],
            onupdate="cascade",
            ondelete="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Platforms_privacy_id_Privacies"),
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            onupdate="cascade",
            ondelete="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Platforms_platform_type_id_PlatformTypes"),
            "PlatformTypes",
            ["platform_type_id"],
            ["platform_type_id"],
            onupdate="cascade",
            ondelete="cascade",
        )

    with op.batch_alter_table(
        "Sensors", schema=None, naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint("fk_Sensors_privacy_id_Privacies", type_="foreignkey")
        batch_op.drop_constraint("fk_Sensors_sensor_type_id_SensorTypes", type_="foreignkey")
        batch_op.drop_constraint("fk_Sensors_host_Platforms", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_Sensors_privacy_id_Privacies"),
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            onupdate="cascade",
            ondelete="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Sensors_sensor_type_id_SensorTypes"),
            "SensorTypes",
            ["sensor_type_id"],
            ["sensor_type_id"],
            onupdate="cascade",
            ondelete="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Sensors_host_Platforms"),
            "Platforms",
            ["host"],
            ["platform_id"],
            onupdate="cascade",
            ondelete="cascade",
        )

    with op.batch_alter_table(
        "States", schema=None, naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint("fk_States_sensor_id_Sensors", type_="foreignkey")
        batch_op.drop_constraint("fk_States_privacy_id_Privacies", type_="foreignkey")
        batch_op.drop_constraint("fk_States_source_id_Datafiles", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_States_sensor_id_Sensors"),
            "Sensors",
            ["sensor_id"],
            ["sensor_id"],
            onupdate="cascade",
            ondelete="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_States_privacy_id_Privacies"),
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            onupdate="cascade",
            ondelete="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_States_source_id_Datafiles"),
            "Datafiles",
            ["source_id"],
            ["datafile_id"],
            onupdate="cascade",
            ondelete="cascade",
        )

    with op.batch_alter_table(
        "TaggedItems", schema=None, naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint("fk_TaggedItems_tag_id_Tags", type_="foreignkey")
        batch_op.drop_constraint("fk_TaggedItems_tagged_by_id_Users", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_TaggedItems_tag_id_Tags"),
            "Tags",
            ["tag_id"],
            ["tag_id"],
            onupdate="cascade",
            ondelete="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_TaggedItems_tagged_by_id_Users"),
            "Users",
            ["tagged_by_id"],
            ["user_id"],
            onupdate="cascade",
            ondelete="cascade",
        )

    with op.batch_alter_table(
        "Tasks", schema=None, naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint("fk_Tasks_privacy_id_Privacies", type_="foreignkey")
        batch_op.drop_constraint("fk_Tasks_parent_id_Tasks", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_Tasks_privacy_id_Privacies"),
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            onupdate="cascade",
            ondelete="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Tasks_parent_id_Tasks"),
            "Tasks",
            ["parent_id"],
            ["task_id"],
            onupdate="cascade",
            ondelete="cascade",
        )


def downgrade():
    with op.batch_alter_table(
        "Tasks", schema=None, naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_Tasks_parent_id_Tasks"), type_="foreignkey")
        batch_op.drop_constraint(batch_op.f("fk_Tasks_privacy_id_Privacies"), type_="foreignkey")
        batch_op.create_foreign_key(
            None, "Privacies", ["privacy_id"], ["privacy_id"], onupdate="CASCADE"
        )
        batch_op.create_foreign_key(None, "Tasks", ["parent_id"], ["task_id"], onupdate="CASCADE")

    with op.batch_alter_table(
        "TaggedItems", schema=None, naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_TaggedItems_tagged_by_id_Users"), type_="foreignkey"
        )
        batch_op.drop_constraint(batch_op.f("fk_TaggedItems_tag_id_Tags"), type_="foreignkey")
        batch_op.create_foreign_key(
            None, "Users", ["tagged_by_id"], ["user_id"], onupdate="CASCADE"
        )
        batch_op.create_foreign_key(None, "Tags", ["tag_id"], ["tag_id"], onupdate="CASCADE")

    with op.batch_alter_table(
        "States", schema=None, naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_States_privacy_id_Privacies"), type_="foreignkey")
        batch_op.drop_constraint(batch_op.f("fk_States_sensor_id_Sensors"), type_="foreignkey")
        batch_op.create_foreign_key(
            None, "Privacies", ["privacy_id"], ["privacy_id"], onupdate="CASCADE"
        )
        batch_op.create_foreign_key(
            None, "Sensors", ["sensor_id"], ["sensor_id"], onupdate="CASCADE"
        )

    with op.batch_alter_table(
        "Sensors", schema=None, naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_Sensors_sensor_type_id_SensorTypes"), type_="foreignkey"
        )
        batch_op.drop_constraint(batch_op.f("fk_Sensors_privacy_id_Privacies"), type_="foreignkey")
        batch_op.create_foreign_key(
            None, "Privacies", ["privacy_id"], ["privacy_id"], onupdate="CASCADE"
        )
        batch_op.create_foreign_key(
            None, "SensorTypes", ["sensor_type_id"], ["sensor_type_id"], onupdate="CASCADE"
        )

    with op.batch_alter_table(
        "Platforms", schema=None, naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_Platforms_platform_type_id_PlatformTypes"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("fk_Platforms_privacy_id_Privacies"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("fk_Platforms_nationality_id_Nationalities"), type_="foreignkey"
        )
        batch_op.create_foreign_key(
            None, "PlatformTypes", ["platform_type_id"], ["platform_type_id"], onupdate="CASCADE"
        )
        batch_op.create_foreign_key(
            None, "Nationalities", ["nationality_id"], ["nationality_id"], onupdate="CASCADE"
        )
        batch_op.create_foreign_key(
            None, "Privacies", ["privacy_id"], ["privacy_id"], onupdate="CASCADE"
        )

    with op.batch_alter_table(
        "Participants", schema=None, naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_Participants_platform_id_Platforms"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("fk_Participants_privacy_id_Privacies"), type_="foreignkey"
        )
        batch_op.drop_constraint(batch_op.f("fk_Participants_task_id_Tasks"), type_="foreignkey")
        batch_op.create_foreign_key(
            None, "Platforms", ["platform_id"], ["platform_id"], onupdate="CASCADE"
        )
        batch_op.create_foreign_key(None, "Tasks", ["task_id"], ["task_id"], onupdate="CASCADE")
        batch_op.create_foreign_key(
            None, "Privacies", ["privacy_id"], ["privacy_id"], onupdate="CASCADE"
        )

    with op.batch_alter_table(
        "Media", schema=None, naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_Media_sensor_id_Sensors"), type_="foreignkey")
        batch_op.drop_constraint(batch_op.f("fk_Media_platform_id_Platforms"), type_="foreignkey")
        batch_op.drop_constraint(batch_op.f("fk_Media_privacy_id_Privacies"), type_="foreignkey")
        batch_op.drop_constraint(
            batch_op.f("fk_Media_media_type_id_MediaTypes"), type_="foreignkey"
        )
        batch_op.drop_constraint(batch_op.f("fk_Media_subject_id_Platforms"), type_="foreignkey")
        batch_op.create_foreign_key(
            None, "Sensors", ["sensor_id"], ["sensor_id"], onupdate="CASCADE"
        )
        batch_op.create_foreign_key(
            None, "MediaTypes", ["media_type_id"], ["media_type_id"], onupdate="CASCADE"
        )
        batch_op.create_foreign_key(
            None, "Platforms", ["subject_id"], ["platform_id"], onupdate="CASCADE"
        )
        batch_op.create_foreign_key(
            None, "Privacies", ["privacy_id"], ["privacy_id"], onupdate="CASCADE"
        )
        batch_op.create_foreign_key(
            None, "Platforms", ["platform_id"], ["platform_id"], onupdate="CASCADE"
        )

    with op.batch_alter_table(
        "LogsHoldings", schema=None, naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_LogsHoldings_privacy_id_Privacies"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("fk_LogsHoldings_platform_id_Platforms"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("fk_LogsHoldings_unit_type_id_UnitTypes"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("fk_LogsHoldings_commodity_id_CommodityTypes"), type_="foreignkey"
        )
        batch_op.create_foreign_key(
            None, "Platforms", ["platform_id"], ["platform_id"], onupdate="CASCADE"
        )
        batch_op.create_foreign_key(
            None, "UnitTypes", ["unit_type_id"], ["unit_type_id"], onupdate="CASCADE"
        )
        batch_op.create_foreign_key(
            None, "CommodityTypes", ["commodity_id"], ["commodity_type_id"], onupdate="CASCADE"
        )
        batch_op.create_foreign_key(
            None, "Privacies", ["privacy_id"], ["privacy_id"], onupdate="CASCADE"
        )

    with op.batch_alter_table("Logs", schema=None, naming_convention=naming_convention) as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_Logs_change_id_Changes"), type_="foreignkey")
        batch_op.create_foreign_key(
            None, "Changes", ["change_id"], ["change_id"], onupdate="CASCADE"
        )

    with op.batch_alter_table(
        "HostedBy", schema=None, naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_HostedBy_subject_id_Platforms"), type_="foreignkey")
        batch_op.drop_constraint(batch_op.f("fk_HostedBy_host_id_Platforms"), type_="foreignkey")
        batch_op.drop_constraint(batch_op.f("fk_HostedBy_privacy_id_Privacies"), type_="foreignkey")
        batch_op.create_foreign_key(
            None, "Privacies", ["privacy_id"], ["privacy_id"], onupdate="CASCADE"
        )
        batch_op.create_foreign_key(
            None, "Platforms", ["subject_id"], ["platform_id"], onupdate="CASCADE"
        )
        batch_op.create_foreign_key(
            None, "Platforms", ["host_id"], ["platform_id"], onupdate="CASCADE"
        )

    with op.batch_alter_table(
        "GeometrySubTypes", schema=None, naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_GeometrySubTypes_parent_GeometryTypes"), type_="foreignkey"
        )
        batch_op.create_foreign_key(
            None, "GeometryTypes", ["parent"], ["geo_type_id"], onupdate="CASCADE"
        )

    with op.batch_alter_table(
        "Geometries", schema=None, naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_Geometries_subject_platform_id_Platforms"), type_="foreignkey"
        )
        batch_op.drop_constraint(batch_op.f("fk_Geometries_task_id_Tasks"), type_="foreignkey")
        batch_op.drop_constraint(
            batch_op.f("fk_Geometries_sensor_platform_id_Platforms"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("fk_Geometries_geo_sub_type_id_GeometrySubTypes"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("fk_Geometries_geo_type_id_GeometryTypes"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("fk_Geometries_privacy_id_Privacies"), type_="foreignkey"
        )
        batch_op.create_foreign_key(
            None, "Privacies", ["privacy_id"], ["privacy_id"], onupdate="CASCADE"
        )
        batch_op.create_foreign_key(
            None, "GeometryTypes", ["geo_type_id"], ["geo_type_id"], onupdate="CASCADE"
        )
        batch_op.create_foreign_key(
            None, "Platforms", ["sensor_platform_id"], ["platform_id"], onupdate="CASCADE"
        )
        batch_op.create_foreign_key(
            None, "Platforms", ["subject_platform_id"], ["platform_id"], onupdate="CASCADE"
        )
        batch_op.create_foreign_key(
            None, "GeometrySubTypes", ["geo_sub_type_id"], ["geo_sub_type_id"], onupdate="CASCADE"
        )
        batch_op.create_foreign_key(None, "Tasks", ["task_id"], ["task_id"], onupdate="CASCADE")

    with op.batch_alter_table(
        "Datafiles", schema=None, naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_Datafiles_datafile_type_id_DatafileTypes"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("fk_Datafiles_privacy_id_Privacies"), type_="foreignkey"
        )
        batch_op.create_foreign_key(
            None, "Privacies", ["privacy_id"], ["privacy_id"], onupdate="CASCADE"
        )
        batch_op.create_foreign_key(
            None, "DatafileTypes", ["datafile_type_id"], ["datafile_type_id"], onupdate="CASCADE"
        )

    with op.batch_alter_table(
        "Contacts", schema=None, naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_Contacts_sensor_id_Sensors"), type_="foreignkey")
        batch_op.drop_constraint(batch_op.f("fk_Contacts_privacy_id_Privacies"), type_="foreignkey")
        batch_op.drop_constraint(batch_op.f("fk_Contacts_subject_id_Platforms"), type_="foreignkey")
        batch_op.create_foreign_key(
            None, "Platforms", ["subject_id"], ["platform_id"], onupdate="CASCADE"
        )
        batch_op.create_foreign_key(
            None, "Sensors", ["sensor_id"], ["sensor_id"], onupdate="CASCADE"
        )
        batch_op.create_foreign_key(
            None, "Privacies", ["privacy_id"], ["privacy_id"], onupdate="CASCADE"
        )

    with op.batch_alter_table(
        "Comments", schema=None, naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_Comments_comment_type_id_CommentTypes"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("fk_Comments_platform_id_Platforms"), type_="foreignkey"
        )
        batch_op.drop_constraint(batch_op.f("fk_Comments_privacy_id_Privacies"), type_="foreignkey")
        batch_op.create_foreign_key(
            None, "Platforms", ["platform_id"], ["platform_id"], onupdate="CASCADE"
        )
        batch_op.create_foreign_key(
            None, "Privacies", ["privacy_id"], ["privacy_id"], onupdate="CASCADE"
        )
        batch_op.create_foreign_key(
            None, "CommentTypes", ["comment_type_id"], ["comment_type_id"], onupdate="CASCADE"
        )

    with op.batch_alter_table(
        "Activations", schema=None, naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_Activations_privacy_id_Privacies"), type_="foreignkey"
        )
        batch_op.drop_constraint(batch_op.f("fk_Activations_sensor_id_Sensors"), type_="foreignkey")
        batch_op.create_foreign_key(
            None, "Privacies", ["privacy_id"], ["privacy_id"], onupdate="CASCADE"
        )
        batch_op.create_foreign_key(
            None, "Sensors", ["sensor_id"], ["sensor_id"], onupdate="CASCADE"
        )
