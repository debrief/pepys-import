import functools
from asyncio import Future, ensure_future

from loguru import logger
from prompt_toolkit.application.current import get_app
from prompt_toolkit.formatted_text.base import merge_formatted_text
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.layout.containers import Float, Window, WindowAlign
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

    def __init__(self, entries, width=None, filter=False, filter_method="contains") -> None:
        """
        Provides a selectable list containing the given entries.

        Parameters:
        - `entries`: list of strings containing entries
        """
        # Create an asyncio Future which will be used to return
        # the value when this object is created
        self.future = Future()

        self.filter_text = ""
        self.filtered_entries = []

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
            for entry in self.entries:
                if self.filter_match_fn(entry, self.filter_text):
                    self.filtered_entries.append(entry)

            if len(self.filter_text) != 0:
                result.append([("class:filter-text", f"Filter: {self.filter_text}\n")])
            else:
                result.append([("class:filter-text", "Type to filter\n")])
        else:
            self.filtered_entries = self.entries

        for i, entry in enumerate(self.filtered_entries):
            if i == self.selected_entry:
                result.append([("[SetCursorPosition]", "")])
                result.append([("class:dropdown-highlight", entry)])
            else:
                result.append(entry)
            result.append("\n")

        return merge_formatted_text(result)

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

        @kb.add("enter")
        def close_float(event) -> None:
            self.future.set_result(self.filtered_entries[self.selected_entry])

        @kb.add("<any>")
        def _(event):
            logger.debug(f"Pressed a key, and caught it {event}")
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


class DropdownBox:
    """
    Widget that provides a dropdown box.

    A value (`text`) can be given to be displayed initially, plus a list of entries
    for the dropdown list. The user will then be able to open the dropdown by pressing
    Enter or the down arrow, and select one of the options. The dropdown list will
    then close and the selected option will be displayed.

    This is mostly a copy of the Button class from prompt_toolkit, with various
    alterations. It originally inherited from Button, but we had to override nearly
    all the methods, so it was easier to just copy it.
    """

    def __init__(self, text, entries, on_select_handler=None, filter=True) -> None:
        self.text = text
        self.entries = entries
        self.on_select_handler = on_select_handler
        self.filter = filter

        # Have to use partial to make this take a reference to self
        # (This could be avoided by making handler a classmethod,
        # but we want access to member variables)
        self.handler = functools.partial(self.handler, self)

        widths_for_max_calc = [len(self.text)]

        if filter:
            widths_for_max_calc.append(len("Type to filter"))

        if not callable(self.entries) and len(self.entries) > 0:
            widths_for_max_calc += [len(entry) for entry in self.entries]

        # Work out the max length of any entry or the original text
        max_len = max(widths_for_max_calc)

        self.width = max_len + 2
        self.control = FormattedTextControl(
            self._get_text_fragments,
            key_bindings=self._get_key_bindings(),
            focusable=True,
        )

        def get_style() -> str:
            if get_app().layout.has_focus(self):
                return "class:dropdown.focused"
            else:
                return "class:dropdown"

        self.window = Window(
            self.control,
            align=WindowAlign.CENTER,
            height=1,
            width=self.width,
            style=get_style,
            dont_extend_width=True,
            dont_extend_height=True,
        )

    def handler(self, event):
        if callable(self.entries):
            entries = self.entries()
        else:
            entries = self.entries

        if len(entries) == 0:
            return

        # We have to define a coroutine (the name doesn't matter)
        # so that we can use await inside the function body.
        async def coroutine():
            app = get_app()

            # Create a ComboBox to display the dropdown list
            menu = ComboBox(entries, self.width, filter=self.filter)

            # Wrap this in a Float, so we can display it above the rest of the
            # display. The high Z index makes this appear on top of anything else
            # By attaching it to a window, we get to use the window's menu position
            # (defined in _get_text_fragments) as the location
            float_ = Float(
                content=menu, z_index=1000, xcursor=True, ycursor=True, attach_to_window=self
            )

            # Add the floats to the FloatContainer, so it displays
            app.layout.container.floats.insert(0, float_)

            # Keep track of focus so we can retun to the previously focused control
            focused_before = app.layout.current_window
            app.layout.focus(menu)

            # This is the key bit - it waits until the ComboBox returns a result
            result = await menu.future

            app.layout.focus(focused_before)

            # Remove the float from the FloatContainer
            if float_ in app.layout.container.floats:
                app.layout.container.floats.remove(float_)

            # Update the display text to the option that was selected
            self.text = result

            # Call the on_select_handler
            if self.on_select_handler is not None:
                self.on_select_handler()

        # Run the coroutine and wait to get the result
        ensure_future(coroutine())

    def _get_text_fragments(self):
        text = ("{:^%s}" % (self.width - 2)).format(self.text)

        def handler(mouse_event) -> None:
            if self.handler is not None and mouse_event.event_type == MouseEventType.MOUSE_UP:
                self.handler()

        return [
            ("[SetMenuPosition]", ""),  # This sets the menu positon to be at the start of the text
            ("class:button.text", text, handler),
            ("class:button.arrow", " ▼", handler),  # TODO: Test the unicode character on Windows
        ]

    def _get_key_bindings(self) -> KeyBindings:
        " Key bindings for the Button. "
        kb = KeyBindings()

        # Make space, enter or down-arrow open the dropdown
        @kb.add(" ")
        @kb.add("enter")
        @kb.add("down")
        def _(event) -> None:
            if self.handler is not None:
                self.handler()

        return kb

    def __pt_container__(self):
        return self.window
