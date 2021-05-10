import json
from typing import Dict, List

import psycopg2
from psycopg2.extras import RealDictCursor

import config
from pepys_timeline.queries import DASHBOARD_METADATA_QUERY, DASHBOARD_STATS_QUERY


def get_db_conn_kwargs():
    db_params = {
        "host": config.DB_HOST,
        "port": config.DB_PORT,
        "database": config.DB_NAME,
        "user": config.DB_USERNAME,
        "password": config.DB_PASSWORD,
    }
    return db_params


def get_dashboard_metadata(from_date: str, to_date: str):
    db_conn_kwargs = get_db_conn_kwargs()
    with psycopg2.connect(**db_conn_kwargs) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as curs:
            curs.execute(DASHBOARD_METADATA_QUERY, (from_date, to_date))
            meta = curs.fetchall()
    return meta


def get_dashboard_stats(serial_participants: List[Dict], range_types: List[str]):
    db_conn_kwargs = get_db_conn_kwargs()
    with psycopg2.connect(**db_conn_kwargs) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as curs:
            curs.execute(
                DASHBOARD_STATS_QUERY, (json.dumps(serial_participants), json.dumps(range_types))
            )
            stats = curs.fetchall()
    return stats
