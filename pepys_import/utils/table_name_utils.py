from pepys_import.core.store import constants


def table_name_to_class_name(table_name):
    """
    Converts a table name which is plural to a singular class name.
    :param table_name: Name of a table
    :type table_name: String
    :return: Returns the singular class name
    :rtype: String
    """
    if table_name in [constants.ALEMBIC_VERSION, constants.HOSTED_BY, constants.MEDIA]:
        table = table_name
    elif table_name == constants.GEOMETRY:
        table = "Geometry1"
    elif table_name.endswith("ies"):
        table = table_name[:-3] + "y"
    else:
        table = table_name[:-1]
    return table


def find_foreign_key_table_names_recursively(table_obj, table_names):
    """
        Finds all necessary classes by running recursively on foreign keys of table_obj.

    :param table_obj: A table object from the sqlite_db
    :param table_obj: Base class
    :param table_names: A list that contains the name of the necessary tables
    :param table_names: List
    :return:
    """
    foreign_keys = list(table_obj.__table__.foreign_keys)
    if not foreign_keys:
        return table_names
    else:
        for foreign_key in foreign_keys:
            foreign_key_table = foreign_key.target_fullname.split(".")[0]
            foreign_key_table = make_table_name_singular(foreign_key_table)
            if foreign_key_table not in table_names:
                table_names.append(foreign_key_table)
                foreign_key_table_obj = getattr(sqlite_db, foreign_key_table)
                find_foreign_key_table_names_recursively(foreign_key_table_obj, table_names)
