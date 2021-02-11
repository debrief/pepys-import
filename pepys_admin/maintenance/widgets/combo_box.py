from asyncio import Future

from prompt_toolkit.application.current import get_app
from prompt_toolkit.formatted_text.base import merge_formatted_text
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.margins import ScrollbarMargin
from prompt_toolkit.mouse_events import MouseEventType


class ComboBox:
    """
    Input field where the user can select one out of multiple entries. Basically acts
    as a popup menu that you can select from, a bit like the completions menu.

    This could be replaced by CompletionsMenuControl from prompt_toolkit itself,
    but it will take a bit of alteration and integration, so the current approach
    is probably easier.

    Taken from https://github.com/prompt-toolkit/python-prompt-toolkit/pull/1129
    (a PR by the author of prompt toolkit) and modified.
    """

    def __init__(
        self,
        entries,
        width=None,
        height=None,
        filter=False,
        filter_method="contains",
        popup=False,
        enter_handler=None,
        style=None,
    ) -> None:
        """
        Provides a selectable list containing the given entries.

        Parameters:
        - `entries`: list of strings containing entries
        - `width`: width of control, in characters
        - `filter`: whether to provide 'type to filter' functionality (boolean)
        - `filter_method`: how to filter - must be either 'contains' or 'startswith'
        - `popup`: whether this ComboBox is being used as a popup menu (boolean) - if it
          is a popup then async features will be used to return values, and tab/shift-tab/esc
          will be captured
        - `enter_handler`: event handler function to be called when an entry is selected
        - `style`: Any custom style to be passed to the underlying control
        """
        # Create an asyncio Future which will be used to return
        # the value when this object is created
        self.future = Future()

        self.popup = popup

        self.filter_text = ""
        self.filtered_entries = []

        self.enter_handler = enter_handler

        self.filter = filter

        if filter_method == "contains":
            self.filter_function = self.filter_contains
        elif filter_method == "startswith":
            self.filter_function = self.filter_startswith
        elif filter_method == "special":
            self.filter_function = self.filter_special

        self.entries = entries

        self.width = width
        self.selected_entry = 0

        if height is None:
            # Give extra space for the Filter line if we're filtering
            if self.filter:
                height = len(entries) + 1
            else:
                height = len(entries)

        if style is None:
            style = ""

        # The content is just a FormattedTextControl containing the text
        # of the control
        self.container = Window(
            content=FormattedTextControl(
                text=self._get_formatted_text,
                focusable=True,
                key_bindings=self._get_key_bindings(),
            ),
            style=style,
            height=height,
            width=self.width,
            right_margins=[
                ScrollbarMargin(display_arrows=True),
            ],
        )

    def startswith(self, string, prefix):
        return string.upper().startswith(prefix.upper())

    def contains(self, string, substring):
        if substring.upper() in string.upper():
            return True
        else:
            return False

    def filter_contains(self):
        for entry in self.entries:
            if self.contains(entry, self.filter_text):
                self.filtered_entries.append(entry)

    def filter_startswith(self):
        for entry in self.entries:
            if self.startswith(entry, self.filter_text):
                self.filtered_entries.append(entry)

    def filter_special(self):
        startswith = []
        contains = []
        for entry in self.entries:
            if self.startswith(entry, self.filter_text):
                startswith.append(entry)
            elif self.contains(entry, self.filter_text):
                # Note: as this is in an elif, an entry
                # will only be added to the contains list
                # if it is not in the startswith list
                # Therefore when we combine them below
                # we won't get duplicates
                contains.append(entry)

        self.filtered_entries = startswith + contains

    def _get_formatted_text(self):
        self.filtered_entries = []
        result = []

        if len(self.entries) == 0:
            result.append([("class:filter-text", "No entries!\n")])
        elif self.filter:
            # Filter entries
            self.filter_function()

            if len(self.filter_text) != 0:
                # Show an extra line at the top, showing the current filter
                result.append([("class:filter-text", f"Filter: {self.filter_text}\n")])
            else:
                result.append([("class:filter-text", "Type to filter\n")])
        else:
            # Just include all entries
            self.filtered_entries = self.entries

        app = get_app()
        for i, entry in enumerate(self.filtered_entries):
            if i == self.selected_entry:
                result.append([("[SetCursorPosition]", "")])
                if self.popup:
                    result.append([("class:dropdown-highlight", entry)])
                elif app.layout.has_focus(self):
                    result.append([("class:combobox-highlight", entry)])
                else:
                    result.append([("", entry)])
            else:
                result.append(entry)
            result.append("\n")

        merged_text = merge_formatted_text(result)()

        # Go through the resulting tuples and add the mouse click handler to each of them
        for i in range(len(merged_text)):
            merged_text[i] = (merged_text[i][0], merged_text[i][1], self.handle_mouse_click)

        return merged_text

    def handle_mouse_click(self, mouse_event):
        if mouse_event.event_type == MouseEventType.MOUSE_UP:
            # If we have an extra row at the top of the combo box
            # for showing the filter text, then we need to take 1
            # off the index when we work out which entry to use
            offset = 1 if self.filter else 0

            if self.popup:
                self.future.set_result(self.filtered_entries[mouse_event.position.y - offset])
            else:
                self.value = self.filtered_entries[mouse_event.position.y - offset]
                if self.enter_handler:
                    self.enter_handler(self.value)

    def _get_key_bindings(self) -> KeyBindings:
        kb = KeyBindings()

        @kb.add("up")
        def _go_up(event) -> None:
            if len(self.filtered_entries):
                self.selected_entry = (self.selected_entry - 1) % len(self.filtered_entries)

        @kb.add("down")
        def _go_down(event) -> None:
            if len(self.filtered_entries):
                self.selected_entry = (self.selected_entry + 1) % len(self.filtered_entries)

        if self.popup:

            @kb.add("tab")
            @kb.add("s-tab")
            def _(event):
                return None

            @kb.add("escape")
            def _(event):
                try:
                    # User cancelled
                    self.future.set_result(None)
                except Exception:
                    pass

            @kb.add("enter")
            def _(event) -> None:
                try:
                    # Return entry to the asyncio future
                    self.future.set_result(self.filtered_entries[self.selected_entry])
                except Exception:
                    self.future.set_result(None)

        else:

            @kb.add("enter")
            def _(event) -> None:
                # Return entry in a non-async way, calling handler
                try:
                    self.value = self.filtered_entries[self.selected_entry]
                except IndexError:
                    return
                if self.enter_handler:
                    self.enter_handler(self.value)

        @kb.add("<any>")
        def _(event):
            key_str = event.key_sequence[0].key
            if key_str == "c-h":
                self.filter_text = self.filter_text[:-1]
            elif len(key_str) == 1:
                self.filter_text += key_str

        return kb

    # This is part of the API that makes this object behave as a
    # valid container
    def __pt_container__(self):
        return self.container
