from prompt_toolkit import Application
from prompt_toolkit.application.current import get_app
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.layout import HSplit, Layout, VSplit
from prompt_toolkit.layout.containers import FloatContainer
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import Box, Button, Label

from pepys_admin.maintenance.widgets.dropdown_box import DropdownBox


def create_prompt_toolkit_app():
    kb = KeyBindings()

    kb.add("tab")(focus_next)
    kb.add("s-tab")(focus_previous)

    @kb.add("escape")
    def exit_handler(event=None) -> None:
        "Button handler that exits the app"
        get_app().exit()

    # All the widgets for the UI.
    dropdown1 = DropdownBox(
        "Select",
        [
            "Platform",
            "Sensor",
            "PlatformType",
            "SensorType",
            "Privacy",
            "CommentType",
            "Nationality",
        ],
    )
    dropdown2 = DropdownBox("Select", [str(i) for i in range(30)])
    button3 = Button("Exit", handler=exit_handler)

    root_container = FloatContainer(
        Box(
            HSplit(
                [
                    Label(text="Press `Tab` to move the focus."),
                    Box(
                        body=HSplit(
                            [
                                VSplit([Label(text="Select table: "), dropdown1]),
                                VSplit([Label(text="Select something else: "), dropdown2]),
                                button3,
                            ],
                            padding=1,
                        ),
                        padding=1,
                        style="class:left-pane",
                    ),
                ]
            ),
        ),
        floats=[],
    )

    layout = Layout(root_container)

    # Styling.
    style = Style(
        [
            ("left-pane", "bg:#888800 #000000"),
            ("right-pane", "bg:#00aa00 #000000"),
            ("button", "#000000"),
            ("button-arrow", "#000000"),
            ("button.focused", "bg:#ff0000"),
            ("dropdown", "bg:#ffff00"),
            ("dropdown.focused", "bg:#ff0000"),
            ("text-area focused", "bg:#ff0000"),
            ("completion-menu.completion.current", "bg:#ff0000"),
            ("dropdown-highlight", "#ff0000"),
        ]
    )

    app = Application(layout=layout, full_screen=True, key_bindings=kb, style=style)

    return app


app = create_prompt_toolkit_app()
app.run()
