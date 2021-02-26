from asyncio import Future

import sqlalchemy
from prompt_toolkit.layout.containers import HSplit, VSplit
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.widgets import Button, Label
from prompt_toolkit.widgets.dialogs import Dialog

from pepys_admin.maintenance.widgets.entry_display_widget import EntryDisplayWidget
from pepys_admin.maintenance.widgets.entry_edit_widget import EntryEditWidget


class EditDialog:
    def __init__(self, column_data, table_object, entries):
        """A dialog for editing object values.

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
        edit_data = self.column_data_to_edit_data(column_data, table_object)

        self.entry_edit_widget = EntryEditWidget(edit_data)
        self.entry_display_widget = EntryDisplayWidget(edit_data, entries)

        lh_side = HSplit([Label("Current values:"), self.entry_display_widget], padding=1)
        rh_side = HSplit([Label("New values:"), self.entry_edit_widget], padding=1)
        self.body = VSplit([lh_side, rh_side], padding=2)

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

    def column_data_to_edit_data(self, column_data, table_object):
        """Converts the original column_data dictionary into a dictionary of data
        for configuring the editing UI.

        :param column_data: column_data dictionary, as provided by create_column_data and used in FilterWidget
        :type column_data: dict
        :param table_object: SQLAlchemy Table object, such as Platform or Nationality
        :type table_object: SQLAlchemy Table object
        :return: Dictionary giving structure of columns for editing GUI
        :rtype: dict
        """
        edit_data = {}

        for key, value in column_data.items():
            if key == "created date":
                # Don't allow to edit the created date
                continue
            if value["type"] == "id":
                # Don't allow to edit ID columns
                continue
            table_attr = getattr(table_object, value["system_name"])
            if not isinstance(
                table_attr, sqlalchemy.ext.associationproxy.ColumnAssociationProxyInstance
            ):
                if "values" in value:
                    # If this isn't a foreign keyed column then don't provide a dropdown list
                    # as we only want dropdown lists for foreign keyed columns
                    del value["values"]

            edit_data[key] = value

        return edit_data

    def __pt_container__(self):
        return self.dialog
