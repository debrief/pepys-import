import sys

import pytest

from tests.gui.gui_test_utils import run_gui

pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="Don't run on Windows")
pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="Don't run on Windows")


def test_gui_opens():
    result = run_gui(print_output=True)

    assert "Build filters  F3" in result
    assert "Preview List   F6" in result
    assert "Platform    ▼" in result


def test_gui_help():
    result = run_gui(keys=b"\x1bOP")  # Escape sequence for F1

    assert "─| Help |─" in result


def test_gui_field_selection():
    result = run_gui(keys=b"\x06")  # Escape sequence for Ctrl-F

    assert "──| Select fields |──" in result
