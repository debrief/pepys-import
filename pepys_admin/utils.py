import os

from sqlalchemy.sql.schema import UniqueConstraint


def get_default_export_folder():
    current_folder_name = os.path.basename(os.path.normpath(os.getcwd()))
    if current_folder_name == "bin":
        return os.path.expanduser("~")
    else:
        return os.getcwd()


def sqlalchemy_obj_to_dict(obj, remove_id=False):
    """Converts a SQLAlchemy result from a query into a dict of {column_name: value}s,
    excluding the 'created_date' column
    """
    d = {column.name: getattr(obj, column.name) for column in obj.__table__.columns}

    del d["created_date"]

    if remove_id:
        pri_key_col_name = obj.__table__.primary_key.columns.values()[0].name
        del d[pri_key_col_name]

    return d


def check_sqlalchemy_results_are_equal(results1, results2):
    list1 = [sqlalchemy_obj_to_dict(item) for item in results1]
    list2 = [sqlalchemy_obj_to_dict(item) for item in results2]

    return list1 == list2


def make_query_for_cols(table_object, comparison_object, columns, session):
    """Create a SQLAlchemy query for the given table_object, with a filter comparing the given
    columns with the given comparison_object.

    For example, if the comparison object contains values
    {'name': GPS, 'host': 42, 'type':12, 'blah': 'hello},
    and the columns are ['name', 'host']
    then this will return a query like this:

    session.query(table_object).filter(table_object.name == "GPS").filter(table_object.host == 42)
    """
    query = session.query(table_object)

    for col_name in columns:
        query = query.filter(
            getattr(table_object, col_name) == getattr(comparison_object, col_name)
        )

    return query


def make_query_for_unique_cols_or_all(table_object, comparison_object, session):
    """Create a SQLAlchemy query object for the given table_object, with a filter comparing it
    to the comparison object. The filter will use just the columns defined in the unique constraint
    for the table if a unique constraint is defined, otherwise it will compare all columns.
    """
    unique_constraints = [
        c for c in table_object.__table__.constraints if isinstance(c, UniqueConstraint)
    ]

    if len(unique_constraints) == 0:
        return make_query_for_all_data_columns(table_object, comparison_object, session)
    elif len(unique_constraints) == 1:
        unique_col_names = [c.name for c in unique_constraints[0].columns]
        return make_query_for_cols(table_object, comparison_object, unique_col_names, session)


def make_query_for_all_data_columns(table_object, comparison_object, session):
    """Makes a query to search for an object where all data columns match the comparison object

    In this case, the data columns are all columns excluding the primary key and the
    created_date column.
    """
    primary_key = table_object.__table__.primary_key.columns.values()[0].name

    column_names = [col.name for col in table_object.__table__.columns.values()]

    # Get rid of the primary key column from the list
    column_names.remove(primary_key)
    # And get rid of the created_date column
    column_names.remove("created_date")
    # And get rid of the privacy column, if it exists
    if "privacy_id" in column_names:
        column_names.remove("privacy_id")

    query = session.query(table_object)

    for col_name in column_names:
        # Don't add a filter to match any columns which have missing values in the comparison object
        if getattr(comparison_object, col_name) is None:
            continue
        query = query.filter(
            getattr(table_object, col_name) == getattr(comparison_object, col_name)
        )

    return query


def table_name_to_class_name(table_name):
    if table_name.endswith("ies"):
        return table_name[:-3] + "y"
    elif table_name.endswith("s"):
        return table_name[:-1]
