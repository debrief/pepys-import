import asyncio
from contextlib import asynccontextmanager

import pytest
from loguru import logger
from prompt_toolkit.application import create_app_session
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.input.ansi_escape_sequences import REVERSE_ANSI_SEQUENCES
from prompt_toolkit.keys import Keys
from prompt_toolkit.output import DummyOutput

from pepys_admin.maintenance.dialogs.help_dialog import HelpDialog
from pepys_admin.maintenance.gui import MaintenanceGUI

logger.add("gui.log")


@asynccontextmanager
async def create_app_and_pipe(datastore, show_output=False, autoexit=True):
    inp = create_pipe_input()
    params = {"input": inp}
    if not show_output:
        params["output"] = DummyOutput()
    print("About to create app session")
    with create_app_session(**params):
        # Create our app
        gui = MaintenanceGUI(datastore)
        print("Created app object")

        app_task = asyncio.create_task(gui.app.run_async())
        print("Ran async")
        await asyncio.sleep(2)
        print("Slept - about to yield")
        yield (inp, gui)
        print("Yielded")
        if autoexit:
            gui.app.exit()  # or: app_task.cancel()

        await app_task
        print("Finished")


async def send_text_with_delay(inp, text, delay=0.5):
    # Just a key by itself
    if isinstance(text, Keys):
        char = REVERSE_ANSI_SEQUENCES[text]
        inp.send_text(char)
        await asyncio.sleep(delay)
    # A string or a list of keys
    for char in text:
        if isinstance(char, Keys):
            char = REVERSE_ANSI_SEQUENCES[char]
        inp.send_text(char)
        await asyncio.sleep(delay)


@pytest.mark.asyncio
async def test_gui_opens(test_datastore):
    async with create_app_and_pipe(test_datastore, autoexit=False) as (inp, gui):
        await send_text_with_delay(inp, [Keys.Escape, "\r"], 1)


@pytest.mark.asyncio
async def test_select_platform_type(test_datastore):
    # Setup for our database access
    async with create_app_and_pipe(test_datastore) as (inp, gui):
        await send_text_with_delay(inp, "PlatformTy\r", 0.5)

        # Check state here.
        assert gui.current_table_object == test_datastore.db_classes.PlatformType

        # First entry is header, so we check 2nd entry
        assert isinstance(gui.table_objects[1], test_datastore.db_classes.PlatformType)
        assert gui.table_data[1] == ["Naval - aircraft"]
        # 19 entries plus a header
        assert len(gui.table_data) == 20


@pytest.mark.asyncio
async def test_show_help(test_datastore):
    async with create_app_and_pipe(test_datastore) as (inp, gui):
        # Open Help dialog
        await send_text_with_delay(inp, Keys.F1, 0.5)

        assert isinstance(gui.current_dialog, HelpDialog)

        # Tab to the close button and close dialog
        await send_text_with_delay(inp, "\t", 0.5)
        await send_text_with_delay(inp, "\r", 0.5)
        assert gui.current_dialog is None


@pytest.mark.asyncio
async def test_delete_platform_type(test_datastore):
    with test_datastore.session_scope():
        pre_count = test_datastore.session.query(test_datastore.db_classes.PlatformType).count()
        assert pre_count == 19
    # Setup for our database access
    async with create_app_and_pipe(test_datastore) as (inp, gui):
        await send_text_with_delay(inp, "PlatformTy\r", 0.5)

        await send_text_with_delay(inp, [Keys.F6, Keys.Down, " ", "4", "\r"])

        await asyncio.sleep(2)
        await send_text_with_delay(inp, "\r")

    # Should be one less PlatformType
    with test_datastore.session_scope():
        post_count = test_datastore.session.query(test_datastore.db_classes.PlatformType).count()
        assert post_count == 18

        # Should no longer have a 'Naval - aircraft' entry
        entry_count = (
            test_datastore.session.query(test_datastore.db_classes.PlatformType)
            .filter_by(name="Naval - aircraft")
            .count()
        )
        assert entry_count == 0
