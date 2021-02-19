import os
from contextlib import contextmanager

import pytest

from pepys_import.core.store.data_store import DataStore

TEST_DB_NAME = "test_gui.db"

# Not currently used
# Kept for future work in trying to not capture stdin


@pytest.fixture
def keep_stdin(pytestconfig):
    @contextmanager
    def f():
        capmanager = pytestconfig.pluginmanager.getplugin("capturemanager")
        capmanager.suspend_global_capture(in_=True)

        try:
            yield
        finally:
            capmanager.resume_global_capture()

    return f


@pytest.fixture
def test_datastore():
    if os.path.exists(TEST_DB_NAME):
        os.remove(TEST_DB_NAME)

    ds = DataStore(
        "", "", "", 0, TEST_DB_NAME, db_type="sqlite", welcome_text="", show_status=False
    )
    ds.initialise()
    with ds.session_scope():
        ds.populate_reference()
        ds.populate_metadata()

    yield ds

    if os.path.exists(TEST_DB_NAME):
        os.remove(TEST_DB_NAME)
