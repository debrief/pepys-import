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

    def __init__(self, text, entries, on_select_handler=None, filter=True) -> None:
        self.text = text
        self.initial_text = text
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
            menu = ComboBox(entries, self.width, filter=self.filter, popup=True)

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

            if result is not None:
                # Update the display text to the option that was selected
                self.text = result

                # Call the on_select_handler
                if self.on_select_handler is not None:
                    self.on_select_handler(self.text)

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
            (
                "class:button.arrow",
                " \u25BC",  # Down arrow symbol
                handler,
            ),
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
