from asyncio import Future

from prompt_toolkit.layout.dimension import D
from prompt_toolkit.widgets import Button
from prompt_toolkit.widgets.dialogs import Dialog

from pepys_admin.maintenance.widgets.entry_display_widget import EntryDisplayWidget


class ViewDialog:
    def __init__(self, column_data, table_object, entries):
        """
        A dialog for viewing object values.

        :param column_data: The column_data dictionary for the given table object
        :type column_data: dict
        :param table_object: SQLAlchemy Table object, such as Platform, Sensor or Nationality
        :type table_object: SQLAlchemy Table Object
        :param entries: List of SQLAlchemy objects representing the objects to be edited
        :type entries: list
        """
        self.future = Future()

        ok_button = Button(text="OK", handler=self.handle_ok)

        # Use the original column_data here, rather than edit_data (as used in the EditDialog)
        # as we want to display the ID values and the created date
        self.entry_display_widget = EntryDisplayWidget(column_data, entries)

        self.dialog = Dialog(
            title=f"View {table_object.__name__} entry",
            body=self.entry_display_widget,
            buttons=[ok_button],
            width=D(preferred=100),
            modal=True,
        )

        # Get the keybindings for the dialog and add a binding for Esc
        # to close the dialog
        dialog_kb = self.dialog.container.container.content.key_bindings

        @dialog_kb.add("escape")
        def _(event) -> None:
            self.handle_ok()

    def handle_ok(self):
        self.future.set_result(None)

    def __pt_container__(self):
        return self.dialog
