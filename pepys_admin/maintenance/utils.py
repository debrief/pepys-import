import sqlalchemy
from sqlalchemy import nullslast


def get_table_titles(fields):
    """
    Takes a list of field names, and returns a list of
    nicely formatted table titles.

    """
    results = []
    for field in fields:
        splitted = field.split("_")
        if len(splitted) > 1 and splitted[-1] == "name":
            # Remove 'name' from the end of the title, but only if it's
            # not the only word in the title
            field_title = " ".join(splitted[:-1])
        else:
            field_title = " ".join(splitted)

        results.append(field_title.capitalize())

    return results


def get_system_name_mappings(column_data):
    """
    Given a column_data dict, get dicts mapping the system_name
    to the display name, and vice versa.
    """
    system_name_to_display_name = {}
    display_name_to_system_name = {}

    for key, entry in column_data.items():
        if entry.get("system_name", None) is not None:
            system_name = entry.get("system_name")
        else:
            system_name = key

        system_name_to_display_name[system_name] = key
        display_name_to_system_name[key] = system_name

    return system_name_to_display_name, display_name_to_system_name


def remove_duplicates_and_nones(items):
    """Removes all duplicates and None values from a list"""
    new_list = [item for item in items if item is not None]

    return list(set(new_list))


def create_column_data(data_store):
    """Creates the column_data needed for the FilterWidget.

    At the moment this is hard-coded to be the column data for
    the Platforms table, with database queries being used to populate
    the 'values' entry in the dict."""
    Platform = data_store.db_classes.Platform
    Nationality = data_store.db_classes.Nationality
    PlatformType = data_store.db_classes.PlatformType
    Privacy = data_store.db_classes.Privacy
    try:
        with data_store.session_scope():
            all_platforms = data_store.session.query(Platform).all()

            platform_ids = [str(platform.platform_id) for platform in all_platforms]
            platform_names = [platform.name for platform in all_platforms]
            platform_identifiers = [platform.identifier for platform in all_platforms]
            platform_trigraphs = [platform.trigraph for platform in all_platforms]
            platform_quadgraphs = [platform.quadgraph for platform in all_platforms]

            # nullslast in the expression below makes NULL entries appear at the end
            # of the sorted list - if we don't have this then they sort as 'zero'
            # and come before the prioritised ones
            all_nationalities = (
                data_store.session.query(Nationality)
                .order_by(nullslast(Nationality.priority.asc()))
                .all()
            )
            nationality_names = [nationality.name for nationality in all_nationalities]

            all_platform_types = data_store.session.query(PlatformType).all()
            platform_type_names = [pt.name for pt in all_platform_types]

            all_privacies = data_store.session.query(Privacy).order_by(Privacy.level).all()
            privacy_names = [priv.name for priv in all_privacies]
    except sqlalchemy.exc.OperationalError:
        raise Exception("Database not initialised error")

    platform_column_data = {
        "platform_id": {"type": "id", "values": platform_ids},
        "name": {
            "type": "string",
            "values": sorted(remove_duplicates_and_nones(platform_names)),
        },
        "identifier": {
            "type": "string",
            "values": sorted(remove_duplicates_and_nones(platform_identifiers)),
        },
        "trigraph": {
            "type": "string",
            "values": sorted(remove_duplicates_and_nones(platform_trigraphs)),
        },
        "quadgraph": {
            "type": "string",
            "values": sorted(remove_duplicates_and_nones(platform_quadgraphs)),
        },
        "nationality name": {
            "type": "string",
            "system_name": "nationality_name",
            "values": nationality_names,
        },
        "platform type name": {
            "type": "string",
            "system_name": "platform_type_name",
            "values": platform_type_names,
        },
        "privacy name": {
            "type": "string",
            "system_name": "privacy_name",
            "values": privacy_names,
        },
    }

    return platform_column_data
