from prompt_toolkit.layout.containers import HorizontalAlign, HSplit, VSplit
from prompt_toolkit.layout.scrollable_pane import ScrollablePane
from prompt_toolkit.widgets.base import Label

from pepys_admin.maintenance.utils import get_system_name_mappings
from pepys_admin.maintenance.widgets.custom_text_area import CustomTextArea
from pepys_admin.maintenance.widgets.dropdown_box import DropdownBox
from pepys_admin.maintenance.widgets.utils import float_validator, int_validator

PROMPT = "Enter new value"


class EntryEditWidget:
    def __init__(self, edit_data):
        """
        Widget for editing table data.

        :param edit_data: Dictionary giving data structure of columns to edit
        :type edit_data: dict
        """
        self.edit_data = edit_data

        max_label_len = max([len(key) for key, value in edit_data.items()])
        edit_width = 30
        self.entry_rows = [
            EntryEditWidgetRow(key, value, max_label_len + 1, edit_width)
            for key, value in edit_data.items()
        ]

        self.widgets = [row.get_widgets() for row in self.entry_rows]

        self.container = ScrollablePane(content=HSplit(self.widgets, padding=1))

    @property
    def output(self):
        """
        Output of the editing, showing which fields are to be edited, and what the new values are

        :return: Dictionary where keys are fields to be edited, and values are new values
        :rtype: dict
        """
        output = {}
        (
            _,
            display_name_to_system_name,
        ) = get_system_name_mappings(self.edit_data)

        for row in self.entry_rows:
            if row.value_widget.text != PROMPT:
                system_name = display_name_to_system_name[row.display_name]
                output[system_name] = row.get_value()

        return output

    def __pt_container__(self):
        return self.container


class EntryEditWidgetRow:
    def __init__(self, display_name, col_config, label_width, edit_width):
        """
        Representation of a row in the EntryEditWidget. Each of these rows
        is for editing a single column.

        :param display_name: Display name for the row (used in the label)
        :type display_name: str
        :param col_config: Column configuration dictionary - this is a single entry
        from the edit_data dictionary
        :type col_config: dict
        :param label_width: Width for the label
        :type label_width: int
        :param edit_width: Width for the value editing widget (eg. TextArea or DropdownBox)
        :type edit_width: int
        """
        self.display_name = display_name
        self.label_width = label_width
        self.col_config = col_config
        self.value_ids = None

        if col_config["type"] == "float":
            self.value_widget = CustomTextArea(
                PROMPT,
                multiline=False,
                validator=float_validator,
                focus_on_click=True,
                width=edit_width,
            )
        elif col_config["type"] == "int":
            self.value_widget = CustomTextArea(
                PROMPT,
                multiline=False,
                validator=int_validator,
                focus_on_click=True,
                width=edit_width,
            )
        elif col_config["type"] == "string":
            if "values" in col_config:
                # A list of values, so use a dropdown
                self.value_widget = DropdownBox(
                    PROMPT,
                    entries=col_config["values"],
                    width=edit_width,
                )
                if "ids" in col_config:
                    self.value_ids = col_config["ids"]
                else:
                    self.value_ids = None
            else:
                self.value_widget = CustomTextArea(
                    PROMPT,
                    multiline=False,
                    focus_on_click=True,
                    width=edit_width,
                )
        else:
            # Fall back on a text area if we don't know what to do
            self.value_widget = CustomTextArea(
                PROMPT,
                multiline=False,
                focus_on_click=True,
                width=edit_width,
            )

    def get_value(self):
        """
        Gets the value of this edit row, looking up the ID for the selected dropdown entry
        if necessary.

        :return: Value or ID
        :rtype: str
        """
        if self.value_ids is not None:
            index = self.col_config["values"].index(self.value_widget.text)
            return self.value_ids[index]
        else:
            return self.value_widget.text

    def get_widgets(self):
        """Gets the widgets to display this row

        :return: VSplit object, containing the relevant widgets
        :rtype: VSplit object
        """
        return VSplit(
            [
                Label(self.display_name, width=self.label_width),
                Label(" = ", width=3),
                self.value_widget,
            ],
            align=HorizontalAlign.LEFT,
        )
