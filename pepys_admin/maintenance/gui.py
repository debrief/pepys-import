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
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets.base import Label

from pepys_admin.maintenance.widgets.checkbox_table import CheckboxTable
from pepys_admin.maintenance.widgets.combo_box import ComboBox
from pepys_admin.maintenance.widgets.dropdown_box import DropdownBox
from pepys_admin.maintenance.widgets.filter_widget import FilterWidget

logger.remove()
logger.add("gui.log")

platform_column_data = {
    "platform_id": {"type": "id", "values": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]},
    "name": {"type": "string", "values": ["HMS Name1", "HMS Floaty", "USS Sinky"]},
    "identifier": {"type": "string"},
    "nationality_id": {"type": "id"},
    "nationality_name": {"type": "string"},
    "timestamp": {"type": "datetime"},
    "speed": {"type": "float"},
}

sensor_column_data = {
    "sensor_id": {"type": "id"},
    "name": {"type": "string"},
    "sensor_type": {"type": "string", "values": ["GPS", "Sonar", "Inertial"]},
    "host": {"type": "string"},
}

column_data = {"Platform": platform_column_data, "Sensor": sensor_column_data}


class MaintenanceGUI:
    def __init__(self):
        table_data = [
            ["Name", "Type", "Nat."],
            ["NELSON", "Frigate", "UK"],
            ["SARK", "Destroyer", "UK"],
            ["ADRI", "Frigate", "UK"],
            ["JEAN", "Corvette", "FR"],
        ]
        table_objects = [None, 1, 2, 3, 4]

        self.filters_tab = "filters"

        self.preview_container = HSplit(
            children=[
                Label(text="Preview List   F7 | Preview Graph  F8", style="class:title-line"),
                Label(
                    text="Select specific fields to display in preview",
                    style="fg:ansiblue",
                ),
                CheckboxTable(table_data=table_data, table_objects=table_objects),
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
            on_select_handler=self.on_table_select,
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

        self.filter_widget = FilterWidget(on_change_handler=self.on_filter_widget_change)

        self.filter_container = DynamicContainer(self.get_filter_container)
        self.filter_query_buffer = Buffer()
        self.filter_query = BufferControl(self.filter_query_buffer)

        self.actions_container = HSplit(
            [
                Label(
                    text="Choose actions  F6",
                    style="class:title-line",
                ),
                ComboBox(
                    entries=["1 Action here", "2 Another action here", "3 A third action here"],
                    enter_handler=self.run_action,
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

    def on_table_select(self, value):
        self.filter_widget.set_column_data(column_data[value])

    def on_filter_widget_change(self, value):
        self.filter_query_buffer.text = repr(value)

    def run_action(self, selected_value):
        logger.debug(f"Running action {selected_value}")

    def get_keybindings(self):
        kb = KeyBindings()

        @kb.add("c-q")
        @kb.add("escape")
        def _(event):
            print("exiting")
            event.app.exit()

        kb.add("tab")(focus_next)
        kb.add("s-tab")(focus_previous)

        @kb.add("c-a")
        def _(event):
            self.filter_widget.set_column_data({})

        @kb.add("f6")
        def _(event):
            event.app.layout.focus(self.actions_container)

        @kb.add("f3")
        def _(event):
            self.filters_tab = "filters"
            event.app.layout.focus(self.filter_container)

        @kb.add("f4")
        def _(event):
            self.filters_tab = "filter_query"
            event.app.layout.focus(self.filter_container)

        @kb.add("f5")
        def _(event):
            self.filters_tab = "complete_query"
            event.app.layout.focus(self.filter_container)

        return kb

    def get_style(self):
        style = Style(
            [
                ("title-line", "bg:ansigray fg:white"),
                ("button", "#000000"),
                ("button-arrow", "#000000"),
                ("button.focused", "bg:#ff0000"),
                ("dropdown", "bg:#ffff00"),
                ("dropdown.focused", "bg:#ff0000"),
                # ("select-box", "bg:ansiblue"),
                ("text-area focused", "bg:#ff0000"),
                ("dropdown-highlight", "#ff0000"),
                ("filter-text", "fg:#0000ff"),
                ("table-title", "fg:#ff0000"),
                ("checkbox-selected", "bg:ansiyellow"),
            ]
        )
        return style

    def get_filter_container(self):
        top_label = Label(
            text="Apply filters   F3 | Filter Query  F4 | Complete query  F5",
            style="class:title-line",
        )
        if self.filters_tab == "filters":
            return HSplit(
                [
                    top_label,
                    Label(
                        text="Press TAB to go to next dropdown or line\nPress Shift + TAB to go to the previous dropdown or line",
                        style="fg:ansiblue",
                    ),
                    self.filter_widget,
                ],
                padding=1,
                height=Dimension(weight=0.5),
            )
        elif self.filters_tab == "filter_query":
            return HSplit(
                [
                    top_label,
                    Window(self.filter_query),
                ],
                padding=1,
                height=Dimension(weight=0.5),
            )
        elif self.filters_tab == "complete_query":
            buffer = Buffer()
            buffer.text = "Not implemented yet"
            return HSplit(
                [
                    top_label,
                    Window(BufferControl(buffer)),
                ],
                padding=1,
                height=Dimension(weight=0.5),
            )


gui = MaintenanceGUI()
gui.app.run()
