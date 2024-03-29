from asyncio import Future

from prompt_toolkit.layout.containers import HSplit
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.widgets import Label
from prompt_toolkit.widgets.base import Button
from prompt_toolkit.widgets.dialogs import Dialog

from pepys_admin.maintenance.widgets.combo_box import ComboBox


class MergeDialog:
    def __init__(self, title, items):
        self.future = Future()

        self.combo = ComboBox(items, enter_handler=self.handle_ok)

        cancel_button = Button(text="Cancel", handler=self.handle_cancel)

        self.dialog = Dialog(
            title=title,
            body=HSplit([Label(title + ":"), self.combo], padding=1),
            buttons=[cancel_button],
            width=D(preferred=80),
            modal=True,
        )

        # Get the keybindings for the dialog and add a binding for Esc
        # to close the dialog
        dialog_kb = self.dialog.container.container.content.key_bindings

        dialog_kb.add("escape")(lambda x: self.handle_ok(None))

    def handle_ok(self, value):
        self.future.set_result(value)

    def handle_cancel(self):
        self.future.set_result(None)

    def __pt_container__(self):
        return self.dialog
