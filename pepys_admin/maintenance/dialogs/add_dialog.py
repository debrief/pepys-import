import textwrap
from asyncio import Future

from prompt_toolkit.layout.containers import HSplit
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.widgets import Button, Label
from prompt_toolkit.widgets.dialogs import Dialog

from pepys_admin.maintenance.column_data import column_data_to_edit_data
from pepys_admin.maintenance.utils import get_system_name_mappings
from pepys_admin.maintenance.widgets.entry_edit_widget import EntryEditWidget


class AddDialog:
    def __init__(self, column_data, table_object):
        """
        A dialog for adding entries to a table

        :param column_data: The column_data dictionary for the given table object
        :type column_data: dict
        :param table_object: SQLAlchemy Table object, such as Platform, Sensor or Nationality
        :type table_object: SQLAlchemy Table Object
        """
        self.future = Future()

        ok_button = Button(text="Add", handler=self.handle_ok)
        cancel_button = Button(text="Cancel", handler=self.handle_cancel)

        # Convert the column_data into the structure we need for editing the data
        # This removes un-needed columns, and un-needed values lists
        self.edit_data = column_data_to_edit_data(column_data, table_object)

        self.required_columns = set(
            [value["system_name"] for key, value in self.edit_data.items() if value["required"]]
        )

        self.entry_edit_widget = EntryEditWidget(self.edit_data, show_required_fields=True)
        self.error_message = Label("", style="class:error-message")

        instructions = Label(
            "Press TAB to move between fields. Required fields are marked with a *.",
            style="class:instruction-text-dark",
        )
        self.body = HSplit([instructions, self.entry_edit_widget, self.error_message], padding=1)

        self.dialog = Dialog(
            title=f"Add {table_object.__name__}",
            body=self.body,
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
        provided_cols = set(self.entry_edit_widget.output.keys())
        if self.required_columns.issubset(provided_cols):
            # In this case, the user has entered values for all of the required columns
            self.future.set_result(self.entry_edit_widget.output)
        else:
            # In this case they haven't, so display a sensible error message
            diff_list = self.required_columns.difference(provided_cols)

            (
                system_name_to_display_name,
                _,
            ) = get_system_name_mappings(self.edit_data)

            diff_list_display_names = sorted(
                [system_name_to_display_name[sys_name] for sys_name in diff_list]
            )
            diff_list_str = ", ".join(diff_list_display_names)

            self.error_message.text = textwrap.fill(
                f"Some required values missing: {diff_list_str}", 70
            )

    def handle_cancel(self):
        self.future.set_result(None)

    def __pt_container__(self):
        return self.dialog
