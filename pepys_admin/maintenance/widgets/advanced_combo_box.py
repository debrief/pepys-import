from asyncio import Future

from prompt_toolkit.application.current import get_app
from prompt_toolkit.formatted_text.base import merge_formatted_text
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.margins import ScrollbarMargin
from prompt_toolkit.mouse_events import MouseEventType

DISABLED_TEXT = " (unavailable, click for more information)"


class AdvancedComboBox:
    """
    TODO: Update
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

        self.enter_handler = enter_handler

        self.entries = entries

        self.width = width
        self.selected_entry = 0

        # if height is None:
        #     height = len(entries)

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

    def _get_formatted_text(self):
        if callable(self.entries):
            self.entry_values = self.entries()
        else:
            self.entry_values = self.entries

        result = []

        if len(self.entry_values) == 0:
            result.append([("class:filter-text", "No entries!\n")])

        app = get_app()
        for i, entry in enumerate(self.entry_values):
            entry_text, enabled = entry
            if i == self.selected_entry:
                result.append([("[SetCursorPosition]", "")])
                if app.layout.has_focus(self):
                    if enabled:
                        result.append([("class:combobox-highlight", entry_text)])
                    else:
                        result.append(
                            [
                                (
                                    "class:combobox-highlight class:disabled-entry",
                                    entry_text + DISABLED_TEXT,
                                )
                            ]
                        )
                else:
                    if enabled:
                        result.append([("", entry_text)])
                    else:
                        result.append([("class:disabled-entry", entry_text + DISABLED_TEXT)])
            else:
                if enabled:
                    result.append(entry_text)
                else:
                    result.append([("class:disabled-entry", entry_text + DISABLED_TEXT)])

            result.append("\n")

        merged_text = merge_formatted_text(result)()

        # Go through the resulting tuples and add the mouse click handler to each of them
        output_text = [(entry[0], entry[1], self.handle_mouse_click) for entry in merged_text]

        return output_text

    def handle_mouse_click(self, mouse_event):
        if mouse_event.event_type == MouseEventType.MOUSE_UP:
            self.value = self.entry_values[mouse_event.position.y][0]
            if self.enter_handler:
                self.enter_handler(self.value)

    def _get_key_bindings(self) -> KeyBindings:
        kb = KeyBindings()

        @kb.add("up")
        def _go_up(event) -> None:
            if len(self.entry_values):
                self.selected_entry = (self.selected_entry - 1) % len(self.entry_values)

        @kb.add("down")
        def _go_down(event) -> None:
            if len(self.entry_values):
                self.selected_entry = (self.selected_entry + 1) % len(self.entry_values)

        @kb.add("enter")
        def _(event) -> None:
            self.select_handler()

        @kb.add("<any>")
        def _(event):
            self.handle_numeric_key(event)

        return kb

    def handle_numeric_key(self, event):
        key_str = event.key_sequence[0].key
        if len(key_str) == 1 and key_str.isdigit():
            int_value = int(key_str)
            if 1 <= int_value <= len(self.entry_values):
                self.selected_entry = int_value - 1
                self.select_handler()

    def select_handler(self):
        # Return entry in a non-async way, calling handler
        try:
            self.value = self.entry_values[self.selected_entry][0]
        except IndexError:
            return
        if self.enter_handler:
            self.enter_handler(self.value)

    # This is part of the API that makes this object behave as a
    # valid container
    def __pt_container__(self):
        return self.container
