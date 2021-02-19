import re

import geoalchemy2
import sqlalchemy
from sqlalchemy import nullslast

import pepys_import
from pepys_admin.maintenance.utils import remove_duplicates_and_nones


def get_type_name(type_object):
    """Get a type name suitable for use with a FilterWidget
    from the SQLAlchemy type of a column."""
    if isinstance(type_object, pepys_import.utils.sqlalchemy_utils.UUIDType):
        return "id"
    elif isinstance(type_object, sqlalchemy.sql.sqltypes.String):
        return "string"
    elif isinstance(type_object, sqlalchemy.sql.sqltypes.DateTime):
        return "datetime"
    elif isinstance(type_object, sqlalchemy.sql.sqltypes.REAL):
        return "float"
    elif isinstance(type_object, sqlalchemy.sql.sqltypes.Integer):
        return "int"
    elif isinstance(type_object, geoalchemy2.types.Geometry):
        return "geometry"


def get_normal_column_objects(table_object):
    """Get a list of 'normal' columns from a SQLAlchemy Table object.

    This does not include defined relationships or association_proxies,
    but includes all normally-defined columns.
    """
    mapper = sqlalchemy.inspect(table_object)
    just_cols = []
    for column in mapper.all_orm_descriptors:
        try:
            # Try accessing column.type to see if it exists
            # If it doesn't then we'll jump to the exception
            # handler, and therefore not add it to the list
            _ = column.type
            just_cols.append(column)
        except Exception:
            pass

    return just_cols


def get_assoc_proxy_names_and_objects(table_object):
    """Get association proxies defined on the given table_object,
    both as a string name and an object representing the proxy.
    """
    attr_names = dir(table_object)
    assoc_proxy_objs = []
    assoc_proxy_names = []
    for attr_name in attr_names:
        if attr_name.startswith("_"):
            continue
        attr = getattr(table_object, attr_name)
        if isinstance(attr, sqlalchemy.ext.associationproxy.ColumnAssociationProxyInstance):
            assoc_proxy_objs.append(attr)
            assoc_proxy_names.append(attr_name)

    return assoc_proxy_names, assoc_proxy_objs


def get_display_name(system_name):
    """Get a display name from a system name, by replacing
    any number of _'s with spaces"""
    display_name = re.sub("_+", " ", system_name)

    return display_name


def str_if_not_none(value):
    """Return the string value of the argument, unless
    it is None, in which case return None"""
    if value is None:
        return None
    else:
        return str(value)


def create_column_data(data_store, table_object, set_percentage=None):
    """Create column data suitable for use in a FilterWidget.

    :param data_store: DataStore object to use to communicate with the database
    :type data_store: DataStore
    :param table_object: Table object (such as data_store.db_classes.Platform) for the table
    to create the column data for
    :type table_object: SQLAlchemy Table object
    :param set_percentage: Function to call to set percentage complete, used for displaying a progress
    bar when used in the GUI, defaults to None
    :type set_percentage: Callable, optional
    :return: Column data structure
    :rtype: Dict
    """
    cols = get_normal_column_objects(table_object)
    assoc_proxy_names, assoc_proxy_objs = get_assoc_proxy_names_and_objects(table_object)

    total_iterations = len(cols) + len(assoc_proxy_names) + 1
    iteration_perc = 100.0 / total_iterations
    i = 1

    with data_store.session_scope():
        column_data = {}
        for col in cols:
            sys_name = col.key
            # Deal with columns where the actual column member
            # variable is something like `_speed`, because we're
            # using a `speed` property to access the column
            if sys_name.startswith("_"):
                sys_name = sys_name[1:]

            details = {"type": get_type_name(col.type), "system_name": sys_name}

            if details["type"] == "string":
                # Get values

                all_records = data_store.session.query(table_object).all()
                values = [
                    str_if_not_none(getattr(record, details["system_name"]))
                    for record in all_records
                ]
                details["values"] = sorted(remove_duplicates_and_nones(values))

            column_data[get_display_name(sys_name)] = details

            if callable(set_percentage):
                set_percentage(i * iteration_perc)
            i += 1

        for ap_name, ap_obj in zip(assoc_proxy_names, assoc_proxy_objs):
            ap_type = getattr(ap_obj.target_class, ap_obj.value_attr).type

            details = {"type": get_type_name(ap_type), "system_name": ap_name}

            if details["type"] == "string":
                if details["system_name"] == "nationality_name":
                    # Get nationality names as a special case, as we want to sort by
                    # priority

                    # nullslast in the expression below makes NULL entries appear at the end
                    # of the sorted list - if we don't have this then they sort as 'zero'
                    # and come before the prioritised ones
                    all_nationalities = (
                        data_store.session.query(data_store.db_classes.Nationality)
                        .order_by(nullslast(data_store.db_classes.Nationality.priority.asc()))
                        .all()
                    )
                    nationality_names = [nationality.name for nationality in all_nationalities]
                    details["values"] = nationality_names
                elif details["system_name"] == "privacy_name":
                    # Get privacy names as a special case, as we want to sort by level
                    all_privacies = (
                        data_store.session.query(data_store.db_classes.Privacy)
                        .order_by(data_store.db_classes.Privacy.level)
                        .all()
                    )
                    privacy_names = [priv.name for priv in all_privacies]
                    details["values"] = privacy_names
                else:
                    # For all other columns, no special processing is needed
                    all_records = data_store.session.query(ap_obj.target_class).all()
                    values = [
                        str_if_not_none(getattr(record, ap_obj.value_attr))
                        for record in all_records
                    ]
                    details["values"] = sorted(remove_duplicates_and_nones(values))

            column_data[get_display_name(ap_name)] = details

            if callable(set_percentage):
                set_percentage(i * iteration_perc)
            i += 1

    if callable(set_percentage):
        # In case rounding errors in the iteration_perc meant that we didn't get to 100
        set_percentage(100)

    return column_data
