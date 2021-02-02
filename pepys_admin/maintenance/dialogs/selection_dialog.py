from asyncio import Future

from prompt_toolkit.application.current import get_app
from prompt_toolkit.layout.containers import HSplit, VSplit
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.widgets import Button, Label
from prompt_toolkit.widgets.dialogs import Dialog

from ..widgets.combo_box import ComboBox


class SelectionDialog:
    def __init__(self, values_left, values_right, title):
        self.future = Future()

        ok_button = Button(text="OK", handler=self.handle_ok)
        cancel_button = Button(text="Cancel", handler=self.handle_cancel)

        self.left_list = ComboBox(values_left, enter_handler=self.move_from_left, height=10)
        self.right_list = ComboBox(values_right, enter_handler=self.move_from_right, height=10)

        body = HSplit(
            [
                Label(
                    "Press TAB or arrow keys to move between lists, and Enter to move an item to the other list"
                ),
                VSplit(
                    [
                        HSplit([Label("Available fields:"), self.left_list], padding=1),
                        HSplit([Label("Selected fields:"), self.right_list], padding=1),
                    ],
                    padding=2,
                ),
            ],
            padding=1,
        )

        self.dialog = Dialog(
            title=title,
            body=body,
            buttons=[ok_button, cancel_button],
            width=D(preferred=80),
            modal=True,
        )

        # Get the keybindings for the dialog and add a binding for Esc
        # to close the dialog
        dialog_kb = self.dialog.container.container.content.key_bindings

        @dialog_kb.add("escape")
        def _(event) -> None:
            self.handle_cancel()

        @dialog_kb.add("right")
        def _(event):
            app = get_app()
            app.layout.focus(self.right_list)

        @dialog_kb.add("left")
        def _(event):
            app = get_app()
            app.layout.focus(self.left_list)

    def move_from_left(self, value):
        # Remove from left-hand list
        del self.left_list.entries[self.left_list.selected_entry]

        if self.left_list.selected_entry > len(self.left_list.entries) - 1:
            self.left_list.selected_entry = len(self.left_list.entries) - 1

        # Add to right-hand list
        self.right_list.entries.append(value)
        self.right_list.selected_entry = self.right_list.entries.index(value)

    def move_from_right(self, value):
        # Remove from left-hand list
        del self.right_list.entries[self.right_list.selected_entry]

        if self.right_list.selected_entry > len(self.right_list.entries) - 1:
            self.right_list.selected_entry = len(self.right_list.entries) - 1

        # Add to right-hand list
        self.left_list.entries.append(value)
        self.left_list.selected_entry = self.left_list.entries.index(value)

    def handle_ok(self):
        self.future.set_result(self.right_list.entries)

    def handle_cancel(self):
        self.future.set_result(None)

    def __pt_container__(self):
        return self.dialog
