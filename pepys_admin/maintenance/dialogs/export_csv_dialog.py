import os
from asyncio import Future

from prompt_toolkit.completion.filesystem import PathCompleter
from prompt_toolkit.layout.containers import HSplit, VSplit
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.widgets import Button, Label
from prompt_toolkit.widgets.base import TextArea
from prompt_toolkit.widgets.dialogs import Dialog

from pepys_admin.utils import get_default_export_folder

from ..widgets.checkbox_table import CheckboxTable


class ExportCSVDialog:
    def __init__(self, column_data):
        self.future = Future()

        ok_button = Button(text="OK", handler=self.handle_ok)
        cancel_button = Button(text="Cancel", handler=self.handle_cancel)

        avail_cols = []
        avail_cols_sys_names = []
        for human_name, data in column_data.items():
            if data["sqlalchemy_type"] == "relationship":
                continue
            # Append a list to the list, as CheckboxTable expects a list of columns to display
            avail_cols.append([human_name])
            avail_cols_sys_names.append(data["system_name"])

        avail_cols = [["Select all/none"]] + avail_cols
        avail_cols_sys_names = [None] + avail_cols_sys_names

        self.table = CheckboxTable(avail_cols, avail_cols_sys_names)

        folder_completer = PathCompleter(only_directories=True, expanduser=True)
        self.filename_textbox = TextArea(
            multiline=False,
            text=get_default_export_folder(),
            completer=folder_completer,
            complete_while_typing=True,
        )

        self.error_message = Label("", style="class:error-message")

        body = HSplit(
            [
                Label("Select the columns to export"),
                self.table,
                VSplit(
                    [Label("Export filename", dont_extend_width=True), self.filename_textbox],
                    padding=2,
                ),
                self.error_message,
            ],
            padding=1,
        )

        self.dialog = Dialog(
            title="CSV Export",
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

    def handle_ok(self):
        if len(self.table.current_values) == 0:
            self.error_message.text = "Please select at least one column to export"
            return
        else:
            self.error_message.text = ""

        if len(self.filename_textbox.text) == 0:
            self.error_message.text = "Please enter a filename"
            return
        else:
            self.error_message.text = ""

        if os.path.isdir(self.filename_textbox.text):
            self.error_message.text = "Please enter a path to a file, not a folder"
            return
        else:
            self.error_message.text = ""

        self.future.set_result(
            {"columns": self.table.current_values, "filename": self.filename_textbox.text}
        )

    def handle_cancel(self):
        self.future.set_result(None)

    def __pt_container__(self):
        return self.dialog
