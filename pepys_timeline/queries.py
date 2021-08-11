CONFIG_OPTIONS_QUERY = """select * from pepys."ConfigOptions";"""
DASHBOARD_METADATA_QUERY = "select * from pepys.dashboard_metadata(%s, %s);"
DASHBOARD_STATS_QUERY = "select * from pepys.dashboard_stats(%s, %s);"
