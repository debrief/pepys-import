from prompt_toolkit.application.current import get_app
from prompt_toolkit.layout import DynamicContainer, HorizontalAlign, HSplit, ScrollablePane, VSplit
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
    list_deep_equals,
)


class FilterWidget:
    def __init__(self, column_data=None, on_change_handler=None, max_filters=None):
        self.column_data = column_data
        self.on_change_handler = on_change_handler
        self.max_filters = max_filters

        self.last_filters_output = []

        # We can handle None for column_data if we turn it into an
        # empty dict, as all the dropdowns just default to not having
        # any entries
        if self.column_data is None:
            self.column_data = {}

        self.scrollable_pane = None

        # For consistency, keep these here, and reference them in the widgets
        # so we only have to change them in one place
        self.column_prompt = "Select column"
        self.value_prompt = "Enter value here"

        # The main container is a DynamicContainer, so it displays whatever the
        # result of a function is
        self.container = DynamicContainer(self.get_container_contents)
        self.button = Button("Add filter condition", self.add_entry)
        self.validation_toolbar = ValidationToolbar()

        # Start with one entry and no boolean operators
        self.entries = [FilterWidgetEntry(self)]
        self.boolean_operators = []

    def trigger_on_change(self, event=None):
        """Triggers the on_change_handler, if it is defined"""
        if self.on_change_handler is not None:
            if not list_deep_equals(self.filters, self.last_filters_output):
                # Only call event there is a difference from last time we called
                # the handler
                # (we have to use a custom list_deep_equals function as doing
                # == for lists of lists doesn't compare fully)
                self.on_change_handler(self.filters)

                self.last_filters_output = self.filters

    def set_column_data(self, column_data):
        """Updates the column_data, and removes all the filter entries
        so we can start again filtering a new table"""
        self.column_data = column_data

        if self.column_data is None:
            self.column_data = {}

        self.entries = [FilterWidgetEntry(self)]
        self.boolean_operators = []

    def get_container_contents(self):
        entry_widgets = [e.get_widgets() for e in self.entries]

        boolean_widgets = [b.get_widgets() for b in self.boolean_operators]

        # For now, just interleave the lists, so we get
        # FilterWidgetEntry
        # BooleanOperatorEntry
        # FilterWidgetEntry
        # ...
        display_widgets = interleave_lists(entry_widgets, boolean_widgets)
        content = HSplit(
            [
                HSplit(display_widgets, padding=1),
                self.button,
                self.validation_toolbar,
            ],
            padding=1,
        )

        if self.scrollable_pane is None:
            self.scrollable_pane = ScrollablePane(
                content,
            )
        else:
            self.scrollable_pane.content = content

        return self.scrollable_pane

    def add_entry(self):
        if self.max_filters is not None and len(self.entries) == self.max_filters:
            # TODO: Show some sort of error here - but we don't have access
            # to all the nice messagebox functionality int he main GUI
            # so I'm not sure how best to do it...
            return
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
        """
        Returns the filters that are currently defined in the widget.

        TODO: Put output format here
        """
        entries_and_booleans = interleave_lists(self.entries, self.boolean_operators)

        filter_output = []

        # Set up the mapping between human and system names,
        # defaulting to the human name if there is no system name defined
        human_to_system_name_mapping = {}
        for human_name in self.column_data.keys():
            system_name = self.column_data[human_name].get("system_name", None)
            if system_name is None:
                system_name = human_name
            human_to_system_name_mapping[human_name] = system_name

        for entry_or_boolean in entries_and_booleans:
            strings = entry_or_boolean.get_string_values()
            if strings[0] == self.column_prompt:
                # The column dropdown is still at the default value
                continue
            elif len(strings) == 3 and strings[2] == entry_or_boolean.get_initial_prompt():
                # We've got a full entry (not a boolean operator)
                # and the value widget is still at the default value
                continue
            elif len(strings) == 3:
                # Convert the column name to the system name for that column
                # (if there is no system name, then this just keeps the column as it is)
                strings[0] = human_to_system_name_mapping[strings[0]]
            filter_output.append(strings)

        if len(filter_output) > 0 and filter_output[-1][0] in ["AND", "OR"]:
            # If there is an AND/OR at the end of the list, then remove it
            # because there is no second operand for the AND/OR
            del filter_output[-1]

        return filter_output

    def __pt_container__(self):
        return self.container


class BooleanOperatorEntry:
    """Represents a boolean operator (AND/OR) entry in the FilterWidget"""

    def __init__(self, filter_widget):
        self.filter_widget = filter_widget
        self.dropdown = DropdownBox(
            text="AND",
            entries=["AND", "OR"],
            filter=False,  # No need to be able to filter, as just two entries
            on_select_handler=filter_widget.trigger_on_change,
        )

    def get_widgets(self):
        return VSplit([self.dropdown], align=HorizontalAlign.LEFT)

    def get_string_values(self):
        return [self.dropdown.text]

    def get_initial_prompt(self):
        # We'll never need to call this for a BooleanOperatorEntry,
        # so we can just return the empty string
        return ""


class FilterWidgetEntry:
    """Represents a full entry in the FilterWidget, consisting
    of a column name, an operator, and a value"""

    def __init__(self, filter_widget):
        self.filter_widget = filter_widget
        # Dropdown for list of column names
        self.dropdown_column = DropdownBox(
            text=filter_widget.column_prompt,
            entries=filter_widget.column_data.keys(),
            on_select_handler=self.filter_widget.trigger_on_change,
        )
        # Dropdown for list of operators
        # (This is automatically updated to show the list of entries
        # returned by self.get_operators, depending on the column chosen)
        self.dropdown_operator = DropdownBox(
            text=" = ",
            entries=self.get_operators,
            filter=False,
            on_select_handler=self.filter_widget.trigger_on_change,
        )

        self.delete_button = Button(text="Delete", handler=self.handle_delete)

        # We have to create the widgets here in the init, or it doesn't work
        # because of some weird scoping issue
        # See https://github.com/prompt-toolkit/python-prompt-toolkit/issues/1324
        # vw is shorthand for value_widget
        # Inside get_widgets we then just get a reference to the relevant one of these
        # (These don't make things much more inefficient, as they aren't displayed anywhere
        # until they're added into a layout)
        self.vw_text = CustomTextArea(
            self.filter_widget.value_prompt,
            multiline=False,
            on_change=self.filter_widget.trigger_on_change,
            focus_on_click=True,
        )
        self.vw_float = CustomTextArea(
            self.filter_widget.value_prompt,
            multiline=False,
            validator=float_validator,
            on_change=self.filter_widget.trigger_on_change,
            focus_on_click=True,
        )
        self.vw_int = CustomTextArea(
            self.filter_widget.value_prompt,
            multiline=False,
            validator=int_validator,
            on_change=self.filter_widget.trigger_on_change,
            focus_on_click=True,
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
        """Gets the widgets to display this entry"""
        vw = self.choose_value_widget()
        elements = [self.dropdown_column, self.dropdown_operator, vw, self.delete_button]
        return VSplit(
            elements,
            align=HorizontalAlign.LEFT,
            padding=2,
        )

    def handle_delete(self):
        index = self.filter_widget.entries.index(self)
        if index == 0 and len(self.filter_widget.entries) == 1:
            # If it's the only one, then delete and immediately add a new blank entry
            self.filter_widget.entries.remove(self)
            self.filter_widget.entries.append(FilterWidgetEntry(self.filter_widget))
        else:
            self.filter_widget.entries.remove(self)
            self.filter_widget.boolean_operators.remove(
                self.filter_widget.boolean_operators[index - 1]
            )
        app = get_app()
        app.layout.focus_next()
        self.filter_widget.trigger_on_change()

    def get_initial_prompt(self):
        """Get the initial text value of the value_widget,
        so we can see if it has changed from it's default."""
        vw = self.choose_value_widget()
        return vw.initial_text

    def get_string_values(self):
        """Get the string values of the widgets - ie. the text that
        has been chosen by the user, as a list of three entries."""
        vw = self.choose_value_widget()
        return [self.dropdown_column.text.strip(), self.dropdown_operator.text.strip(), vw.text]

    def get_value_dropdown_entries(self):
        """Gives the entries for the value widget dropdown
        (only called if that's being used)"""
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
        """Decide which value widget to use, depending on the col_type
        in the column data"""
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
        """Get the list of entries for the operators dropdown, based on the
        col_type entry in the column data"""
        try:
            col_info = self.filter_widget.column_data[self.dropdown_column.text]
            col_type = col_info["type"]
        except KeyError:
            return []
        return self.get_operators_for_column_type(col_type)

    def get_operators_for_column_type(self, col_type):
        """Get the list of entries for the operators dropdown, based on the
        col_type entry in the column data"""
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
