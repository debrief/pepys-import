import os
import unittest

import pytest

from pepys_import.core.store.data_store import DataStore
from pepys_import.resolvers.constants import (
    ADD_TO_PLATFORMS,
    ADD_TO_SENSORS,
    DID_NOT_SELECT_EXISTING,
    FUZZY_SEARCH_DATAFILE_TYPE,
    FUZZY_SEARCH_NATIONALITY,
    FUZZY_SEARCH_PLATFORM,
    FUZZY_SEARCH_PLATFORM_TYPE,
    FUZZY_SEARCH_PRIVACY,
    FUZZY_SEARCH_SENSOR,
    FUZZY_SEARCH_SENSOR_TYPE,
    KEEP_PLATFORM_AS_SYNONYM,
    RESOLVE_DATAFILE,
    RESOLVE_DATAFILE_TYPE,
    RESOLVE_NATIONALITY,
    RESOLVE_PLATFORM,
    RESOLVE_PLATFORM_TYPE,
    RESOLVE_PRIVACY,
    RESOLVE_SENSOR,
    RESOLVE_SENSOR_TYPE,
)

FILE_PATH = os.path.dirname(__file__)
TEST_DATA_PATH = os.path.join(FILE_PATH, "sample_data", "csv_files")

HELP_TEXT_IDS = [
    RESOLVE_DATAFILE_TYPE,
    RESOLVE_PRIVACY,
    RESOLVE_DATAFILE,
    RESOLVE_PLATFORM,
    RESOLVE_SENSOR,
    FUZZY_SEARCH_PLATFORM,
    ADD_TO_PLATFORMS,
    ADD_TO_SENSORS,
    FUZZY_SEARCH_SENSOR,
    RESOLVE_NATIONALITY,
    RESOLVE_PLATFORM_TYPE,
    RESOLVE_SENSOR_TYPE,
    FUZZY_SEARCH_PRIVACY,
    FUZZY_SEARCH_DATAFILE_TYPE,
    FUZZY_SEARCH_PLATFORM_TYPE,
    FUZZY_SEARCH_SENSOR_TYPE,
    FUZZY_SEARCH_NATIONALITY,
    KEEP_PLATFORM_AS_SYNONYM,
    DID_NOT_SELECT_EXISTING,
]


@pytest.mark.parametrize(
    "help_id",
    HELP_TEXT_IDS,
)
def test_help_text(help_id):
    datastore = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    datastore.initialise()
    HelpText = datastore.db_classes.HelpText
    # Populate Help Text table
    with datastore.session_scope():
        datastore.populate_reference(TEST_DATA_PATH)
    # Assert that there is one entity for each help ID string
    with datastore.session_scope():
        assert datastore.session.query(HelpText).filter(HelpText.id == help_id).count() == 1


if __name__ == "__main__":
    unittest.main()
