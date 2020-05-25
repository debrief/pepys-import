import os


def get_default_export_folder():
    current_folder_name = os.path.basename(os.path.normpath(os.getcwd()))
    if current_folder_name == "bin":
        return os.path.expanduser("~")
    else:
        return os.getcwd()


def sqlalchemy_obj_to_dict(obj):
    """Converts a SQLAlchemy result from a query into a dict of {column_name: value}s,
    excluding the 'created_date' column
    """
    d = {column.name: getattr(obj, column.name) for column in obj.__table__.columns}

    del d["created_date"]

    return d


def check_sqlalchemy_results_are_equal(results1, results2):
    list1 = [sqlalchemy_obj_to_dict(item) for item in results1]
    list2 = [sqlalchemy_obj_to_dict(item) for item in results2]

    return list1 == list2


def make_query_for_all_data_columns(table_object, comparison_object, session):
    """Makes a query to search for an object where all data columns match.

    In this case, the data columns are all columns excluding the primary key and the
    created_date column.
    """
    primary_key = table_object.__table__.primary_key.columns.values()[0].name

    column_names = [col.name for col in table_object.__table__.columns.values()]

    # Get rid of the primary key column from the list
    column_names.remove(primary_key)
    # And get rid of the created_date column
    column_names.remove("created_date")

    query = session.query(table_object)

    for col_name in column_names:
        query = query.filter(
            getattr(table_object, col_name) == getattr(comparison_object, col_name)
        )

    return query
