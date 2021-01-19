from prompt_toolkit.application.current import get_app
from prompt_toolkit.layout.containers import DynamicContainer, HorizontalAlign, HSplit, VSplit
from prompt_toolkit.validation import Validator
from prompt_toolkit.widgets.base import Button
from prompt_toolkit.widgets.toolbars import ValidationToolbar

from pepys_admin.maintenance.widgets.custom_text_area import CustomTextArea
from pepys_admin.maintenance.widgets.dropdown_box import DropdownBox


def validate_float(s):
    try:
        _ = float(s)
    except ValueError:
        return False
    return True


def validate_int(s):
    try:
        _ = int(s)
    except ValueError:
        return False
    return True


class FilterWidget:
    def __init__(self, column_data):
        self.column_data = column_data

        self.container = DynamicContainer(self.get_container_contents)
        self.button = Button("Add entry", self.add_entry)

        self.entries = [FilterWidgetEntry(self)]

    def get_container_contents(self):
        return HSplit(
            [
                HSplit([e.get_widgets() for e in self.entries], padding=1),
                self.button,
                ValidationToolbar(),
            ],
            padding=1,
        )

    def add_entry(self):
        self.entries.append(FilterWidgetEntry(self))
        get_app().layout.focus(self.entries[-1].get_widgets().get_children()[0])

    def __pt_container__(self):
        return self.container


class FilterWidgetEntry:
    def __init__(self, filter_widget):
        self.filter_widget = filter_widget
        self.dropdown_column = DropdownBox(
            text="Select column", entries=filter_widget.column_data.keys()
        )
        self.dropdown_operator = DropdownBox(text=" = ", entries=self.get_operators, filter=False)

        float_validator = Validator.from_callable(
            validate_float,
            error_message="This input is not a valid floating point value",
            move_cursor_to_end=True,
        )

        int_validator = Validator.from_callable(
            validate_int,
            error_message="This input is not a valid integer value",
            move_cursor_to_end=True,
        )

        # We have to create the widgets here in the init, or it doesn't work
        # because of some weird scoping issue
        # See https://github.com/prompt-toolkit/python-prompt-toolkit/issues/1324
        # vw = value_widget
        self.vw_text = CustomTextArea("Enter value here", multiline=False)
        self.vw_float = CustomTextArea(
            "Enter value here", multiline=False, validator=float_validator
        )
        self.vw_int = CustomTextArea("Enter value here", multiline=False, validator=int_validator)
        self.vw_dropdown = DropdownBox("Select value", entries=self.get_value_dropdown_entries)

    def get_widgets(self):
        vw = self.choose_value_widget()
        return VSplit(
            [self.dropdown_column, self.dropdown_operator, vw],
            align=HorizontalAlign.LEFT,
            padding=2,
        )

    def get_value_dropdown_entries(self):
        try:
            col_info = self.filter_widget.column_data[self.dropdown_column.text]
            col_values = col_info["values"]
            return [str(value) for value in col_values]
        except KeyError:
            return []

    def choose_value_widget(self):
        try:
            col_info = self.filter_widget.column_data[self.dropdown_column.text]
            col_type = col_info["type"]
        except KeyError:
            return self.vw_text
        if col_type == "float":
            return self.vw_float
        elif col_type == "int":
            return self.vw_int
        elif col_type == "id":
            if col_info.get("values") is not None:
                # We have a list of values, so give a dropdown
                return self.vw_dropdown
            else:
                # We don't have values, so just use a text box
                return self.vw_text
        elif col_type == "string":
            if col_info.get("values") is not None:
                # We have a list of values, so give a dropdown
                return self.vw_dropdown
            else:
                # We don't have values, so just use a text box
                return self.vw_text
        else:
            # If we don't have any idea what to do, just return a text box!
            return self.vw_text

    def get_operators(self):
        try:
            col_info = self.filter_widget.column_data[self.dropdown_column.text]
            col_type = col_info["type"]
        except KeyError:
            return []
        return self.get_operators_for_column_type(col_type)

    def get_operators_for_column_type(self, col_type):
        if col_type == "string":
            return ["=", "!=", "LIKE"]
        elif col_type == "id":
            return ["="]
        elif col_type == "float":
            return ["=", "!=", ">", "<", ">=", "<="]
        elif col_type == "datetime":
            return ["=", "!=", ">", "<", ">=", "<="]
        else:
            return []
