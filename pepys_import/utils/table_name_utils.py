from pepys_import.core.store import sqlite_db


def make_table_name_singular(table_name):
    if table_name in ["alembic_version", "HostedBy", "Media"]:
        table = table_name
    elif table_name == "Geometries":
        table = "Geometry1"
    elif table_name.endswith("ies"):
        table = table_name[:-3] + "y"
    else:
        table = table_name[:-1]
    return table


def find_foreign_key_table_names_recursively(table_obj, table_names):
    """
        This function finds all necessary classes by running recursively on foreign keys of table_obj.

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
