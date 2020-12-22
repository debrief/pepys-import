from prompt_toolkit import Application
from prompt_toolkit.application.current import get_app
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.layout import HSplit, Layout, VSplit
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import Box, Button, Frame, Label, TextArea

buffer1 = Buffer()  # Editable buffer.


def exit_handler() -> None:
    " Button handler that returns None. "
    get_app().exit()


def next_dialog():
    # dlg.__init__(
    #     title="NEW NEW NEW",
    #     body=Label(
    #         text="Label here",
    #     ),
    #     buttons=[Button(text="Ok", handler=exit_handler)],
    #     with_background=True,
    # )
    # root_container[0] = BufferControl(buffer1)
    # left_window = Window(content=BufferControl(buffer1))
    pass


# def send_text():
#     right_buffer.text = textfield.text


kb = KeyBindings()

kb.add("tab")(focus_next)
kb.add("s-tab")(focus_previous)
kb.add("up")(focus_previous)
kb.add("down")(focus_next)


@kb.add("c-q")
def exit_(event):
    """
    Pressing Ctrl-Q will exit the user interface.

    Setting a return value means: quit the event loop that drives the user
    interface and return this value from the `Application.run()` call.
    """
    event.app.exit()


# Event handlers for all the buttons.
def button1_clicked():
    # right_buffer.text = "Button 1 clicked"
    # right_buffer.text = repr(root_container.children)
    bc = BufferControl(right_buffer)
    root_container.children[0] = Window(content=bc)
    bc.focus()


def button2_clicked():
    right_buffer.text = "Button 2 clicked"


def button3_clicked():
    right_buffer.text = "Button 3 clicked"


def exit_clicked():
    get_app().exit()


# All the widgets for the UI.
button1 = Button("Button 1", handler=button1_clicked)
button2 = Button("Button 2", handler=button2_clicked)
button3 = Button("Button 3", handler=button3_clicked)
button4 = Button("Exit", handler=exit_clicked)
text_area = TextArea(focusable=True)


# Combine all the widgets in a UI.
# The `Box` object ensures that padding will be inserted around the containing
# widget. It adapts automatically, unless an explicit `padding` amount is given.
wizard_container = Box(
    HSplit(
        [
            Label(text="Press `Tab` to move the focus."),
            VSplit(
                [
                    Box(
                        body=HSplit([button1, button2, button3, button4], padding=1),
                        padding=1,
                        style="class:left-pane",
                    ),
                    Box(body=Frame(text_area), padding=1, style="class:right-pane"),
                ]
            ),
        ]
    ),
)

right_buffer = Buffer()
root_container = VSplit(
    [
        # One window that holds the BufferControl with the default buffer on
        # the left.
        wizard_container,
        # A vertical line in the middle. We explicitly specify the width, to
        # make sure that the layout engine will not try to divide the whole
        # width by three for all these windows. The window will simply fill its
        # content by repeating this character.
        Window(width=1, char="|"),
        # Display the text 'Hello world' on the right.
        Window(content=BufferControl(right_buffer)),
    ]
)

layout = Layout(root_container)

# Styling.
style = Style(
    [
        ("left-pane", "bg:#888800 #000000"),
        ("right-pane", "bg:#00aa00 #000000"),
        ("button", "#000000"),
        ("button-arrow", "#000000"),
        ("button focused", "bg:#ff0000"),
        ("text-area focused", "bg:#ff0000"),
    ]
)

app = Application(layout=layout, full_screen=True, key_bindings=kb, style=style)
app.run()  # You won't be able to Exit this app
