from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.layout.containers import FloatContainer, HorizontalAlign, HSplit, VSplit, Window
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets.base import Label

from pepys_admin.maintenance.widgets.dropdown_box import DropdownBox


class MaintenanceGUI:
    def __init__(self):
        self.preview_buffer = Buffer()
        self.preview_container = HSplit(
            children=[
                Label(text="Preview List   F7 | Preview Graph  F8", style="class:title-line"),
                Label(
                    text="Select specific fields to display in preview",
                    style="fg:ansiblue",
                ),
            ],
            padding=1,
            width=Dimension(weight=0.4),
        )

        self.data_type_container = HSplit(
            children=[
                Label(text="Select data type   F2", style="class:title-line"),
                VSplit(
                    [
                        DropdownBox(
                            text="Select a table",
                            entries=[
                                "Platform",
                                "Sensor",
                                "PlatformType",
                                "SensorType",
                                "Privacy",
                                "CommentType",
                                "Nationality",
                            ],
                        )
                    ],
                    align=HorizontalAlign.LEFT,
                ),
            ],
            padding=1,
            height=Dimension(weight=0.05),
        )

        self.filter_container = HSplit(
            [
                Label(
                    text="Apply filters   F3 | Filter Query  F4 | Complete query  F5",
                    style="class:title-line",
                ),
                Label(
                    text="Press TAB to go to next dropdown or line\nPress Shift + TAB to go to the previous dropdown or line",
                    style="fg:ansiblue",
                ),
            ],
            padding=1,
            height=Dimension(weight=0.5),
        )

        self.actions_container = HSplit(
            [
                Label(
                    text="Choose actions  F6",
                    style="class:title-line",
                ),
                Label(
                    text="Actions here",
                    style="",
                ),
            ],
            padding=1,
            height=Dimension(weight=0.4),
        )

        self.root_container = FloatContainer(
            VSplit(
                [
                    HSplit(
                        [
                            self.data_type_container,
                            Window(height=1, char="-"),
                            self.filter_container,
                            Window(height=1, char="-"),
                            self.actions_container,
                        ],
                        width=Dimension(weight=0.6),
                    ),
                    Window(width=1, char="|"),
                    self.preview_container,
                ]
            ),
            floats=[],
        )

        layout = Layout(self.root_container)

        self.app = Application(
            layout=layout,
            key_bindings=self.get_keybindings(),
            full_screen=True,
            mouse_support=True,
            style=self.get_style(),
        )

    def get_keybindings(self):
        kb = KeyBindings()

        @kb.add("c-q")
        def _(event):
            print("exiting")
            event.app.exit()

        kb.add("tab")(focus_next)
        kb.add("s-tab")(focus_previous)

        return kb

    def get_style(self):
        return Style([("title-line", "bg:ansigray fg:white")])


gui = MaintenanceGUI()
gui.app.run()
