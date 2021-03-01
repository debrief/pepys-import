from asyncio import Future

from prompt_toolkit.layout.containers import HSplit, VSplit
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.widgets import Button, Label
from prompt_toolkit.widgets.dialogs import Dialog

from pepys_admin.maintenance.column_data import column_data_to_edit_data
from pepys_admin.maintenance.widgets.entry_display_widget import EntryDisplayWidget
from pepys_admin.maintenance.widgets.entry_edit_widget import EntryEditWidget


class EditDialog:
    def __init__(self, column_data, table_object, entries):
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

        # Convert the column_data into the structure we need for editing the data
        # This removes un-needed columns, and un-needed values lists
        edit_data = column_data_to_edit_data(column_data, table_object)

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
                        str(getattr(entry, field_name))
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
        self.body = HSplit(
            [instructions, selected_items_ui, VSplit([lh_side, rh_side], padding=2)], padding=1
        )

        self.dialog = Dialog(
            title="Edit item(s)",
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
        self.future.set_result(self.entry_edit_widget.output)

    def handle_cancel(self):
        self.future.set_result(None)

    def __pt_container__(self):
        return self.dialog
