from loguru import logger
from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.layout.containers import (
    DynamicContainer,
    FloatContainer,
    HorizontalAlign,
    HSplit,
    VSplit,
    Window,
)
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets.base import Button, Label, TextArea

from pepys_admin.maintenance.widgets.dropdown_box import ComboBox, DropdownBox

logger.remove()
logger.add("gui.log")

ta = TextArea("blah")


class MaintenanceGUI:
    def __init__(self):
        self.filter_entries = [FilterEntry(self), FilterEntry(self)]
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

        self.button = None

        self.dropdown_table = DropdownBox(
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
        self.data_type_container = HSplit(
            children=[
                Label(text="Select data type   F2", style="class:title-line"),
                VSplit(
                    [self.dropdown_table],
                    align=HorizontalAlign.LEFT,
                ),
            ],
            padding=1,
            height=Dimension(weight=0.05),
        )

        self.filter_container = DynamicContainer(self.get_filter_container)

        self.actions_container = HSplit(
            [
                Label(
                    text="Choose actions  F6",
                    style="class:title-line",
                ),
                ComboBox(
                    entries=["1 Action here", "2 Another action here", "3 A third action here"]
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

        @kb.add("c-a")
        def _(event):
            self.add_filter_entry()

        kb.add("tab")(focus_next)
        kb.add("s-tab")(focus_previous)

        return kb

    def get_style(self):
        style = Style(
            [
                ("title-line", "bg:ansigray fg:white"),
                ("button", "#000000"),
                ("button-arrow", "#000000"),
                ("button.focused", "fg:#ff0000"),
                ("dropdown", "bg:ansigreen"),
                ("dropdown.focused", "bg:ansired"),
                # ("select-box", "bg:ansiblue"),
                ("text-area focused", "bg:#ff0000"),
                ("dropdown-highlight", "#ff0000"),
                ("filter-text", "fg:#0000ff"),
            ]
        )
        return style

    def get_columns(self):
        if self.dropdown_table.text == "Platform":
            return ["platform_id", "name", "identifier", "trigraph", "quadgraph", "etc"]
        elif self.dropdown_table.text == "Sensor":
            return ["sensor_id", "name", "sensor_type", "host", "etc"]
        else:
            return []

    def get_filter_container(self):
        filter_entry_widgets = [entry.get_widgets() for entry in self.filter_entries]
        labels = [
            Label(
                text="Apply filters   F3 | Filter Query  F4 | Complete query  F5",
                style="class:title-line",
            ),
            Label(
                text="Press TAB to go to next dropdown or line\nPress Shift + TAB to go to the previous dropdown or line",
                style="fg:ansiblue",
            ),
        ]
        self.button = Button(text="Add new entry", handler=lambda: logger.debug("Clicked!!"))
        self.h_split_contents = labels + filter_entry_widgets + [ta]
        # self.h_split_contents = [ta]
        result = HSplit(
            self.h_split_contents,
            padding=1,
            height=Dimension(weight=0.5),
        )

        return result

    def add_filter_entry(self):
        self.filter_entries.append(FilterEntry(self))


class FilterEntry:
    def __init__(self, gui):
        self.gui = gui
        self.dropdown_column = DropdownBox(text="Select column", entries=self.gui.get_columns)
        self.dropdown_operator = DropdownBox(
            text=" = ", entries=["=", "!=", ">", "<"], filter=False
        )
        self.value_widget = ta

    def get_widgets(self):
        if self.dropdown_column.text == "identifier":
            self.value_widget.text = "Enter identifier"
        else:
            self.value_widget.text = "Enter something else"
        return VSplit(
            [self.dropdown_column, self.dropdown_operator, self.value_widget],
            align=HorizontalAlign.LEFT,
            padding=2,
        )


gui = MaintenanceGUI()
gui.app.run()
