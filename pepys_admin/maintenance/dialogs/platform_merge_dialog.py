from asyncio import Future

from loguru import logger
from prompt_toolkit.layout.containers import HSplit
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.widgets import Label
from prompt_toolkit.widgets.dialogs import Dialog

from pepys_admin.maintenance.widgets.combo_box import ComboBox


class PlatformMergeDialog:
    def __init__(self, selected_items):
        self.future = Future()

        self.combo = ComboBox(selected_items, enter_handler=self.handle_ok)

        self.dialog = Dialog(
            title="Select target platform",
            body=HSplit([Label("Select target platform:"), self.combo], padding=1),
            buttons=[],
            width=D(preferred=80),
            modal=True,
        )

    def handle_ok(self, value):
        logger.debug(value)
        self.future.set_result(value)

    def __pt_container__(self):
        return self.dialog
