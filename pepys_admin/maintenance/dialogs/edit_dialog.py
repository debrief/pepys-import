from asyncio import Future

from prompt_toolkit.layout.containers import HSplit, VSplit
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.widgets import Button, Label
from prompt_toolkit.widgets.dialogs import Dialog

from pepys_admin.maintenance.utils import get_str_for_field
from pepys_admin.maintenance.widgets.entry_display_widget import EntryDisplayWidget
from pepys_admin.maintenance.widgets.entry_edit_widget import EntryEditWidget


class EditDialog:
    def __init__(self, edit_data, table_object, entries):
        """
        A dialog for editing object values.

        :param column_data: The column_data dictionary for the given table object
        :type column_data: dict
        :param table_object: SQLAlchemy Table object, such as Platform, Sensor or Nationality
        :type table_object: SQLAlchemy Table Object
        :param entries: List of SQLAlchemy objects representing the objects to be edited
        :type entries: list
        """
        self.future = Future()

        ok_button = Button(text="OK", handler=self.handle_ok)
        cancel_button = Button(text="Cancel", handler=self.handle_cancel)

        self.entry_edit_widget = EntryEditWidget(edit_data)
        self.entry_display_widget = EntryDisplayWidget(edit_data, entries)

        lh_side = HSplit(
            [Label("Current values:", style="class:table-title"), self.entry_display_widget],
            padding=1,
        )
        rh_side = HSplit(
            [Label("New values:", style="class:table-title"), self.entry_edit_widget], padding=1
        )

        instructions = Label(
            "Press TAB to move between fields. Only non-empty new values will replace current values",
            style="class:instruction-text-dark",
        )

        if len(entries) < 10:
            display_strs = []
            for entry in entries:
                display_str = " - ".join(
                    [
                        get_str_for_field(getattr(entry, field_name))
                        for field_name in entry._default_preview_fields
                    ]
                )
                display_strs.append(display_str)
            selected_items_text = "\n".join(display_strs)
        else:
            selected_items_text = f"{len(entries)} items selected"
        selected_items_ui = HSplit(
            [Label("Selected items: ", style="class:table-title"), Label(selected_items_text)]
        )

        self.error_message = Label("", style="class:error-message")

        self.body = HSplit(
            [
                instructions,
                selected_items_ui,
                VSplit([lh_side, rh_side], padding=2),
                self.error_message,
            ],
            padding=1,
        )

        self.dialog = Dialog(
            title=f"Edit {table_object.__name__}(s)",
            body=self.body,
            buttons=[ok_button, cancel_button],
            width=D(preferred=100),
            modal=True,
        )

        # Get the keybindings for the dialog and add a binding for Esc
        # to close the dialog
        dialog_kb = self.dialog.container.container.content.key_bindings

        @dialog_kb.add("escape")
        def _(event) -> None:
            self.handle_cancel()

    def handle_ok(self):
        try:
            output = self.entry_edit_widget.output
        except Exception:
            self.error_message.text = "Error converting values, please edit and try again"
            return
        self.future.set_result(output)

    def handle_cancel(self):
        self.future.set_result(None)

    def __pt_container__(self):
        return self.dialog
