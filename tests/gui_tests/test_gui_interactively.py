import asyncio

from prompt_toolkit.application import create_app_session
from prompt_toolkit.input.base import DummyInput
from prompt_toolkit.key_binding.key_processor import KeyPress
from prompt_toolkit.keys import Keys
from prompt_toolkit.output import DummyOutput

from pepys_admin.maintenance.dialogs.help_dialog import HelpDialog
from pepys_admin.maintenance.gui import MaintenanceGUI


class InteractiveGUITest:
    def __init__(self, datastore, show_output=False, delay=None):
        self.datastore = datastore
        self.show_output = show_output
        self.delay = delay

    async def __aenter__(self):
        input = DummyInput()
        if self.show_output:
            output = None
        else:
            output = DummyOutput()

        self.cas = create_app_session(output=output, input=input)
        self.cas.__enter__()

        self.gui = MaintenanceGUI(self.datastore)

        self.task = asyncio.create_task(self.gui.app.run_async())
        print("Created task")
        self.ready_event = asyncio.Event()
        self.gui.app.after_render += lambda _: self.ready_event.set()
        await self.ready_event.wait()
        self.ready_event.clear()
        print("Ready")

        self.progress_bar_event = asyncio.Event()
        self.gui.app.progress_bar_finished += lambda _: self.progress_bar_event.set()

        self.preview_updated = asyncio.Event()
        self.gui.app.preview_table_updated += lambda _: self.preview_updated.set()

        return self

    async def wait_for_progress_bar(self):
        self.progress_bar_event.clear()
        await self.progress_bar_event.wait()
        self.progress_bar_event.clear()

        await self.wait_for_redraw()

    async def wait_for_redraw(self):
        await self.ready_event.wait()
        self.ready_event.clear()

    async def wait_for_preview_table_update(self):
        self.preview_updated.clear()
        await self.preview_updated.wait()
        self.preview_updated.clear()

    async def send_keys(self, keys):
        if isinstance(keys, Keys):
            keys = [keys]

        for key in keys:
            print(f"Sending {key}")
            # print(f"{key}: {self.gui.app.layout.current_window.content.text()}")
            # print("----")
            self.gui.app.key_processor.feed(KeyPress(key))
            self.gui.app.key_processor.process_keys()

            await self.wait_for_redraw()

            if self.delay is not None:
                await asyncio.sleep(self.delay)

    async def __aexit__(self, exc_type, exc_value, tb):
        self.gui.app.exit()

        await self.task

        self.cas.__exit__(None, None, None)

        if exc_type is not None:
            return False
        else:
            return True


async def test_new_open_help_dialog(test_datastore):
    async with InteractiveGUITest(test_datastore, show_output=False) as gui_test:
        await gui_test.send_keys([Keys.F1])

        assert isinstance(gui_test.gui.current_dialog, HelpDialog)

        await gui_test.send_keys([Keys.Tab, Keys.ControlM])

        assert gui_test.gui.current_dialog is None


async def test_new_select_platform_type(test_datastore):
    async with InteractiveGUITest(test_datastore) as gui_test:
        await gui_test.send_keys("PlatformTy")
        await gui_test.send_keys([Keys.Enter])

        assert gui_test.gui.current_table_object == test_datastore.db_classes.PlatformType

        await gui_test.wait_for_progress_bar()

        # First entry is header, so we check 2nd entry
        assert isinstance(gui_test.gui.table_objects[1], test_datastore.db_classes.PlatformType)
        assert gui_test.gui.table_data[1] == ["Naval - aircraft"]
        # 19 entries plus a header
        assert len(gui_test.gui.table_data) == 20


async def test_tabbing(test_datastore):
    async with InteractiveGUITest(test_datastore, show_output=True, delay=0.5) as gui_test:
        await gui_test.send_keys("Plat")
        await gui_test.send_keys([Keys.Enter])

        await gui_test.send_keys([Keys.Tab])
        await gui_test.send_keys([Keys.Tab])
        await gui_test.send_keys([Keys.Tab])


async def test_filtering(test_datastore):
    async with InteractiveGUITest(test_datastore, show_output=True) as gui_test:
        await gui_test.send_keys("Plat")
        await gui_test.send_keys(Keys.Enter)

        # await gui_test.wait_for_progress_bar()

        await gui_test.send_keys(
            [
                Keys.Tab,
                Keys.Enter,
                Keys.Down,
                Keys.Enter,
                Keys.Tab,
                Keys.Tab,
                Keys.Enter,
                Keys.Down,
                Keys.Enter,
            ]
        )
        await asyncio.sleep(2)
        # await gui_test.wait_for_preview_table_update()

        assert len(gui_test.gui.table_data) == 2

    # async with create_app_and_pipe(test_datastore, show_output=True) as (inp, gui):
    #     await send_text_with_delay(inp, "Plat\r", 0.5)
    #     await asyncio.sleep(1)
    #     await send_text_with_delay(
    #         inp, ["\t", Keys.Down, Keys.Down, "\r", "\t", "\t", Keys.Down, "\r"]
    #     )

    #     assert len(gui.table_data) == 2


# async def test_open_help_dialog(test_datastore):
#     # Test application in a dummy session.
#     input = DummyInput()
#     output = DummyOutput()
#     # output = None

#     with create_app_session(output=output, input=input):
#         gui = MaintenanceGUI(test_datastore)

#         # Run the application.
#         # We run it by scheduling the run_async coroutine in the current event
#         # loop.
#         task = asyncio.create_task(gui.app.run_async())

#         ready_event = asyncio.Event()
#         gui.app.after_render += lambda _: ready_event.set()
#         await ready_event.wait()
#         ready_event.clear()
#         print("Initial ready")

#         # Send F1 to open the help dialog
#         gui.app.key_processor.feed(KeyPress(Keys.F1))
#         gui.app.key_processor.process_keys()

#         await ready_event.wait()
#         ready_event.clear()
#         print("Ready after F1")

#         # Check the help dialog has opened
#         assert isinstance(gui.current_dialog, HelpDialog)

#         # Send Tab and Enter to exit the help dialog
#         gui.app.key_processor.feed(KeyPress(Keys.Tab, "\t"))
#         gui.app.key_processor.feed(KeyPress(Keys.ControlM, "\r"))
#         gui.app.key_processor.process_keys()

#         # ready_event = asyncio.Event()
#         # gui.app.after_render += lambda _: ready_event.set()
#         await ready_event.wait()
#         ready_event.clear()
#         print("Ready after dialog exit")

#         # Check no dialog is open
#         assert gui.current_dialog is None

#         # Send ESC to open the 'Do you want to exit?' dialog
#         gui.app.key_processor.feed(KeyPress(Keys.Escape))
#         gui.app.key_processor.process_keys()

#         # ready_event = asyncio.Event()
#         # gui.app.after_render += lambda _: ready_event.set()
#         await ready_event.wait()
#         ready_event.clear()

#         gui.app.exit()

#         # Send Enter to say yes
#         # gui.app.key_processor.feed(KeyPress(Keys.ControlM, "\r"))
#         # gui.app.key_processor.process_keys()

#         # Wait for the application to properly terminate.
#         await task


# async def test_select_platform_type(test_datastore):
#     # Test application in a dummy session.
#     input = DummyInput()
#     output = DummyOutput()
#     # output = None

#     with create_app_session(output=output, input=input):
#         gui = MaintenanceGUI(test_datastore)

#         task = asyncio.create_task(gui.app.run_async())

#         ready_event = asyncio.Event()
#         gui.app.after_render += lambda _: ready_event.set()
#         await ready_event.wait()
#         ready_event.clear()

#         # Type 'PlatformTy' - which filters a dropdown box on every keypress
#         for letter in "PlatformTy":
#             gui.app.key_processor.feed(KeyPress(letter))
#             gui.app.key_processor.process_keys()

#             await ready_event.wait()
#             ready_event.clear()

#         # Send Enter to select the 'PlatformTypes' entry
#         gui.app.key_processor.feed(KeyPress(Keys.ControlM, "\r"))
#         gui.app.key_processor.process_keys()

#         await ready_event.wait()
#         ready_event.clear()

#         assert gui.current_table_object == test_datastore.db_classes.PlatformType

#         progress_bar_event = asyncio.Event()
#         gui.app.progress_bar_finished += lambda _: progress_bar_event.set()
#         await progress_bar_event.wait()
#         progress_bar_event.clear()

#         await ready_event.wait()
#         ready_event.clear()

#         # First entry is header, so we check 2nd entry
#         assert isinstance(gui.table_objects[1], test_datastore.db_classes.PlatformType)
#         assert gui.table_data[1] == ["Naval - aircraft"]
#         # 19 entries plus a header
#         assert len(gui.table_data) == 20

#         gui.app.exit()

#         # Wait for the application to properly terminate.
#         await task


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
