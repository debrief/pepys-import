from contextlib import contextmanager

import pytest

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
