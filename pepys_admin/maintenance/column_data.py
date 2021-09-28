import geoalchemy2
import sqlalchemy
from sqlalchemy import nullslast
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, TIMESTAMP, UUID

from pepys_admin.maintenance.utils import get_display_name, remove_duplicates_and_nones
from pepys_import.utils.sqlalchemy_utils import UUIDType, get_primary_key_for_table


def get_type_name(type_object):
    """Get a type name suitable for use with a FilterWidget
    from the SQLAlchemy type of a column."""
    # Check for both the SQLite UUID type or the Postgres UUID type
    if isinstance(type_object, UUIDType) or isinstance(type_object, UUID):
        return "id"
    elif isinstance(type_object, sqlalchemy.sql.sqltypes.String):
        return "string"
    elif isinstance(type_object, sqlalchemy.sql.sqltypes.DateTime) or isinstance(
        type_object, TIMESTAMP
    ):
        return "datetime"
    elif isinstance(type_object, sqlalchemy.sql.sqltypes.REAL) or isinstance(
        type_object, DOUBLE_PRECISION
    ):
        return "float"
    elif isinstance(type_object, sqlalchemy.sql.sqltypes.Integer):
        return "int"
    elif isinstance(type_object, geoalchemy2.types.Geometry):
        return "geometry"
    elif isinstance(type_object, sqlalchemy.sql.sqltypes.Boolean):
        return "bool"


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
        if isinstance(
            attr,
            (
                sqlalchemy.ext.associationproxy.ColumnAssociationProxyInstance,
                sqlalchemy.ext.associationproxy.ObjectAssociationProxyInstance,
            ),
        ):
            assoc_proxy_objs.append(attr)
            assoc_proxy_names.append(attr_name)

    return assoc_proxy_names, assoc_proxy_objs


def get_relationship_columns(table_object):
    attr_names = dir(table_object)
    rel_columns = []
    for attr_name in attr_names:
        attr = getattr(table_object, attr_name)
        try:
            if isinstance(attr.prop, sqlalchemy.orm.relationships.RelationshipProperty):
                rel_columns.append(attr_name)
        except Exception:
            pass

    return rel_columns


def str_if_not_none(value):
    """Return the string value of the argument, unless
    it is None, in which case return None"""
    if value is None:
        return None
    else:
        return str(value)


def create_assoc_proxy_data(ap_name, ap_obj, data_store, table_object):
    """Creates the column data for an association proxy column.

    :param ap_name: Association proxy name
    :type ap_name: str
    :param ap_obj: Association proxy object
    :type ap_obj: AssociationProxyInstance
    :param data_store: DataStore instance
    :type data_store: DataStore
    :param table_object: SQLAlchemy table object
    :type table_object: SQLAlchemy table object
    :return: Tuple of display name for this column, and a dictionary of column details
    :rtype: tuple (str, dict)
    """
    target_value = getattr(ap_obj.target_class, ap_obj.value_attr)
    # If the target value is _another_ association proxy, then get it's target, and continue doing this
    # until we get something that is no longer an association proxy (ie. it is a normal column or a relationship)
    while isinstance(
        target_value,
        (
            sqlalchemy.ext.associationproxy.ColumnAssociationProxyInstance,
            sqlalchemy.ext.associationproxy.ObjectAssociationProxyInstance,
        ),
    ):
        target_value = getattr(target_value.target_class, target_value.value_attr)

    # If we've got an association proxy that is pointing to a raw relationship, then return None, meaning that
    # this association proxy won't be included in the final column data list
    try:
        if isinstance(target_value.prop, sqlalchemy.orm.relationships.RelationshipProperty):
            return None, None
    except Exception:
        pass

    ap_type = target_value.type

    details = {
        "type": get_type_name(ap_type),
        "system_name": ap_name,
        "sqlalchemy_type": "assoc_proxy",
    }

    # This reflects whether the ID field for the relationship that is
    # linked to this association proxy is required or not
    relationship_name = ap_obj.target_collection
    relationship_obj = getattr(table_object, relationship_name)
    foreign_key_col_name = list(relationship_obj.property.local_columns)[0].key
    foreign_key_col = getattr(table_object, foreign_key_col_name)
    details["required"] = not foreign_key_col.prop.columns[0].nullable

    if details["type"] == "id":
        return None, None

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
            values = [str_if_not_none(getattr(record, ap_obj.value_attr)) for record in all_records]

            sorted_values = sorted(set(values))
            details["values"] = sorted_values

    return get_display_name(ap_name), details


def create_normal_column_data(col, data_store, table_object):
    """Creates the column data for a normal column (ie. not an association proxy or a relationship)

    :param col: Column name
    :type col: str
    :param data_store: DataStore
    :type data_store: DataStore
    :param table_object: SQLAlchemy table object - such as Platform or Sensor
    :type table_object: SQLAlchemy table object
    :return: Tuple of display name of the column and a dict of column details
    :rtype: tuple (str, dict)
    """
    sys_name = col.key
    # Deal with columns where the actual column member
    # variable is something like `_speed`, because we're
    # using a `speed` property to access the column
    if sys_name.startswith("_"):
        sys_name = sys_name[1:]

    details = {
        "type": get_type_name(col.type),
        "system_name": sys_name,
        "sqlalchemy_type": "column",
    }

    details["required"] = not col.prop.columns[0].nullable

    if (
        details["type"] == "id"
        and col.key != get_primary_key_for_table(table_object)
        and col.key != "entry_id"
    ):
        # Skip all ID columns except the primary key
        # Make a special exception for the entry_id field in the Extractions table
        # where there is no relationship to use to navigate between tables, as entry_id could be
        # a primary key in any measurement table
        return None, None

    # Skip getting values for the remarks column, as we don't need a dropdown for that
    if details["type"] == "string" and details["system_name"] != "remarks":
        # Get values
        # Here we query for just the specific column name (details['system_name']) so that
        # the generated SQL is just selecting that column, rather than selecting all the columns
        # and doing all the joins to get the denormalised data
        all_records = data_store.session.query(getattr(table_object, details["system_name"])).all()
        values = [str_if_not_none(record[0]) for record in all_records]
        details["values"] = sorted(remove_duplicates_and_nones(values))

    return get_display_name(sys_name), details


def create_relationship_data(rel_name, data_store, table_object):
    """Creates the column data for a relationship column.

    :param rel_name: Relationship name
    :type rel_name: str
    :param data_store: DataStore
    :type data_store: DataStore
    :param table_object: SQLAlchemy table object, like Platform or Sensor
    :type table_object: SQLAlchemy table object
    :return: Tuple of display name of the column and a dict of column details
    :rtype: tuple (str, dict)
    """
    column_config = {"system_name": rel_name, "type": "string", "sqlalchemy_type": "relationship"}

    rel = getattr(table_object, rel_name)

    if rel.info.get("skip_in_gui"):
        return None, None

    if rel.prop.secondary is not None:
        # Mark all second-level relationships so we can skip them when editing
        # Eg. this will mark State.platform, which is a relationship that passes
        # through State.sensor
        column_config["second_level"] = True
    else:
        column_config["second_level"] = False

    # Get the object for the foreign table in this relationship
    column = list(rel.prop.local_columns)[0]
    foreign_table_object = rel.prop.entity.class_

    column_config["multiple_values_allowed"] = rel.prop.uselist

    column_config["foreign_table_type"] = foreign_table_object.table_type

    with data_store.session_scope():
        # Treat Nationalities as a special case, so we can sort them the way we want
        if foreign_table_object == data_store.db_classes.Nationality:
            all_nationalities = (
                data_store.session.query(data_store.db_classes.Nationality)
                .order_by(nullslast(data_store.db_classes.Nationality.priority.asc()))
                .all()
            )
            str_entries = [nationality.name for nationality in all_nationalities]
            ids = [str(nationality.nationality_id) for nationality in all_nationalities]
        # Treat Privacies as a special case so we can sort them the way we want
        elif foreign_table_object == data_store.db_classes.Privacy:
            all_privacies = (
                data_store.session.query(data_store.db_classes.Privacy)
                .order_by(data_store.db_classes.Privacy.level)
                .all()
            )
            str_entries = [priv.name for priv in all_privacies]
            ids = [str(priv.privacy_id) for priv in all_privacies]
        else:
            all_entries = data_store.session.query(foreign_table_object).all()
            str_entries = []
            for entry in all_entries:
                field_values = [
                    str(getattr(entry, field_name))
                    for field_name in foreign_table_object._default_dropdown_fields
                ]
                str_entries.append(" / ".join(field_values))
            ids = [
                str(getattr(entry, get_primary_key_for_table(foreign_table_object)))
                for entry in all_entries
            ]

    column_config["values"] = str_entries
    column_config["ids"] = ids

    column_config["required"] = not column.nullable

    return get_display_name(rel_name), column_config


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
    relationships = get_relationship_columns(table_object)

    total_iterations = len(cols) + len(assoc_proxy_names) + len(relationships) + 1
    iteration_perc = 100.0 / total_iterations
    i = 1

    with data_store.session_scope():
        column_data = {}

        # Get details for normal columns
        for col in cols:
            display_name, details = create_normal_column_data(col, data_store, table_object)

            if display_name is not None:
                column_data[display_name] = details

            if callable(set_percentage):
                set_percentage(i * iteration_perc)
            i += 1

        # Get details for all the association proxies
        for ap_name, ap_obj in zip(assoc_proxy_names, assoc_proxy_objs):
            display_name, details = create_assoc_proxy_data(
                ap_name, ap_obj, data_store, table_object
            )

            if display_name is not None:
                column_data[display_name] = details

            if callable(set_percentage):
                set_percentage(i * iteration_perc)
            i += 1

        # Get details for all the association proxies
        for rel_name in relationships:
            display_name, details = create_relationship_data(rel_name, data_store, table_object)

            if display_name is not None:
                column_data[display_name] = details

            if callable(set_percentage):
                set_percentage(i * iteration_perc)
            i += 1

    if callable(set_percentage):
        # In case rounding errors in the iteration_perc meant that we didn't get to 100
        set_percentage(100)

    return column_data


def convert_column_data_to_edit_data(column_data, set_percentage=None):
    """
    Converts the original column_data dictionary into a dictionary of data
    for configuring the editing UI.

    :param column_data: column_data dictionary, as provided by create_column_data and used in FilterWidget
    :type column_data: dict
    :param table_object: SQLAlchemy Table object, such as Platform or Nationality
    :type table_object: SQLAlchemy Table object
    :return: Dictionary giving structure of columns for editing GUI
    :rtype: dict
    """
    edit_data = {}

    # Take the existing column_data information and process it
    # to make it the basis of the edit_data
    for key, value in column_data.items():
        if key == "created date":
            # Don't allow to edit the created date
            continue

        if key == "location":
            # Don't allow to edit location at the moment
            # as we don't have a sensible UI for doing it
            # FUTURE: Remove when we want to edit locations
            continue

        if value["type"] == "id":
            # Don't allow to edit ID columns
            continue

        if key == "wargame participations":
            # Don't allow to edit wargame participations, as joining the data
            # initially takes a long time, and slows everything down
            # This can be edited in the Tasks GUI
            continue

        if value["sqlalchemy_type"] == "relationship" and value["second_level"]:
            continue

        if value["sqlalchemy_type"] == "column":
            if "values" in value:
                # If this is a normal column (ie. not a foreign keyed column)
                # then don't provide a dropdown list
                # as we only want dropdown lists for foreign keyed columns
                del value["values"]
        elif value["sqlalchemy_type"] == "assoc_proxy":
            continue
        elif value.get("multiple_values_allowed"):
            continue

        edit_data[key] = value

    if callable(set_percentage):
        set_percentage(100)

    return edit_data
