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

CONTEXTUAL_HELP_STRING = "# Second panel: Build filters (F3)"
from loguru import logger


class FilterWidget:
    def __init__(
        self,
        column_data=None,
        on_change_handler=None,
        max_filters=None,
        contextual_help_setter=None,
        filter_function=None,
    ):
        """A widget that allows the creation of SQL-style filter constraints, in the style
        of <column_name> <operator> <value> such as "name == 'Robin'" or "speed >= 23.5". Also
        provides the ability to combine these constraints with boolean AND or OR operators.

        :param column_data: Dictionary data structure defining the columns that can be selected,
        and their types and values, defaults to None. Can be set after creation with `set_column_data`.
        See below for an example.
        :type column_data: dict, optional
        :param on_change_handler: Function to be called whenever the output (as provided by the .filters
        property) changes, defaults to None
        :type on_change_handler: Function, optional
        :param max_filters: Maximum number of filters to allow, defaults to None
        :type max_filters: int, optional
        :param filter_function: Function called with the column_data as an argument whenever column data is set/reset.
        This should return a new column_data dict to be used, and is designed to allow filtering out elements of the column
        data so they don't get offered as options for filtering (eg. filtering out specific fields)

        Column Data structure
        =====================
        The column data structure is a dictionary with the column display names as its keys, and details about
        the column in the values. Each value is another dictionary which can contain keys of "type" (column
        data type), "values" (a list of values to select from) and "system_name" (an internal name to be used
        for this column in the output). Recognised types are "id", "string", "float", "int" and "datetime",
        and different widgets will be displayed to select entries of these different types - including a masked
        input widget for datetime, and numerical validation for int and float. The only compulsory entry is the
        "type" specifying the column data type.

        A full example of a valid column_data dictionary is:
        {
            "platform_id": {"type": "id", "values": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]},
            "name": {"type": "string", "values": ["HMS Name1", "HMS Floaty", "USS Sinky"]},
            "identifier": {"type": "string"},
            "nationality_id": {"type": "id", "system_name": "Nationality.nationality_id"},
            "nationality_name": {"type": "string", "system_name": "Nationality.name"},
            "timestamp": {"type": "datetime"},
            "speed": {"type": "float"},
        }
        """
        self.column_data = column_data
        self.on_change_handler = on_change_handler
        self.max_filters = max_filters
        self.contextual_help_setter = contextual_help_setter
        self.filter_function = filter_function
        self.last_filters_output = []

        # We can handle None for column_data if we turn it into an
        # empty dict, as all the dropdowns just default to not having
        # any entries
        if self.column_data is None:
            self.column_data = {}
        else:
            if callable(self.filter_function):
                self.column_data = self.filter_function(self.column_data)

        self.scrollable_pane = None

        # For consistency, keep these here, and reference them in the widgets
        # so we only have to change them in one place
        self.column_prompt = "Select column"
        self.value_prompt = "Enter value here"

        # The main container is a DynamicContainer, so it displays whatever the
        # result of a function is
        self.container = DynamicContainer(self.get_container_contents)
        self.button = Button("Add filter condition", self.add_entry, width=22)
        self.set_contextual_help(self.button, CONTEXTUAL_HELP_STRING)
        self.validation_toolbar = ValidationToolbar()

        # Start with one entry and no boolean operators
        self.entries = [FilterWidgetEntry(self)]
        self.boolean_operators = []

    def set_contextual_help(self, widget, text):
        if self.contextual_help_setter is not None:
            self.contextual_help_setter(widget, text)

    def trigger_on_change(self, event=None):
        """Triggers the on_change_handler, if it is defined"""
        logger.debug("trigger on change")
        logger.debug(f"{self.filters=}")
        if self.on_change_handler is not None:
            if not list_deep_equals(self.filters, self.last_filters_output):
                # Only call event there is a difference from last time we called
                # the handler
                # (we have to use a custom list_deep_equals function as doing
                # == for lists of lists doesn't compare fully)
                self.on_change_handler(self.filters)

                self.last_filters_output = self.filters

    def set_column_data(self, column_data, clear_entries=True):
        """Updates the column_data, and removes all the filter entries
        so we can start again filtering a new table"""
        if column_data is None:
            self.column_data = {}
        elif callable(self.filter_function):
            self.column_data = self.filter_function(column_data)
        else:
            self.column_data = column_data

        if clear_entries:
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
                VSplit([self.button], align=HorizontalAlign.CENTER),
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

        Currently, the output is a very simple list of lists that looks like this:

        [
            ["col_name", "operator", "value"],
            ["AND"]
            ["col_name2", "operator2", "value2"],
            ...
        ]
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
            logger.debug(f"{strings=}")
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

        # Remove any trailing AND or OR values from the list
        # These can occur if we have multiple empty filter entries
        # at the end of the list
        # This also catches the situation where the result is *all*
        # AND/OR values (ie. all filter entries are empty)
        if len(filter_output) > 0:
            for i in range(len(filter_output), 0, -1):
                if filter_output[i - 1] == ["AND"] or filter_output[i - 1] == ["OR"]:
                    del filter_output[i - 1]
                else:
                    break

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
        self.filter_widget.set_contextual_help(self.dropdown, "## Operator line")

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
            on_select_handler=self.on_dropdown_column_select,
        )
        self.filter_widget.set_contextual_help(self.dropdown_column, CONTEXTUAL_HELP_STRING)
        # Dropdown for list of operators
        # (This is automatically updated to show the list of entries
        # returned by self.get_operators, depending on the column chosen)
        self.dropdown_operator = DropdownBox(
            text=" = ",
            entries=self.get_operators,
            filter=False,
            on_select_handler=self.filter_widget.trigger_on_change,
        )
        self.filter_widget.set_contextual_help(self.dropdown_operator, CONTEXTUAL_HELP_STRING)

        self.delete_button = Button(text="Delete", handler=self.handle_delete)
        self.filter_widget.set_contextual_help(self.delete_button, CONTEXTUAL_HELP_STRING)

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
        self.filter_widget.set_contextual_help(self.vw_text, CONTEXTUAL_HELP_STRING)
        self.vw_float = CustomTextArea(
            self.filter_widget.value_prompt,
            multiline=False,
            validator=float_validator,
            on_change=self.filter_widget.trigger_on_change,
            focus_on_click=True,
        )
        self.filter_widget.set_contextual_help(self.vw_float, CONTEXTUAL_HELP_STRING)
        self.vw_int = CustomTextArea(
            self.filter_widget.value_prompt,
            multiline=False,
            validator=int_validator,
            on_change=self.filter_widget.trigger_on_change,
            focus_on_click=True,
        )
        self.filter_widget.set_contextual_help(self.vw_int, CONTEXTUAL_HELP_STRING)
        self.vw_datetime = MaskedInputWidget(
            ["yyyy", "!-", "mm", "!-", "dd", "! ", "HH", "!:", "MM", "!:", "SS"],
            overall_validator=datetime_validator,
            part_validator=int_validator,
            on_change=self.filter_widget.trigger_on_change,
        )
        self.filter_widget.set_contextual_help(self.vw_datetime, CONTEXTUAL_HELP_STRING)
        self.vw_dropdown = DropdownBox(
            self.filter_widget.value_prompt,
            entries=self.get_value_dropdown_entries,
            on_select_handler=self.filter_widget.trigger_on_change,
        )
        self.filter_widget.set_contextual_help(self.vw_dropdown, CONTEXTUAL_HELP_STRING)
        self.vw_bool = DropdownBox(
            self.filter_widget.value_prompt,
            entries=["True", "False"],
            on_select_handler=self.filter_widget.trigger_on_change,
        )
        self.filter_widget.set_contextual_help(self.vw_bool, CONTEXTUAL_HELP_STRING)

    def on_dropdown_column_select(self, value):
        """Called when an entry is selected from the column dropdown.
        Resets the other widgets in that line back to their default."""
        self.dropdown_operator.text = " = "
        self.vw_dropdown.text = self.filter_widget.value_prompt

        if self.filter_widget.column_data[value]["type"] == "id":
            self.dropdown_operator.text = "LIKE"

        self.filter_widget.trigger_on_change()

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
        "Called when the delete button is pressed for this row"
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

        # If the column AND the value aren't set to the default prompts
        if (
            self.dropdown_column.text != self.filter_widget.column_prompt
            and vw.text != self.filter_widget.value_prompt
        ):
            # Get the column info and if it has a list of IDs then
            # return the ID of the entry the user selected rather than the text of the entry
            col_config = self.filter_widget.column_data[self.dropdown_column.text]
            if col_config["type"] == "bool":
                if vw.text == "True":
                    value_obj = True
                else:
                    value_obj = False
            elif "ids" in col_config:
                index = col_config["values"].index(vw.text)
                value_obj = col_config["ids"][index]
            else:
                value_obj = vw.text
        else:
            value_obj = vw.text

        return [self.dropdown_column.text.strip(), self.dropdown_operator.text.strip(), value_obj]

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
        elif col_type == "bool":
            return self.vw_bool
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
        except KeyError:
            return []
        return self.get_operators_for_column(col_info)

    def get_operators_for_column(self, col_info):
        """Get the list of entries for the operators dropdown, based on the
        col_type entry in the column data"""
        col_type = col_info["type"]
        if col_info["sqlalchemy_type"] == "relationship":
            return ["=", "!="]
        elif col_type == "string":
            return ["=", "!=", "LIKE"]
        elif col_type == "id":
            return ["LIKE"]
        elif col_type == "float":
            return ["=", "!=", ">", "<", ">=", "<="]
        elif col_type == "int":
            return ["=", "!=", ">", "<", ">=", "<="]
        elif col_type == "datetime":
            return ["=", "!=", ">", "<", ">=", "<="]
        elif col_type == "bool":
            return ["="]
        else:
            return []
