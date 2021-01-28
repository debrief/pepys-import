from asyncio import Future

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
        filter=False,
        filter_method="contains",
        popup=False,
        enter_handler=None,
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
            self.filter_match_fn = self.contains
        else:
            self.filter_match_fn = self.startswith

        self.entries = entries

        self.width = width
        self.selected_entry = 0

        # Give extra space for the Filter line if we're filtering
        if self.filter:
            height = len(entries) + 1
        else:
            height = len(entries)

        # The content is just a FormattedTextControl containing the text
        # of the control
        self.container = Window(
            content=FormattedTextControl(
                text=self._get_formatted_text,
                focusable=True,
                key_bindings=self._get_key_bindings(),
            ),
            style="class:select-box",
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

    def _get_formatted_text(self):
        self.filtered_entries = []
        result = []

        if self.filter:
            # Filter entries
            for entry in self.entries:
                if self.filter_match_fn(entry, self.filter_text):
                    self.filtered_entries.append(entry)

            if len(self.filter_text) != 0:
                # Show an extra line at the top, showing the current filter
                result.append([("class:filter-text", f"Filter: {self.filter_text}\n")])
            else:
                result.append([("class:filter-text", "Type to filter\n")])
        else:
            # Just include all entries
            self.filtered_entries = self.entries

        for i, entry in enumerate(self.filtered_entries):
            if i == self.selected_entry:
                result.append([("[SetCursorPosition]", "")])
                result.append([("class:dropdown-highlight", entry)])
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
                # User cancelled
                self.future.set_result(None)

            @kb.add("enter")
            def _(event) -> None:
                # Return entry to the asyncio future
                self.future.set_result(self.filtered_entries[self.selected_entry])

        else:

            @kb.add("enter")
            def _(event) -> None:
                # Return entry in a non-async way, calling handler
                self.value = self.filtered_entries[self.selected_entry]
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