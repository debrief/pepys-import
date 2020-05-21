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
