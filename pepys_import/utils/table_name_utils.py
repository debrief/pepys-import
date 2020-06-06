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
