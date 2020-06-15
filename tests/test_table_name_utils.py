import unittest

import pytest
from sqlalchemy.ext.declarative import DeclarativeMeta

from pepys_import.core.store import sqlite_db
from pepys_import.core.store.constants import *
from pepys_import.utils.table_name_utils import (
    find_foreign_key_table_names_recursively,
    table_name_to_class_name,
)

TABLE_NAMES = [
    HOSTED_BY,
    SENSOR,
    PLATFORM,
    TASK,
    PARTICIPANT,
    DATAFILE,
    SYNONYM,
    CHANGE,
    LOG,
    EXTRACTION,
    TAG,
    TAGGED_ITEM,
    PLATFORM_TYPE,
    NATIONALITY,
    GEOMETRY_TYPE,
    GEOMETRY_SUBTYPE,
    USER,
    UNIT_TYPE,
    CLASSIFICATION_TYPE,
    CONTACT_TYPE,
    SENSOR_TYPE,
    PRIVACY,
    DATAFILE_TYPE,
    MEDIA_TYPE,
    COMMENT_TYPE,
    COMMODITY_TYPE,
    CONFIDENCE_LEVEL,
    STATE,
    CONTACT,
    ACTIVATION,
    LOGS_HOLDING,
    COMMENT,
    GEOMETRY,
    MEDIA,
]


@pytest.mark.parametrize(
    "table_name", TABLE_NAMES,
)
def test_make_table_names_singular(table_name):
    table = table_name_to_class_name(table_name)
    table_obj = getattr(sqlite_db, table)
    assert isinstance(table_obj, DeclarativeMeta) is True


@pytest.mark.parametrize(
    "table_name", ["alembic_version"],
)
def test_make_table_names_singular_alembic_version(table_name):
    table = table_name_to_class_name(table_name)
    assert table == "alembic_version"


@pytest.mark.parametrize(
    "table_name,actual_result",
    [
        (NATIONALITY, []),
        (PLATFORM, ["Privacy", "PlatformType", "Nationality"]),
        (
            STATE,
            [
                "Datafile",
                "DatafileType",
                "Privacy",
                "Sensor",
                "SensorType",
                "Platform",
                "PlatformType",
                "Nationality",
            ],
        ),
    ],
)
def test_find_foreign_key_table_names(table_name, actual_result):
    tables = list()
    table = make_table_name_singular(table_name)
    table_obj = getattr(sqlite_db, table)
    find_foreign_key_table_names_recursively(table_obj, tables)
    # They should have the same values but they might not have the same order.
    # Convert them to set and compare
    assert set(tables) == set(actual_result)


if __name__ == "__main__":
    unittest.main()
