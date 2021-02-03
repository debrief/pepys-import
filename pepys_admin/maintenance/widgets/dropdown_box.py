import functools
from asyncio import ensure_future

from prompt_toolkit.application.current import get_app
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.layout.containers import Float, Window, WindowAlign
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.mouse_events import MouseEventType

from pepys_admin.maintenance.widgets.combo_box import ComboBox


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

    def __init__(
        self,
        text,
        entries,
        on_select_handler=None,
        filter=True,
        filter_method="special",
        open_on_any_key=True,
        max_width=30,
    ) -> None:
        self.text = text
        self.initial_text = text
        self.entries = entries
        self.on_select_handler = on_select_handler
        self.filter = filter
        self.filter_method = filter_method
        self.open_on_any_key = open_on_any_key
        self.max_width = max_width

        self.menu = None
        self.disabled = False

        # Have to use partial to make this take a reference to self
        # (This could be avoided by making handler a classmethod,
        # but we want access to member variables)
        self.handler = functools.partial(self.handler, self)

        self.calculate_width()

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

    def calculate_width(self):
        widths_for_max_calc = [len(self.text)]

        if self.filter:
            widths_for_max_calc.append(len("Type to filter"))

        if not callable(self.entries) and len(self.entries) > 0:
            widths_for_max_calc += [len(entry) for entry in self.entries]
        elif callable(self.entries):
            entries = self.entries()
            widths_for_max_calc += [len(entry) for entry in entries]
        # Work out the max length of any entry or the original text
        max_len = max(widths_for_max_calc)

        calc_width = max_len + 2

        if calc_width > self.max_width:
            self.width = self.max_width
        else:
            self.width = calc_width

    def handler(self, event):
        if self.disabled:
            return

        if callable(self.entries):
            entries = self.entries()
        else:
            entries = self.entries

        if len(entries) == 0:
            return

        self.calculate_width()

        # Create a ComboBox to display the dropdown list
        self.menu = ComboBox(
            entries,
            self.width,
            filter=self.filter,
            popup=True,
            style="class:dropdown.box",
            filter_method=self.filter_method,
        )

        # We have to define a coroutine (the name doesn't matter)
        # so that we can use await inside the function body.
        async def coroutine():
            app = get_app()

            # Wrap this in a Float, so we can display it above the rest of the
            # display. The high Z index makes this appear on top of anything else
            # By attaching it to a window, we get to use the window's menu position
            # (defined in _get_text_fragments) as the location
            float_ = Float(
                content=self.menu, z_index=1000, xcursor=True, ycursor=True, attach_to_window=self
            )

            # Add the floats to the FloatContainer, so it displays
            app.layout.container.floats.insert(0, float_)

            # Keep track of focus so we can retun to the previously focused control
            focused_before = app.layout.current_window
            app.layout.focus(self.menu)

            # This is the key bit - it waits until the ComboBox returns a result
            result = await self.menu.future

            try:
                app.layout.focus(focused_before)
            except Exception:
                pass

            # Remove the float from the FloatContainer
            if float_ in app.layout.container.floats:
                app.layout.container.floats.remove(float_)

            if result is not None:
                # Update the display text to the option that was selected
                self.text = result

                # Call the on_select_handler
                if self.on_select_handler is not None:
                    self.on_select_handler(self.text)

        # Run the coroutine and wait to get the result
        ensure_future(coroutine())

    def _get_text_fragments(self):
        # Update the width calculation, but only
        # refresh the whole screen if the window width
        # actually needs to change
        prev_window_width = self.window.width
        self.calculate_width()
        if self.width != prev_window_width:
            self.window.width = self.width
            app = get_app()
            app.invalidate()

        text = ("{:^%s}" % (self.width - 2)).format(self.text)

        def handler(mouse_event) -> None:
            if self.handler is not None and mouse_event.event_type == MouseEventType.MOUSE_UP:
                self.handler()

        return [
            ("[SetMenuPosition]", ""),  # This sets the menu positon to be at the start of the text
            ("class:dropdown.text", text, handler),
            (
                "class:dropdown.arrow",
                " \u25BC",  # Down arrow symbol
                handler,
            ),
        ]

    def _get_key_bindings(self) -> KeyBindings:
        " Key bindings for the Dropdown Box. "
        kb = KeyBindings()

        # Make space, enter or down-arrow open the dropdown
        @kb.add(" ")
        @kb.add("enter")
        @kb.add("down")
        def _(event) -> None:
            if self.handler is not None:
                self.handler()

        @kb.add("<any>")
        def _(event):
            key_str = event.key_sequence[0].key
            if len(key_str) == 1:
                if self.open_on_any_key and self.handler is not None:
                    self.handler()
                    self.menu.filter_text += key_str

        return kb

    def __pt_container__(self):
        return self.window
