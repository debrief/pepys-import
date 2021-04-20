from pepys_import.core.store import constants


def table_name_to_class_name(table_name):
    """
    Converts a table name which is plural to a singular class name.
    :param table_name: Name of a table
    :type table_name: String
    :return: Returns the singular class name
    :rtype: String
    """
    if table_name in [
        constants.ALEMBIC_VERSION,
        constants.HOSTED_BY,
        constants.MEDIA,
        constants.SERIES,
    ]:
        table = table_name
    elif table_name == constants.GEOMETRY:
        table = "Geometry1"
    elif table_name.endswith("ies"):
        table = table_name[:-3] + "y"
    else:
        table = table_name[:-1]
    return table
