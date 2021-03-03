from prompt_toolkit.formatted_text.base import to_formatted_text
from prompt_toolkit.mouse_events import MouseEventType
from prompt_toolkit.widgets.base import CheckboxList


class CheckboxTable(CheckboxList):
    def __init__(self, table_data, table_objects, any_keybinding=None):
        """Creates a table view with checkboxes on the left-hand side.

        Parameters:
        - `table_data`: A list of lists, containing each row of the data. Each list
          must be the same length. For example:
            [
                ["Name", "Type", "Nat."],
                ["NELSON", "Frigate", "UK"],
                ["SARK", "Destroyer", "UK"],
                ["ADRI", "Frigate", "UK"],
                ["JEAN", "Corvette", "FR"],
            ]
        - `table_objects`: A list of objects of any type that are associated with each row.
          These are the objects that are returned when a row is selected. They could, for instance,
          be row IDs, SQLAlchemy objects, or similar. (We can't just return one of the columns,
          as we don't know if any of them will be a unique column)

        Both of these arguments can be functions which return a list containing the relevant data
        """
        self.values = []

        self.table_data = table_data
        self.table_objects = table_objects

        self.old_table_objects = None

        self.create_values_from_parameters()

        super().__init__(self.values)

        if callable(any_keybinding):
            kb = self.control.key_bindings

            @kb.add("<any>")
            def _(event):
                any_keybinding(event)

    def create_values_from_parameters(self):
        self.values = []

        if callable(self.table_data):
            table_data = self.table_data()
        else:
            table_data = self.table_data

        if callable(self.table_objects):
            table_objects = self.table_objects()
        else:
            table_objects = self.table_objects

        if table_objects != self.old_table_objects:
            # We've got a change to the data
            # So clear the list of current values
            self.current_values = []
            self.old_table_objects = table_objects

        if len(table_data) == 0 or len(table_objects) == 0:
            # The underlying CheckboxList implementation
            # has an assert statement checking there is at least one entry
            # in the values list.
            # So, we fake it with an empty string.
            self.values = [(None, "")]
            return

        if len(table_data) != len(table_objects):
            raise ValueError("table_data and table_objects lists must be the same length")

        # Work out the maximum length of each column
        # col_max_length[col_index] will be the maximum
        # length of strings for that column
        col_max_lengths = []
        for col_index in range(len(table_data[0])):
            lengths = []
            for entry in table_data:
                lengths.append(len(entry[col_index]))
            col_max_lengths.append(max(lengths))

        # Left-justify the strings in each column, and join them
        # with a " | " as a column separator
        for data, obj in zip(table_data, table_objects):
            justified_cols = []
            for col_index, col in enumerate(data):
                justified_cols.append(col.ljust(col_max_lengths[col_index]))
            self.values.append((obj, " | ".join(justified_cols)))

    def _get_text_fragments(self):
        # Mostly copied from the prompt_toolkit CheckboxList
        # class, with some minor alterations to:
        # - Not show a selection box for the header line
        # - Mark selected items with 'x' not '*'
        # - Highlight whole row when moving up and down
        def mouse_handler(mouse_event) -> None:
            """
            Set `_selected_index` and `current_value` according to the y
            position of the mouse click event.
            """
            if mouse_event.event_type == MouseEventType.MOUSE_UP:
                self._selected_index = mouse_event.position.y
                self._handle_enter()

        self.create_values_from_parameters()

        # the 1's in the code below are to deal with the header row
        all_selected = len(self.current_values) == len(self.values) - 1
        none_selected = len(self.current_values) == 0

        result = []
        for i, value in enumerate(self.values):
            if i == 0:
                result.append(("class:table-title", self.open_character))
                if i == self._selected_index:
                    result.append(("[SetCursorPosition]", ""))
                if all_selected:
                    result.append(("class:table-title", "x"))
                elif none_selected:
                    result.append(("class:table-title", " "))
                else:
                    result.append(("class:table-title", "-"))
                result.append(("class:table-title", self.close_character))
                result.append(("", " "))
                result.extend(to_formatted_text(value[1], style="class:table-title"))
                result.append(("", "\n"))
                continue
            if self.multiple_selection:
                checked = value[0] in self.current_values
            else:
                checked = value[0] == self.current_value
            selected = i == self._selected_index

            style = ""
            if checked:
                style += " " + self.checked_style
            if selected:
                style += " " + self.selected_style

            result.append((style, self.open_character))

            if selected:
                result.append(("[SetCursorPosition]", ""))

            if checked:
                result.append((style, "x"))
            else:
                result.append((style, " "))

            result.append((style, self.close_character))
            result.append((style, " "))
            result.extend(to_formatted_text(value[1], style=style))
            result.append(("", "\n"))

        # Add mouse handler to all fragments.
        for i in range(len(result)):
            result[i] = (result[i][0], result[i][1], mouse_handler)

        if len(result) > 0:
            result.pop()  # Remove last newline.
        return result

    def _handle_enter(self) -> None:
        if self._selected_index == 0:
            # If we've pressed enter (or clicked) on the header row
            # then turn them all on/off as required
            all_selected = len(self.current_values) >= len(self.values) - 1
            if all_selected:
                self.current_values = []
            else:
                # This sets current_values to all of the entries of the table objects
                # excluding the None value for the header row
                self.current_values = [val[0] for val in self.values[1:]]
            return
        val = self.values[self._selected_index][0]
        if val in self.current_values:
            self.current_values.remove(val)
        else:
            self.current_values.append(val)
