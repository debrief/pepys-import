import unittest

import pytest
from sqlalchemy.orm import DeclarativeMeta

from pepys_import.core.store import sqlite_db
from pepys_import.core.store.constants import (
    ACTIVATION,
    CHANGE,
    CLASSIFICATION_TYPE,
    COMMENT,
    COMMENT_TYPE,
    COMMODITY_TYPE,
    CONFIDENCE_LEVEL,
    CONTACT,
    CONTACT_TYPE,
    DATAFILE,
    DATAFILE_TYPE,
    EXTRACTION,
    GEOMETRY,
    GEOMETRY_SUBTYPE,
    GEOMETRY_TYPE,
    HOSTED_BY,
    LOG,
    LOGS_HOLDING,
    MEDIA,
    MEDIA_TYPE,
    NATIONALITY,
    PLATFORM,
    PLATFORM_TYPE,
    PRIVACY,
    SENSOR,
    SENSOR_TYPE,
    SERIAL,
    SERIAL_PARTICIPANT,
    SERIES,
    STATE,
    SYNONYM,
    TAG,
    TAGGED_ITEM,
    UNIT_TYPE,
    USER,
    WARGAME,
    WARGAME_PARTICIPANT,
)
from pepys_import.utils.table_name_utils import table_name_to_class_name

TABLE_NAMES = [
    HOSTED_BY,
    SENSOR,
    PLATFORM,
    DATAFILE,
    SERIES,
    WARGAME,
    SERIAL,
    SERIAL_PARTICIPANT,
    WARGAME_PARTICIPANT,
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
    "table_name",
    TABLE_NAMES,
)
def test_make_table_names_singular(table_name):
    table = table_name_to_class_name(table_name)
    table_obj = getattr(sqlite_db, table)
    assert isinstance(table_obj, DeclarativeMeta) is True


@pytest.mark.parametrize(
    "table_name",
    ["alembic_version"],
)
def test_make_table_names_singular_alembic_version(table_name):
    table = table_name_to_class_name(table_name)
    assert table == "alembic_version"


if __name__ == "__main__":
    unittest.main()
