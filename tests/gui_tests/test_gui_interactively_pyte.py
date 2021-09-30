import sys

import pytest

from tests.gui_tests.gui_test_utils import run_gui

pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="Don't run on Windows")

# These tests use the run_gui function to run the GUI in a Python terminal emulator
# (provided by the pyte package). However, this doesn't work on Windows, so all
# these tests are skipped on Windows.
# Also, these tests only work properly if pytest is run with the -s option
# that stops pytest trying to change where stdin is pointing to.
# I tried various ways to configure this programatically, and they all
# failed in various interesting and intermittent ways - so it is best
# just to run these tests with -s.
# The first few lines of each test skip the test if pytest hasn't been
# run with -s - otherwise they would fail.
# The CI configuration has been updated to do two test runs: one
# for most of the tests without -s, and then the GUI tests with -s.


def test_gui_opens(pytestconfig, test_datastore):
    if pytestconfig.getoption("capture") != "no":
        pytest.skip("Skipped because pytest was not run with -s option")

    result = run_gui(test_datastore, print_output=True)

    assert "Build filters  F3" in result
    assert "Preview List   F6" in result


def test_gui_help(pytestconfig, test_datastore):
    if pytestconfig.getoption("capture") != "no":
        pytest.skip("Skipped because pytest was not run with -s option")

    result = run_gui(test_datastore, keys=b"\x1bOP", print_output=True)  # Escape sequence for F1

    assert "─| Help |─" in result
