import json
from typing import Dict, List

import psycopg2
from psycopg2.extras import RealDictCursor

import config
from pepys_timeline.exceptions import DatabaseConnectionError, DatabaseQueryError
from pepys_timeline.queries import (
    CONFIG_OPTIONS_QUERY,
    DASHBOARD_METADATA_QUERY,
    DASHBOARD_STATS_QUERY,
)


def get_db_conn_kwargs():
    db_params = {
        "host": config.DB_HOST,
        "port": config.DB_PORT,
        "database": config.DB_NAME,
        "user": config.DB_USERNAME,
        "password": config.DB_PASSWORD,
    }
    return db_params


def get_query_result(query, vars_=None):
    db_conn_kwargs = get_db_conn_kwargs()
    try:
        with psycopg2.connect(**db_conn_kwargs) as conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as curs:
                    curs.execute(query, vars_)
                    result = curs.fetchall()
            except psycopg2.Error as e:
                raise DatabaseQueryError("Error querying database.") from e
    except psycopg2.Error as e:
        raise DatabaseConnectionError("Error connecting to database.") from e
    return result


def get_config_options():
    res = get_query_result(CONFIG_OPTIONS_QUERY)
    for row in res:
        if row["name"] == "TimelineRefreshSecs":
            row["value"] = int(row["value"])
    return res


def get_dashboard_metadata(from_date: str, to_date: str):
    return get_query_result(DASHBOARD_METADATA_QUERY, (from_date, to_date))


def get_dashboard_stats(serial_participants: List[Dict], range_types: List[str]):
    return get_query_result(
        DASHBOARD_STATS_QUERY, (json.dumps(serial_participants), json.dumps(range_types))
    )
