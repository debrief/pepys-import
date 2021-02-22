import re


def get_display_names(fields, capitalized=False):
    """
    Takes a list of field names, and returns a list of
    nicely formatted table titles.

    """
    results = []
    for field in fields:
        field_title = get_display_name(field, capitalized)

        results.append(field_title)

    return results


def get_display_name(field, capitalized=False):
    field = re.sub("_+", "_", field)
    splitted = field.split("_")
    if len(splitted) > 1 and splitted[-1] == "name":
        # Remove 'name' from the end of the title, but only if it's
        # not the only word in the title
        field_title = " ".join(splitted[:-1])
    else:
        field_title = " ".join(splitted)

    if capitalized:
        field_title = field_title.capitalize()

    return field_title


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
