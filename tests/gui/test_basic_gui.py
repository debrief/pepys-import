import sys

import pytest

from tests.gui.gui_test_utils import run_gui

pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="Don't run on Windows")


def test_gui_opens(pytestconfig):
    # with keep_stdin():

    capmanager = pytestconfig.pluginmanager.getplugin("capturemanager")
    capmanager.suspend_global_capture(in_=True)
    result = run_gui(print_output=True)
    capmanager.resume_global_capture()

    assert "Build filters  F3" in result
    assert "Preview List   F6" in result
    assert "Platform    ▼" in result


def test_gui_help(keep_stdin):
    with keep_stdin():
        result = run_gui(keys=b"\x1bOP")  # Escape sequence for F1

    assert "─| Help |─" in result


def test_gui_field_selection(keep_stdin):
    with keep_stdin():
        result = run_gui(keys=b"\x06")  # Escape sequence for Ctrl-F

    assert "──| Select fields |──" in result
