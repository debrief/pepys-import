import re
from collections.abc import Iterable
from datetime import datetime, timedelta
from sqlalchemy.orm.exc import DetachedInstanceError


import pint
import sqlalchemy
from sqlalchemy.dialects.postgresql import TIMESTAMP as PSQL_TIMESTAMP
from sqlalchemy.dialects.sqlite import TIMESTAMP as SQLITE_TIMESTAMP

from pepys_admin.maintenance import constants
from pepys_import.core.store.data_store import DataStore
from pepys_import.core.store.db_base import BasePostGIS, BaseSpatiaLite
from pepys_import.utils.table_name_utils import table_name_to_class_name


def empty_str_if_none(value):
    if value is None:
        return ""
    else:
        return value


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
    field_title = field.replace("_", " ")

    if capitalized:
        field_title = field_title.capitalize()

    return field_title.strip()


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
    """Removes all duplicates and None values from a list."""
    new_list = [item for item in items if item is not None]

    return list(set(new_list))


def get_str_for_field(value):
    if isinstance(value, float):
        # For floats, display to 2 decimal places
        return f"{value:.2f}"
    elif isinstance(value, pint.Quantity):
        return f"{value:~.2fP}"
    elif isinstance(value, Iterable) and not isinstance(value, str):
        return ", ".join(value)
    elif isinstance(value, BasePostGIS) or isinstance(value, BaseSpatiaLite):
        strings = [str(getattr(value, field_name)) for field_name in value._default_dropdown_fields]
        return " / ".join(strings)
    else:
        return str(value)


def create_time_filter_dict() -> dict:
    """Creates a dictionary that has the filter strings as keys, and related datetimes as values."""
    today = datetime.today()
    today_as_date = today.date()
    one_day_delta = timedelta(hours=24)
    time_filter_dict = {
        constants.DAY_BEFORE_YESTERDAY: (
            today_as_date - one_day_delta * 2,
            today_as_date - one_day_delta,
        ),
        constants.IN_PAST_24_HOURS: (today - one_day_delta, today),
        constants.YESTERDAY: (today_as_date - one_day_delta, today_as_date),
        constants.TODAY: (today_as_date, today_as_date + one_day_delta),
        constants.IN_NEXT_24_HOURS: (today, today + one_day_delta),
        constants.TOMORROW: (today_as_date + one_day_delta, today_as_date + one_day_delta * 2),
    }
    return time_filter_dict


def table_has_any_timestamp_fields(table_object) -> bool:
    """
    Returns true if there is any field of type 'TIMESTAMP'.

    :param table_object: A table object
    :type table_object: Base SQLAlchemy Model
    """
    mapper = sqlalchemy.inspect(table_object)
    for column in mapper.all_orm_descriptors:
        try:
            if isinstance(column.type, PSQL_TIMESTAMP) or isinstance(column.type, SQLITE_TIMESTAMP):
                return True
        except Exception:
            pass
    return False


def convert_relative_time_string_to_sqlalchemy_filter(
    relative_time: str, table_name: str, data_store: DataStore
):
    """
    Filters objects by given relative time and returns them.

    :param relative_time: Selected relative time in the GUI
    :type relative_time: str
    :param table_name: Name of the table
    :type table_name: str
    :param data_store: DataStore object to use to communicate with the database
    :type data_store: DataStore
    """
    class_name = table_name_to_class_name(table_name)
    class_obj = getattr(data_store.db_classes, class_name)
    if not table_has_any_timestamp_fields(class_obj):
        raise ValueError(f"This table doesn't have any type of 'time' fields: {table_name}")

    filter_dict = create_time_filter_dict()
    start, end = filter_dict.get(relative_time)
    if start is None or end is None:
        raise ValueError(f"Given relative time couldn't be converted: {relative_time}")

    if isinstance(
        class_obj,
        (
            data_store.db_classes.Series,
            data_store.db_classes.Wargame,
            data_store.db_classes.Serial,
            data_store.db_classes.SerialParticipant,
        ),
    ):
        start_field, end_field = getattr(class_obj, "start"), getattr(class_obj, "end")
    else:
        start_field, end_field = getattr(class_obj, "time"), getattr(class_obj, "time")

    # TODO: Add filtering for relative time for Series, Wargame and Serial
    return start <= start_field, end_field <= end


def trim_string(s, chars):
    if len(s) >= chars:
        return s[:chars]
    else:
        return f"{s: <{chars}}"


def load_participants_attribute(data_store, obj):
    if isinstance(obj, (data_store.db_classes.Wargame, data_store.db_classes.Serial)):
        try:
            _ = obj.participants
        except DetachedInstanceError:
            with data_store.session_scope():
                obj = data_store.session.merge(obj)
                _ = obj.participants
    
    return obj
