import sys

import pytest

from tests.gui_tests.gui_test_utils import run_gui

pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="Don't run on Windows")


def test_gui_opens(pytestconfig):
    if pytestconfig.getoption("capture") != "no":
        pytest.skip("Skipped because pytest was not run with -s option")

    result = run_gui()

    assert "Build filters  F3" in result
    assert "Preview List   F6" in result
    assert "Platform    ▼" in result


def test_gui_help(pytestconfig):
    if pytestconfig.getoption("capture") != "no":
        pytest.skip("Skipped because pytest was not run with -s option")

    result = run_gui(keys=b"\x1bOP")  # Escape sequence for F1

    assert "─| Help |─" in result


def test_gui_field_selection(pytestconfig):
    if pytestconfig.getoption("capture") != "no":
        pytest.skip("Skipped because pytest was not run with -s option")

    result = run_gui(keys=b"\x06")  # Escape sequence for Ctrl-F

    assert "──| Select fields |──" in result
