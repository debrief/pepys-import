from prompt_toolkit.application.current import get_app
from prompt_toolkit.layout.containers import DynamicContainer, HorizontalAlign, HSplit, VSplit
from prompt_toolkit.widgets.base import Button
from prompt_toolkit.widgets.toolbars import ValidationToolbar

from pepys_admin.maintenance.widgets.custom_text_area import CustomTextArea
from pepys_admin.maintenance.widgets.dropdown_box import DropdownBox
from pepys_admin.maintenance.widgets.masked_input_widget import MaskedInputWidget
from pepys_admin.maintenance.widgets.utils import (
    datetime_validator,
    float_validator,
    int_validator,
    interleave_lists,
)


class FilterWidget:
    def __init__(self, column_data=None, on_change_handler=None):
        self.column_data = column_data
        self.on_change_handler = on_change_handler

        # We can handle None for column_data if we turn it into an
        # empty dict, as all the dropdowns just default to not having
        # any entries
        if self.column_data is None:
            self.column_data = {}

        # For consistency, keep these here, and reference them in the widgets
        # so we only have to change them in one place
        self.column_prompt = "Select column"
        self.value_prompt = "Enter value here"

        self.container = DynamicContainer(self.get_container_contents)
        self.button = Button("Add filter condition", self.add_entry)

        # Start with one entry and no boolean operators
        self.entries = [FilterWidgetEntry(self)]
        self.boolean_operators = []

    def trigger_on_change(self, event=None):
        """Triggers the on_change_handler, if it is defined"""
        if self.on_change_handler is not None:
            self.on_change_handler(self.filters)

    def set_column_data(self, column_data):
        """Updates the column_data, and removes all the filter entries
        so we can start again with a new table"""
        self.column_data = column_data

        if self.column_data is None:
            self.column_data = {}

        self.entries = [FilterWidgetEntry(self)]
        self.boolean_operators = []

    def get_container_contents(self):
        entry_widgets = [e.get_widgets() for e in self.entries]

        boolean_widgets = [b.get_widgets() for b in self.boolean_operators]

        display_widgets = interleave_lists(entry_widgets, boolean_widgets)

        return HSplit(
            [
                HSplit(display_widgets, padding=1),
                self.button,
                ValidationToolbar(),
            ],
            padding=1,
        )

    def add_entry(self):
        self.entries.append(FilterWidgetEntry(self))
        self.boolean_operators.append(BooleanOperatorEntry(self))
        # Set the focus to the first widget in the most recently created entry
        # This is what we USED to do when we were just adding condition entries
        # rather than adding boolean conditions in between them
        # get_app().layout.focus(self.entries[-1].get_widgets().get_children()[0])
        # Now we set the focus to the newly added boolean operator dropdown
        get_app().layout.focus(self.boolean_operators[-1].get_widgets())
        self.trigger_on_change()

    @property
    def filters(self):
        entries_and_booleans = interleave_lists(self.entries, self.boolean_operators)

        filter_output = []

        for entry_or_boolean in entries_and_booleans:
            strings = entry_or_boolean.get_string_values()
            if strings[0] == self.column_prompt:
                continue
            elif len(strings) == 3 and strings[2] == entry_or_boolean.get_initial_prompt():
                continue
            filter_output.append(strings)

        if len(filter_output) > 0 and filter_output[-1][0] in ["AND", "OR"]:
            del filter_output[-1]

        return filter_output

    def __pt_container__(self):
        return self.container


class BooleanOperatorEntry:
    def __init__(self, filter_widget):
        self.filter_widget = filter_widget
        self.dropdown = DropdownBox(
            text="AND",
            entries=["AND", "OR"],
            filter=False,
            on_select_handler=filter_widget.trigger_on_change,
        )

    def get_widgets(self):
        return VSplit([self.dropdown], align=HorizontalAlign.LEFT)

    def get_string_values(self):
        return [self.dropdown.text]

    def get_initial_prompt(self):
        return ""


class FilterWidgetEntry:
    def __init__(self, filter_widget):
        self.filter_widget = filter_widget
        self.dropdown_column = DropdownBox(
            text=filter_widget.column_prompt,
            entries=filter_widget.column_data.keys(),
            on_select_handler=self.filter_widget.trigger_on_change,
        )
        self.dropdown_operator = DropdownBox(
            text=" = ",
            entries=self.get_operators,
            filter=False,
            on_select_handler=self.filter_widget.trigger_on_change,
        )

        # We have to create the widgets here in the init, or it doesn't work
        # because of some weird scoping issue
        # See https://github.com/prompt-toolkit/python-prompt-toolkit/issues/1324
        # vw = value_widget
        # Inside get_widgets we then just get a reference to the relevant one of these
        # (These don't make things much more inefficient, as they aren't displayed anywhere)
        # until they're added into a layout
        self.vw_text = CustomTextArea(
            self.filter_widget.value_prompt,
            multiline=False,
            on_change=self.filter_widget.trigger_on_change,
        )
        self.vw_float = CustomTextArea(
            self.filter_widget.value_prompt,
            multiline=False,
            validator=float_validator,
            on_change=self.filter_widget.trigger_on_change,
        )
        self.vw_int = CustomTextArea(
            self.filter_widget.value_prompt,
            multiline=False,
            validator=int_validator,
            on_change=self.filter_widget.trigger_on_change,
        )
        self.vw_datetime = MaskedInputWidget(
            ["yyyy", "!-", "mm", "!-", "dd", "! ", "HH", "!:", "MM", "!:", "SS"],
            overall_validator=datetime_validator,
            part_validator=int_validator,
            on_change=self.filter_widget.trigger_on_change,
        )
        self.vw_dropdown = DropdownBox(
            self.filter_widget.value_prompt,
            entries=self.get_value_dropdown_entries,
            on_select_handler=self.filter_widget.trigger_on_change,
        )

    def get_widgets(self):
        vw = self.choose_value_widget()
        return VSplit(
            [self.dropdown_column, self.dropdown_operator, vw],
            align=HorizontalAlign.LEFT,
            padding=2,
        )

    def get_initial_prompt(self):
        vw = self.choose_value_widget()
        return vw.initial_text

    def get_string_values(self):
        vw = self.choose_value_widget()
        return [self.dropdown_column.text.strip(), self.dropdown_operator.text.strip(), vw.text]

    def get_value_dropdown_entries(self):
        try:
            col_info = self.filter_widget.column_data[self.dropdown_column.text]
            col_values = col_info["values"]
            # We might have been passed integers or GUID types or something,
            # so convert to string
            return [str(value) for value in col_values]
        except KeyError:
            # If there isn't a values list provided then we won't be displaying
            # the dropdown anyway, so we can leave the list entry
            return []

    def choose_value_widget(self):
        try:
            col_info = self.filter_widget.column_data[self.dropdown_column.text]
            col_type = col_info["type"]
        except KeyError:
            # Default to a standard TextArea if we can't work out what to do
            return self.vw_text

        if col_type == "float":
            return self.vw_float
        elif col_type == "int":
            return self.vw_int
        elif col_type == "id":
            if self.dropdown_operator.text == "LIKE":
                # We want to be able to specify free text, like "*HMS PLA*"
                return self.vw_text
            if col_info.get("values") is not None:
                # We have a list of values, so give a dropdown
                return self.vw_dropdown
            else:
                # We don't have values, so just use a text box
                return self.vw_text
        elif col_type == "string":
            if self.dropdown_operator.text == "LIKE":
                # We want to be able to specify free text, like "*HMS PLA*"
                return self.vw_text
            if col_info.get("values") is not None:
                # We have a list of values, so give a dropdown
                return self.vw_dropdown
            else:
                # We don't have values, so just use a text box
                return self.vw_text
        elif col_type == "datetime":
            return self.vw_datetime
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
            return ["=", "!=", "LIKE"]
        elif col_type == "float":
            return ["=", "!=", ">", "<", ">=", "<="]
        elif col_type == "datetime":
            return ["=", "!=", ">", "<", ">=", "<="]
        else:
            return []
