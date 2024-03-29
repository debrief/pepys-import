"""Add onupdate=cascade parameter to foreign key fields

Revision ID: 351e30ff45e6
Revises: 23345c20c2c5
Create Date: 2020-06-15 12:41:54.820265

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "351e30ff45e6"
down_revision = "23345c20c2c5"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("Activations", schema="pepys") as batch_op:
        batch_op.drop_constraint("fk_Activations_source_id_Datafiles", type_="foreignkey")
        batch_op.drop_constraint("fk_Activations_privacy_id_Privacies", type_="foreignkey")
        batch_op.drop_constraint("fk_Activations_sensor_id_Sensors", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_Activations_privacy_id_Privacies"),
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Activations_source_id_Datafiles"),
            "Datafiles",
            ["source_id"],
            ["datafile_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Activations_sensor_id_Sensors"),
            "Sensors",
            ["sensor_id"],
            ["sensor_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )

    with op.batch_alter_table("Comments", schema="pepys") as batch_op:
        batch_op.drop_constraint("fk_Comments_platform_id_Platforms", type_="foreignkey")
        batch_op.drop_constraint("fk_Comments_source_id_Datafiles", type_="foreignkey")
        batch_op.drop_constraint("fk_Comments_comment_type_id_CommentTypes", type_="foreignkey")
        batch_op.drop_constraint("fk_Comments_privacy_id_Privacies", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_Comments_source_id_Datafiles"),
            "Datafiles",
            ["source_id"],
            ["datafile_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Comments_platform_id_Platforms"),
            "Platforms",
            ["platform_id"],
            ["platform_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Comments_privacy_id_Privacies"),
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Comments_comment_type_id_CommentTypes"),
            "CommentTypes",
            ["comment_type_id"],
            ["comment_type_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )

    with op.batch_alter_table("Contacts", schema="pepys") as batch_op:
        batch_op.drop_constraint("fk_Contacts_source_id_Datafiles", type_="foreignkey")
        batch_op.drop_constraint("fk_Contacts_privacy_id_Privacies", type_="foreignkey")
        batch_op.drop_constraint("fk_Contacts_subject_id_Platforms", type_="foreignkey")
        batch_op.drop_constraint("fk_Contacts_sensor_id_Sensors", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_Contacts_sensor_id_Sensors"),
            "Sensors",
            ["sensor_id"],
            ["sensor_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Contacts_source_id_Datafiles"),
            "Datafiles",
            ["source_id"],
            ["datafile_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Contacts_privacy_id_Privacies"),
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Contacts_subject_id_Platforms"),
            "Platforms",
            ["subject_id"],
            ["platform_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )

    with op.batch_alter_table("Datafiles", schema="pepys") as batch_op:
        batch_op.drop_constraint("fk_Datafiles_datafile_type_id_DatafileTypes", type_="foreignkey")
        batch_op.drop_constraint("fk_Datafiles_privacy_id_Privacies", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_Datafiles_datafile_type_id_DatafileTypes"),
            "DatafileTypes",
            ["datafile_type_id"],
            ["datafile_type_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Datafiles_privacy_id_Privacies"),
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )

    with op.batch_alter_table("Geometries", schema="pepys") as batch_op:
        batch_op.drop_constraint("fk_Geometries_subject_platform_id_Platforms", type_="foreignkey")
        batch_op.drop_constraint("fk_Geometries_task_id_Tasks", type_="foreignkey")
        batch_op.drop_constraint("fk_Geometries_privacy_id_Privacies", type_="foreignkey")
        batch_op.drop_constraint(
            "fk_Geometries_geo_sub_type_id_GeometrySubTypes", type_="foreignkey"
        )
        batch_op.drop_constraint("fk_Geometries_geo_type_id_GeometryTypes", type_="foreignkey")
        batch_op.drop_constraint("fk_Geometries_source_id_Datafiles", type_="foreignkey")
        batch_op.drop_constraint("fk_Geometries_sensor_platform_id_Platforms", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_Geometries_subject_platform_id_Platforms"),
            "Platforms",
            ["subject_platform_id"],
            ["platform_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Geometries_sensor_platform_id_Platforms"),
            "Platforms",
            ["sensor_platform_id"],
            ["platform_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Geometries_task_id_Tasks"),
            "Tasks",
            ["task_id"],
            ["task_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Geometries_geo_type_id_GeometryTypes"),
            "GeometryTypes",
            ["geo_type_id"],
            ["geo_type_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Geometries_privacy_id_Privacies"),
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Geometries_source_id_Datafiles"),
            "Datafiles",
            ["source_id"],
            ["datafile_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Geometries_geo_sub_type_id_GeometrySubTypes"),
            "GeometrySubTypes",
            ["geo_sub_type_id"],
            ["geo_sub_type_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )

    with op.batch_alter_table("HostedBy", schema="pepys") as batch_op:
        batch_op.drop_constraint("fk_HostedBy_privacy_id_Privacies", type_="foreignkey")
        batch_op.drop_constraint("fk_HostedBy_host_id_Platforms", type_="foreignkey")
        batch_op.drop_constraint("fk_HostedBy_subject_id_Platforms", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_HostedBy_subject_id_Platforms"),
            "Platforms",
            ["subject_id"],
            ["platform_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_HostedBy_privacy_id_Privacies"),
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_HostedBy_host_id_Platforms"),
            "Platforms",
            ["host_id"],
            ["platform_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )

    with op.batch_alter_table("Logs", schema="pepys") as batch_op:
        batch_op.drop_constraint("fk_Logs_change_id_Changes", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_Logs_change_id_Changes"),
            "Changes",
            ["change_id"],
            ["change_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )

    with op.batch_alter_table("LogsHoldings", schema="pepys") as batch_op:
        batch_op.drop_constraint("fk_LogsHoldings_unit_type_id_UnitTypes", type_="foreignkey")
        batch_op.drop_constraint("fk_LogsHoldings_privacy_id_Privacies", type_="foreignkey")
        batch_op.drop_constraint("fk_LogsHoldings_commodity_id_CommodityTypes", type_="foreignkey")
        batch_op.drop_constraint("fk_LogsHoldings_platform_id_Platforms", type_="foreignkey")
        batch_op.drop_constraint("fk_LogsHoldings_source_id_Datafiles", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_LogsHoldings_commodity_id_CommodityTypes"),
            "CommodityTypes",
            ["commodity_id"],
            ["commodity_type_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_LogsHoldings_platform_id_Platforms"),
            "Platforms",
            ["platform_id"],
            ["platform_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_LogsHoldings_source_id_Datafiles"),
            "Datafiles",
            ["source_id"],
            ["datafile_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_LogsHoldings_unit_type_id_UnitTypes"),
            "UnitTypes",
            ["unit_type_id"],
            ["unit_type_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_LogsHoldings_privacy_id_Privacies"),
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )

    with op.batch_alter_table("Media", schema="pepys") as batch_op:
        batch_op.drop_constraint("fk_Media_subject_id_Platforms", type_="foreignkey")
        batch_op.drop_constraint("fk_Media_source_id_Datafiles", type_="foreignkey")
        batch_op.drop_constraint("fk_Media_platform_id_Platforms", type_="foreignkey")
        batch_op.drop_constraint("fk_Media_privacy_id_Privacies", type_="foreignkey")
        batch_op.drop_constraint("fk_Media_media_type_id_MediaTypes", type_="foreignkey")
        batch_op.drop_constraint("fk_Media_sensor_id_Sensors", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_Media_subject_id_Platforms"),
            "Platforms",
            ["subject_id"],
            ["platform_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Media_privacy_id_Privacies"),
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Media_platform_id_Platforms"),
            "Platforms",
            ["platform_id"],
            ["platform_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Media_source_id_Datafiles"),
            "Datafiles",
            ["source_id"],
            ["datafile_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Media_media_type_id_MediaTypes"),
            "MediaTypes",
            ["media_type_id"],
            ["media_type_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Media_sensor_id_Sensors"),
            "Sensors",
            ["sensor_id"],
            ["sensor_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )

    with op.batch_alter_table("Participants", schema="pepys") as batch_op:
        batch_op.drop_constraint("fk_Participants_platform_id_Platforms", type_="foreignkey")
        batch_op.drop_constraint("fk_Participants_privacy_id_Privacies", type_="foreignkey")
        batch_op.drop_constraint("fk_Participants_task_id_Tasks", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_Participants_platform_id_Platforms"),
            "Platforms",
            ["platform_id"],
            ["platform_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Participants_task_id_Tasks"),
            "Tasks",
            ["task_id"],
            ["task_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Participants_privacy_id_Privacies"),
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )

    with op.batch_alter_table("Platforms", schema="pepys") as batch_op:
        batch_op.drop_constraint("fk_Platforms_platform_type_id_PlatformTypes", type_="foreignkey")
        batch_op.drop_constraint("fk_Platforms_privacy_id_Privacies", type_="foreignkey")
        batch_op.drop_constraint("fk_Platforms_nationality_id_Nationalities", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_Platforms_nationality_id_Nationalities"),
            "Nationalities",
            ["nationality_id"],
            ["nationality_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Platforms_privacy_id_Privacies"),
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Platforms_platform_type_id_PlatformTypes"),
            "PlatformTypes",
            ["platform_type_id"],
            ["platform_type_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )

    with op.batch_alter_table("Sensors", schema="pepys") as batch_op:
        batch_op.drop_constraint("fk_Sensors_host_Platforms", type_="foreignkey")
        batch_op.drop_constraint("fk_Sensors_sensor_type_id_SensorTypes", type_="foreignkey")
        batch_op.drop_constraint("fk_Sensors_privacy_id_Privacies", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_Sensors_privacy_id_Privacies"),
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Sensors_host_Platforms"),
            "Platforms",
            ["host"],
            ["platform_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Sensors_sensor_type_id_SensorTypes"),
            "SensorTypes",
            ["sensor_type_id"],
            ["sensor_type_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )

    with op.batch_alter_table("States", schema="pepys") as batch_op:
        batch_op.drop_constraint("fk_States_sensor_id_Sensors", type_="foreignkey")
        batch_op.drop_constraint("fk_States_privacy_id_Privacies", type_="foreignkey")
        batch_op.drop_constraint("fk_States_source_id_Datafiles", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_States_sensor_id_Sensors"),
            "Sensors",
            ["sensor_id"],
            ["sensor_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_States_source_id_Datafiles"),
            "Datafiles",
            ["source_id"],
            ["datafile_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_States_privacy_id_Privacies"),
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )

    with op.batch_alter_table("TaggedItems", schema="pepys") as batch_op:
        batch_op.drop_constraint("fk_TaggedItems_tag_id_Tags", type_="foreignkey")
        batch_op.drop_constraint("fk_TaggedItems_tagged_by_id_Users", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_TaggedItems_tagged_by_id_Users"),
            "Users",
            ["tagged_by_id"],
            ["user_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_TaggedItems_tag_id_Tags"),
            "Tags",
            ["tag_id"],
            ["tag_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )

    with op.batch_alter_table("Tasks", schema="pepys") as batch_op:
        batch_op.drop_constraint("fk_Tasks_privacy_id_Privacies", type_="foreignkey")
        batch_op.drop_constraint("fk_Tasks_parent_id_Tasks", type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_Tasks_privacy_id_Privacies"),
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_Tasks_parent_id_Tasks"),
            "Tasks",
            ["parent_id"],
            ["task_id"],
            referent_schema="pepys",
            onupdate="cascade",
        )

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("Tasks", schema="pepys") as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_Tasks_parent_id_Tasks"), type_="foreignkey")
        batch_op.drop_constraint(batch_op.f("fk_Tasks_privacy_id_Privacies"), type_="foreignkey")
        batch_op.create_foreign_key(
            "fk_Tasks_parent_id_Tasks", "Tasks", ["parent_id"], ["task_id"], referent_schema="pepys"
        )
        batch_op.create_foreign_key(
            "fk_Tasks_privacy_id_Privacies",
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            referent_schema="pepys",
        )

    with op.batch_alter_table("TaggedItems", schema="pepys") as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_TaggedItems_tag_id_Tags"), type_="foreignkey")
        batch_op.drop_constraint(
            batch_op.f("fk_TaggedItems_tagged_by_id_Users"), type_="foreignkey"
        )
        batch_op.create_foreign_key(
            "fk_TaggedItems_tagged_by_id_Users",
            "Users",
            ["tagged_by_id"],
            ["user_id"],
            referent_schema="pepys",
        )
        batch_op.create_foreign_key(
            "fk_TaggedItems_tag_id_Tags", "Tags", ["tag_id"], ["tag_id"], referent_schema="pepys"
        )

    with op.batch_alter_table("States", schema="pepys") as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_States_privacy_id_Privacies"), type_="foreignkey")
        batch_op.drop_constraint(batch_op.f("fk_States_source_id_Datafiles"), type_="foreignkey")
        batch_op.drop_constraint(batch_op.f("fk_States_sensor_id_Sensors"), type_="foreignkey")
        batch_op.create_foreign_key(
            "fk_States_source_id_Datafiles",
            "Datafiles",
            ["source_id"],
            ["datafile_id"],
            referent_schema="pepys",
        )
        batch_op.create_foreign_key(
            "fk_States_privacy_id_Privacies",
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            referent_schema="pepys",
        )
        batch_op.create_foreign_key(
            "fk_States_sensor_id_Sensors",
            "Sensors",
            ["sensor_id"],
            ["sensor_id"],
            referent_schema="pepys",
        )

    with op.batch_alter_table("Sensors", schema="pepys") as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_Sensors_sensor_type_id_SensorTypes"), type_="foreignkey"
        )
        batch_op.drop_constraint(batch_op.f("fk_Sensors_host_Platforms"), type_="foreignkey")
        batch_op.drop_constraint(batch_op.f("fk_Sensors_privacy_id_Privacies"), type_="foreignkey")
        batch_op.create_foreign_key(
            "fk_Sensors_privacy_id_Privacies",
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            referent_schema="pepys",
        )
        batch_op.create_foreign_key(
            "fk_Sensors_sensor_type_id_SensorTypes",
            "SensorTypes",
            ["sensor_type_id"],
            ["sensor_type_id"],
            referent_schema="pepys",
        )
        batch_op.create_foreign_key(
            "fk_Sensors_host_Platforms",
            "Platforms",
            ["host"],
            ["platform_id"],
            referent_schema="pepys",
        )

    with op.batch_alter_table("Platforms", schema="pepys") as batch_op:
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
            "fk_Platforms_nationality_id_Nationalities",
            "Nationalities",
            ["nationality_id"],
            ["nationality_id"],
            referent_schema="pepys",
        )
        batch_op.create_foreign_key(
            "fk_Platforms_privacy_id_Privacies",
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            referent_schema="pepys",
        )
        batch_op.create_foreign_key(
            "fk_Platforms_platform_type_id_PlatformTypes",
            "PlatformTypes",
            ["platform_type_id"],
            ["platform_type_id"],
            referent_schema="pepys",
        )

    with op.batch_alter_table("Participants", schema="pepys") as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_Participants_privacy_id_Privacies"), type_="foreignkey"
        )
        batch_op.drop_constraint(batch_op.f("fk_Participants_task_id_Tasks"), type_="foreignkey")
        batch_op.drop_constraint(
            batch_op.f("fk_Participants_platform_id_Platforms"), type_="foreignkey"
        )
        batch_op.create_foreign_key(
            "fk_Participants_task_id_Tasks",
            "Tasks",
            ["task_id"],
            ["task_id"],
            referent_schema="pepys",
        )
        batch_op.create_foreign_key(
            "fk_Participants_privacy_id_Privacies",
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            referent_schema="pepys",
        )
        batch_op.create_foreign_key(
            "fk_Participants_platform_id_Platforms",
            "Platforms",
            ["platform_id"],
            ["platform_id"],
            referent_schema="pepys",
        )

    with op.batch_alter_table("Media", schema="pepys") as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_Media_sensor_id_Sensors"), type_="foreignkey")
        batch_op.drop_constraint(
            batch_op.f("fk_Media_media_type_id_MediaTypes"), type_="foreignkey"
        )
        batch_op.drop_constraint(batch_op.f("fk_Media_source_id_Datafiles"), type_="foreignkey")
        batch_op.drop_constraint(batch_op.f("fk_Media_platform_id_Platforms"), type_="foreignkey")
        batch_op.drop_constraint(batch_op.f("fk_Media_privacy_id_Privacies"), type_="foreignkey")
        batch_op.drop_constraint(batch_op.f("fk_Media_subject_id_Platforms"), type_="foreignkey")
        batch_op.create_foreign_key(
            "fk_Media_sensor_id_Sensors",
            "Sensors",
            ["sensor_id"],
            ["sensor_id"],
            referent_schema="pepys",
        )
        batch_op.create_foreign_key(
            "fk_Media_media_type_id_MediaTypes",
            "MediaTypes",
            ["media_type_id"],
            ["media_type_id"],
            referent_schema="pepys",
        )
        batch_op.create_foreign_key(
            "fk_Media_privacy_id_Privacies",
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            referent_schema="pepys",
        )
        batch_op.create_foreign_key(
            "fk_Media_platform_id_Platforms",
            "Platforms",
            ["platform_id"],
            ["platform_id"],
            referent_schema="pepys",
        )
        batch_op.create_foreign_key(
            "fk_Media_source_id_Datafiles",
            "Datafiles",
            ["source_id"],
            ["datafile_id"],
            referent_schema="pepys",
        )
        batch_op.create_foreign_key(
            "fk_Media_subject_id_Platforms",
            "Platforms",
            ["subject_id"],
            ["platform_id"],
            referent_schema="pepys",
        )

    with op.batch_alter_table("LogsHoldings", schema="pepys") as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_LogsHoldings_privacy_id_Privacies"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("fk_LogsHoldings_unit_type_id_UnitTypes"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("fk_LogsHoldings_source_id_Datafiles"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("fk_LogsHoldings_platform_id_Platforms"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("fk_LogsHoldings_commodity_id_CommodityTypes"), type_="foreignkey"
        )
        batch_op.create_foreign_key(
            "fk_LogsHoldings_source_id_Datafiles",
            "Datafiles",
            ["source_id"],
            ["datafile_id"],
            referent_schema="pepys",
        )
        batch_op.create_foreign_key(
            "fk_LogsHoldings_platform_id_Platforms",
            "Platforms",
            ["platform_id"],
            ["platform_id"],
            referent_schema="pepys",
        )
        batch_op.create_foreign_key(
            "fk_LogsHoldings_commodity_id_CommodityTypes",
            "CommodityTypes",
            ["commodity_id"],
            ["commodity_type_id"],
            referent_schema="pepys",
        )
        batch_op.create_foreign_key(
            "fk_LogsHoldings_privacy_id_Privacies",
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            referent_schema="pepys",
        )
        batch_op.create_foreign_key(
            "fk_LogsHoldings_unit_type_id_UnitTypes",
            "UnitTypes",
            ["unit_type_id"],
            ["unit_type_id"],
            referent_schema="pepys",
        )

    with op.batch_alter_table("Logs", schema="pepys") as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_Logs_change_id_Changes"), type_="foreignkey")
        batch_op.create_foreign_key(
            "fk_Logs_change_id_Changes",
            "Changes",
            ["change_id"],
            ["change_id"],
            referent_schema="pepys",
        )

    with op.batch_alter_table("HostedBy", schema="pepys") as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_HostedBy_host_id_Platforms"), type_="foreignkey")
        batch_op.drop_constraint(batch_op.f("fk_HostedBy_privacy_id_Privacies"), type_="foreignkey")
        batch_op.drop_constraint(batch_op.f("fk_HostedBy_subject_id_Platforms"), type_="foreignkey")
        batch_op.create_foreign_key(
            "fk_HostedBy_subject_id_Platforms",
            "Platforms",
            ["subject_id"],
            ["platform_id"],
            referent_schema="pepys",
        )
        batch_op.create_foreign_key(
            "fk_HostedBy_host_id_Platforms",
            "Platforms",
            ["host_id"],
            ["platform_id"],
            referent_schema="pepys",
        )
        batch_op.create_foreign_key(
            "fk_HostedBy_privacy_id_Privacies",
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            referent_schema="pepys",
        )

    with op.batch_alter_table("Geometries", schema="pepys") as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_Geometries_geo_sub_type_id_GeometrySubTypes"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("fk_Geometries_source_id_Datafiles"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("fk_Geometries_privacy_id_Privacies"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("fk_Geometries_geo_type_id_GeometryTypes"), type_="foreignkey"
        )
        batch_op.drop_constraint(batch_op.f("fk_Geometries_task_id_Tasks"), type_="foreignkey")
        batch_op.drop_constraint(
            batch_op.f("fk_Geometries_sensor_platform_id_Platforms"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("fk_Geometries_subject_platform_id_Platforms"), type_="foreignkey"
        )
        batch_op.create_foreign_key(
            "fk_Geometries_sensor_platform_id_Platforms",
            "Platforms",
            ["sensor_platform_id"],
            ["platform_id"],
            referent_schema="pepys",
        )
        batch_op.create_foreign_key(
            "fk_Geometries_source_id_Datafiles",
            "Datafiles",
            ["source_id"],
            ["datafile_id"],
            referent_schema="pepys",
        )
        batch_op.create_foreign_key(
            "fk_Geometries_geo_type_id_GeometryTypes",
            "GeometryTypes",
            ["geo_type_id"],
            ["geo_type_id"],
            referent_schema="pepys",
        )
        batch_op.create_foreign_key(
            "fk_Geometries_geo_sub_type_id_GeometrySubTypes",
            "GeometrySubTypes",
            ["geo_sub_type_id"],
            ["geo_sub_type_id"],
            referent_schema="pepys",
        )
        batch_op.create_foreign_key(
            "fk_Geometries_privacy_id_Privacies",
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            referent_schema="pepys",
        )
        batch_op.create_foreign_key(
            "fk_Geometries_task_id_Tasks",
            "Tasks",
            ["task_id"],
            ["task_id"],
            referent_schema="pepys",
        )
        batch_op.create_foreign_key(
            "fk_Geometries_subject_platform_id_Platforms",
            "Platforms",
            ["subject_platform_id"],
            ["platform_id"],
            referent_schema="pepys",
        )

    with op.batch_alter_table("Datafiles", schema="pepys") as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_Datafiles_privacy_id_Privacies"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("fk_Datafiles_datafile_type_id_DatafileTypes"), type_="foreignkey"
        )
        batch_op.create_foreign_key(
            "fk_Datafiles_privacy_id_Privacies",
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            referent_schema="pepys",
        )
        batch_op.create_foreign_key(
            "fk_Datafiles_datafile_type_id_DatafileTypes",
            "DatafileTypes",
            ["datafile_type_id"],
            ["datafile_type_id"],
            referent_schema="pepys",
        )

    with op.batch_alter_table("Contacts", schema="pepys") as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_Contacts_subject_id_Platforms"), type_="foreignkey")
        batch_op.drop_constraint(batch_op.f("fk_Contacts_privacy_id_Privacies"), type_="foreignkey")
        batch_op.drop_constraint(batch_op.f("fk_Contacts_source_id_Datafiles"), type_="foreignkey")
        batch_op.drop_constraint(batch_op.f("fk_Contacts_sensor_id_Sensors"), type_="foreignkey")
        batch_op.create_foreign_key(
            "fk_Contacts_sensor_id_Sensors",
            "Sensors",
            ["sensor_id"],
            ["sensor_id"],
            referent_schema="pepys",
        )
        batch_op.create_foreign_key(
            "fk_Contacts_subject_id_Platforms",
            "Platforms",
            ["subject_id"],
            ["platform_id"],
            referent_schema="pepys",
        )
        batch_op.create_foreign_key(
            "fk_Contacts_privacy_id_Privacies",
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            referent_schema="pepys",
        )
        batch_op.create_foreign_key(
            "fk_Contacts_source_id_Datafiles",
            "Datafiles",
            ["source_id"],
            ["datafile_id"],
            referent_schema="pepys",
        )

    with op.batch_alter_table("Comments", schema="pepys") as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_Comments_comment_type_id_CommentTypes"), type_="foreignkey"
        )
        batch_op.drop_constraint(batch_op.f("fk_Comments_privacy_id_Privacies"), type_="foreignkey")
        batch_op.drop_constraint(
            batch_op.f("fk_Comments_platform_id_Platforms"), type_="foreignkey"
        )
        batch_op.drop_constraint(batch_op.f("fk_Comments_source_id_Datafiles"), type_="foreignkey")
        batch_op.create_foreign_key(
            "fk_Comments_privacy_id_Privacies",
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            referent_schema="pepys",
        )
        batch_op.create_foreign_key(
            "fk_Comments_comment_type_id_CommentTypes",
            "CommentTypes",
            ["comment_type_id"],
            ["comment_type_id"],
            referent_schema="pepys",
        )
        batch_op.create_foreign_key(
            "fk_Comments_source_id_Datafiles",
            "Datafiles",
            ["source_id"],
            ["datafile_id"],
            referent_schema="pepys",
        )
        batch_op.create_foreign_key(
            "fk_Comments_platform_id_Platforms",
            "Platforms",
            ["platform_id"],
            ["platform_id"],
            referent_schema="pepys",
        )

    with op.batch_alter_table("Activations", schema="pepys") as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_Activations_sensor_id_Sensors"), type_="foreignkey")
        batch_op.drop_constraint(
            batch_op.f("fk_Activations_source_id_Datafiles"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("fk_Activations_privacy_id_Privacies"), type_="foreignkey"
        )
        batch_op.create_foreign_key(
            "fk_Activations_sensor_id_Sensors",
            "Sensors",
            ["sensor_id"],
            ["sensor_id"],
            referent_schema="pepys",
        )
        batch_op.create_foreign_key(
            "fk_Activations_privacy_id_Privacies",
            "Privacies",
            ["privacy_id"],
            ["privacy_id"],
            referent_schema="pepys",
        )
        batch_op.create_foreign_key(
            "fk_Activations_source_id_Datafiles",
            "Datafiles",
            ["source_id"],
            ["datafile_id"],
            referent_schema="pepys",
        )

    # ### end Alembic commands ###
