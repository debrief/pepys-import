from prompt_toolkit.layout.containers import DynamicContainer, HorizontalAlign, HSplit, VSplit
from prompt_toolkit.widgets.base import Button, TextArea

from pepys_admin.maintenance.widgets.dropdown_box import DropdownBox


class FilterWidget:
    def __init__(self, column_data):
        self.column_data = column_data

        self.container = DynamicContainer(self.get_container_contents)
        self.button = Button("Add entry", self.add_entry)

        self.entries = [FilterWidgetEntry(self)]

    def get_container_contents(self):
        return HSplit([HSplit([e.get_widgets() for e in self.entries]), self.button])

    def add_entry(self):
        self.entries.append(FilterWidgetEntry(self))

    def __pt_container__(self):
        return self.container


class FilterWidgetEntry:
    def __init__(self, filter_widget):
        self.filter_widget = filter_widget
        self.dropdown_column = DropdownBox(
            text="Select column", entries=filter_widget.column_data.keys()
        )
        self.dropdown_operator = DropdownBox(text=" = ", entries=self.get_operators, filter=False)
        # We have to create the widgets here in the init, or it doesn't work
        # because of some weird scoping issue
        # See https://github.com/prompt-toolkit/python-prompt-toolkit/issues/1324
        self.value_widget1 = TextArea("Text VW", multiline=False)
        self.value_widget2 = TextArea("Numeric VW", multiline=False)
        self.value_dropdown = DropdownBox("Select value", entries=self.get_value_dropdown_entries)

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
            return self.value_widget1
        if col_type == "float":
            return self.value_widget2
        elif col_type == "id":
            return self.value_dropdown
        else:
            return self.value_widget1

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
