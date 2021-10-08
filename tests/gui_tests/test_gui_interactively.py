import asyncio

from prompt_toolkit.application import create_app_session
from prompt_toolkit.input.base import DummyInput
from prompt_toolkit.key_binding.key_processor import KeyPress
from prompt_toolkit.keys import Keys
from prompt_toolkit.output import DummyOutput

from pepys_admin.maintenance.dialogs.help_dialog import HelpDialog
from pepys_admin.maintenance.gui import MaintenanceGUI

# @asynccontextmanager
# async def create_app_and_pipe(datastore, show_output=False):
#     inp = create_pipe_input()
#     params = {"input": inp}
#     if not show_output:
#         params["output"] = DummyOutput()
#     with create_app_session(**params):
#         # Create our app
#         gui = MaintenanceGUI(datastore)

#         app_task = asyncio.create_task(gui.app.run_async())
#         await asyncio.sleep(2)

#         yield (inp, gui)

#         gui.app.exit()  # or: app_task.cancel()

#         await app_task


# async def send_text_with_delay(inp, text, delay=0.5):
#     # Just a key by itself
#     if isinstance(text, Keys):
#         char = REVERSE_ANSI_SEQUENCES[text]
#         inp.send_text(char)
#         await asyncio.sleep(delay)
#     # A string or a list of keys
#     for char in text:
#         if isinstance(char, Keys):
#             char = REVERSE_ANSI_SEQUENCES[char]
#         inp.send_text(char)
#         await asyncio.sleep(delay)


# # async def test_select_platform_type(test_datastore):
# #     # Setup for our database access
# #     async with create_app_and_pipe(test_datastore) as (inp, gui):
# #         await send_text_with_delay(inp, "PlatformTy\r", 0.5)

# #         # Check state here.
# #         assert gui.current_table_object == test_datastore.db_classes.PlatformType

# # # First entry is header, so we check 2nd entry
# # assert isinstance(gui.table_objects[1], test_datastore.db_classes.PlatformType)
# # assert gui.table_data[1] == ["Naval - aircraft"]
# # # 19 entries plus a header
# # assert len(gui.table_data) == 20


async def test_open_help_dialog(test_datastore):
    # Test application in a dummy session.
    input = DummyInput()
    output = DummyOutput()
    # output = None

    with create_app_session(output=output, input=input):
        gui = MaintenanceGUI(test_datastore)

        # Run the application.
        # We run it by scheduling the run_async coroutine in the current event
        # loop.
        task = asyncio.create_task(gui.app.run_async())

        ready_event = asyncio.Event()
        gui.app.after_render += lambda _: ready_event.set()
        await ready_event.wait()
        ready_event.clear()

        # Send F1 to open the help dialog
        gui.app.key_processor.feed(KeyPress(Keys.F1))
        gui.app.key_processor.process_keys()

        await ready_event.wait()
        ready_event.clear()

        # Check the help dialog has opened
        assert isinstance(gui.current_dialog, HelpDialog)

        # Send Tab and Enter to exit the help dialog
        gui.app.key_processor.feed(KeyPress(Keys.Tab, "\t"))
        gui.app.key_processor.feed(KeyPress(Keys.ControlM, "\r"))
        gui.app.key_processor.process_keys()

        # ready_event = asyncio.Event()
        # gui.app.after_render += lambda _: ready_event.set()
        await ready_event.wait()
        ready_event.clear()

        # Check no dialog is open
        assert gui.current_dialog is None

        # Send ESC to open the 'Do you want to exit?' dialog
        gui.app.key_processor.feed(KeyPress(Keys.Escape))
        gui.app.key_processor.process_keys()

        # ready_event = asyncio.Event()
        # gui.app.after_render += lambda _: ready_event.set()
        await ready_event.wait()
        ready_event.clear()

        # Send Enter to say yes
        gui.app.key_processor.feed(KeyPress(Keys.ControlM, "\r"))
        gui.app.key_processor.process_keys()

        # Wait for the application to properly terminate.
        await task


async def test_select_platform_type(test_datastore):
    # Test application in a dummy session.
    input = DummyInput()
    output = DummyOutput()
    # output = None

    with create_app_session(output=output, input=input):
        gui = MaintenanceGUI(test_datastore)

        task = asyncio.create_task(gui.app.run_async())

        ready_event = asyncio.Event()
        gui.app.after_render += lambda _: ready_event.set()
        await ready_event.wait()
        ready_event.clear()

        # Type 'PlatformTy' - which filters a dropdown box on every keypress
        for letter in "PlatformTy":
            gui.app.key_processor.feed(KeyPress(letter))
            gui.app.key_processor.process_keys()

            await ready_event.wait()
            ready_event.clear()

        # Send Enter to select the 'PlatformTypes' entry
        gui.app.key_processor.feed(KeyPress(Keys.ControlM, "\r"))
        gui.app.key_processor.process_keys()

        await ready_event.wait()
        ready_event.clear()

        assert gui.current_table_object == test_datastore.db_classes.PlatformType

        # Send Enter to say yes
        gui.app.exit()

        # Wait for the application to properly terminate.
        await task


# async def test_show_help(test_datastore):
#     async with create_app_and_pipe(test_datastore) as (inp, gui):
#         # Open Help dialog
#         await send_text_with_delay(inp, Keys.F1, 0.5)

#         assert isinstance(gui.current_dialog, HelpDialog)

#         # Tab to the close button and close dialog
#         await send_text_with_delay(inp, "\t", 0.5)
#         await send_text_with_delay(inp, "\r", 0.5)
#         assert gui.current_dialog is None


# async def test_filtering(test_datastore):
#     async with create_app_and_pipe(test_datastore, show_output=True) as (inp, gui):
#         await send_text_with_delay(inp, "Plat\r", 0.5)
#         await asyncio.sleep(1)
#         await send_text_with_delay(
#             inp, ["\t", Keys.Down, Keys.Down, "\r", "\t", "\t", Keys.Down, "\r"]
#         )

#         assert len(gui.table_data) == 2


# async def test_filtering_no_show_output(test_datastore):
#     async with create_app_and_pipe(test_datastore, show_output=False) as (inp, gui):
#         await send_text_with_delay(inp, "Plat\r", 0.5)
#         await asyncio.sleep(1)
#         await send_text_with_delay(
#             inp, ["\t", Keys.Down, Keys.Down, "\r", "\t", "\t", Keys.Down, "\r"]
#         )

#         assert len(gui.table_data) == 2


# async def test_delete_platform_type(test_datastore):
#     with test_datastore.session_scope():
#         pre_count = test_datastore.session.query(test_datastore.db_classes.PlatformType).count()
#         assert pre_count == 19

#     async with create_app_and_pipe(test_datastore) as (inp, gui):
#         await send_text_with_delay(inp, "PlatformTy\r", 0.5)

#         await asyncio.sleep(1)

#         await send_text_with_delay(inp, [Keys.F6, Keys.Down, " ", "4", "\r"])

#         await asyncio.sleep(20)
#         await send_text_with_delay(inp, "\r")

#     with open("gui.log") as f:
#         print(f.read())

#     # Should be one less PlatformType
#     with test_datastore.session_scope():
#         post_count = test_datastore.session.query(test_datastore.db_classes.PlatformType).count()
#         assert post_count == 18

#         # Should no longer have a 'Naval - aircraft' entry
#         entry_count = (
#             test_datastore.session.query(test_datastore.db_classes.PlatformType)
#             .filter_by(name="Naval - aircraft")
#             .count()
#         )
#         assert entry_count == 0


# async def test_select_plat_type(test_datastore):
#     async with create_app_and_pipe(test_datastore) as (inp, gui):
#         await send_text_with_delay(inp, "PlatformTy\r", 0.5)

#         assert gui.current_table_object == test_datastore.db_classes.PlatformType

#         # First entry is header, so we check 2nd entry
#         assert isinstance(gui.table_objects[1], test_datastore.db_classes.PlatformType)
#         assert gui.table_data[1] == ["Naval - aircraft"]
#         # 19 entries plus a header
#         assert len(gui.table_data) == 20
