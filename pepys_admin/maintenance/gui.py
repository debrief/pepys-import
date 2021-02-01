import asyncio
import time
from asyncio.tasks import ensure_future
from datetime import datetime
from functools import partial

from loguru import logger
from prompt_toolkit import Application
from prompt_toolkit.application.current import get_app
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.layout.containers import (
    DynamicContainer,
    Float,
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
from prompt_toolkit.widgets.base import Border, Label
from sqlalchemy.orm import undefer

from pepys_admin.maintenance.dialogs.confirmation_dialog import ConfirmationDialog
from pepys_admin.maintenance.dialogs.help_dialog import HelpDialog
from pepys_admin.maintenance.dialogs.message_dialog import MessageDialog
from pepys_admin.maintenance.dialogs.platform_merge_dialog import PlatformMergeDialog
from pepys_admin.maintenance.dialogs.progress_dialog import ProgressDialog
from pepys_admin.maintenance.dialogs.selection_dialog import SelectionDialog
from pepys_admin.maintenance.widgets.checkbox_table import CheckboxTable
from pepys_admin.maintenance.widgets.combo_box import ComboBox
from pepys_admin.maintenance.widgets.dropdown_box import DropdownBox
from pepys_admin.maintenance.widgets.filter_widget import FilterWidget
from pepys_admin.maintenance.widgets.filter_widget_utils import filter_widget_output_to_query
from pepys_import.core.store.data_store import DataStore

logger.remove()
logger.add("gui.log")

platform_column_data = {
    "platform_id": {"type": "id", "values": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]},
    "name": {"type": "string", "values": ["ADRI", "JEAN", "HMS Floaty", "USS Sinky"]},
    "identifier": {"type": "string"},
    "trigraph": {"type": "string"},
    "quadgraph": {"type": "string"},
    "nationality_id": {"type": "id"},
    "nationality name": {"type": "string", "system_name": "nationality_name"},
    "platform type name": {"type": "string", "system_name": "platform_type_name"},
    "privacy name": {"type": "string", "system_name": "privacy_name"},
}

sensor_column_data = {
    "sensor_id": {"type": "id"},
    "name": {"type": "string"},
    "sensor_type": {"type": "string", "values": ["GPS", "Sonar", "Inertial"]},
    "host": {"type": "string"},
}

column_data = {"Platform": platform_column_data, "Sensor": sensor_column_data}


class MaintenanceGUI:
    def __init__(self, data_store=None):
        if data_store is not None:
            self.data_store = data_store
        else:
            # TODO: Remove this, it's just for ease of testing/development at the moment
            self.data_store = DataStore("", "", "", 0, "test_gui.db", db_type="sqlite")
            self.data_store.initialise()
            with self.data_store.session_scope():
                self.data_store.populate_reference()
                self.data_store.populate_metadata()

        self.preview_selected_fields = [
            "name",
            "identifier",
            "nationality_name",
            "platform_type_name",
        ]

        self.table_data = []
        self.table_objects = []

        self.filters_tab = "filters"
        self.preview_tab = "table"

        self.preview_table = CheckboxTable(
            table_data=self.get_table_data, table_objects=self.get_table_objects
        )
        self.preview_graph = Window(
            BufferControl(Buffer(document=Document("Graph here", 0), read_only=True))
        )

        self.preview_container = DynamicContainer(self.get_preview_container)

        self.dropdown_table = DropdownBox(
            text="Select a table",
            entries=[
                "Platform",
                "Sensor",
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

        self.filter_widget = FilterWidget(
            on_change_handler=self.on_filter_widget_change, max_filters=None
        )

        self.filter_container = DynamicContainer(self.get_filter_container)
        self.filter_query_buffer = Buffer()
        self.filter_query = BufferControl(self.filter_query_buffer)

        self.actions_container = HSplit(
            [
                Label(
                    text="Choose actions  F8",
                    style="class:title-line",
                ),
                ComboBox(
                    entries=[
                        "1 - Merge Platforms",
                        "2 - Test Progressbar",
                        "3 - A third action here",
                    ],
                    enter_handler=self.run_action,
                ),
            ],
            padding=1,
            height=Dimension(weight=0.2),
        )

        self.status_bar_shortcuts = ["Ctrl-F - Select fields"]
        self.status_bar_container = DynamicContainer(self.get_status_bar_container)

        self.root_container = FloatContainer(
            HSplit(
                [
                    VSplit(
                        [
                            HSplit(
                                [
                                    self.data_type_container,
                                    Window(height=1, char=Border.HORIZONTAL),
                                    self.filter_container,
                                    Window(height=1, char=Border.HORIZONTAL),
                                    self.actions_container,
                                ],
                                width=Dimension(weight=0.6),
                            ),
                            Window(width=1, char=Border.VERTICAL),
                            self.preview_container,
                        ],
                        height=Dimension(weight=1),
                    ),
                    Window(height=1, char=Border.HORIZONTAL),
                    self.status_bar_container,
                ],
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

    def get_table_titles(self, fields):
        results = []
        for field in fields:
            splitted = field.split("_")
            if len(splitted) > 1 and splitted[-1] == "name":
                field_title = " ".join(splitted[:-1])
            else:
                field_title = " ".join(splitted)

            results.append(field_title.capitalize())

        return results

    def run_query(self):
        logger.debug("Running query")
        filters = self.filter_widget.filters
        with self.data_store.session_scope():
            if filters == []:
                query_obj = self.data_store.session.query(self.data_store.db_classes.Platform)
            else:
                filter_query = filter_widget_output_to_query(filters, "Platforms", self.data_store)
                query_obj = self.data_store.session.query(
                    self.data_store.db_classes.Platform
                ).filter(filter_query)
            logger.debug(f"{query_obj=!s}")
            results = query_obj.options(undefer("*")).all()
            logger.debug(results)

            if len(results) == 0:
                self.table_data = []
                self.table_objects = []
                app = get_app()
                app.invalidate()
                return

            self.table_data = [self.get_table_titles(self.preview_selected_fields)]
            self.table_objects = [None]

            self.data_store.session.expunge_all()

            for result in results:
                self.table_data.append(
                    [
                        str(getattr(result, field_name))
                        for field_name in self.preview_selected_fields
                    ]
                )
                self.table_objects.append(result)

        app = get_app()
        app.invalidate()
        logger.debug("Ran query")
        logger.debug(f"{self.table_data=}")

    def create_platforms(self):
        with self.data_store.session_scope():
            change_id = self.data_store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id
            nationality = self.data_store.add_to_nationalities("test_nationality", change_id).name
            platform_type = self.data_store.add_to_platform_types(
                "test_platform_type", change_id
            ).name
            privacy = self.data_store.add_to_privacies("test_privacy", 0, change_id).name
            _ = self.data_store.get_platform(
                platform_name="Test Platform 1",
                nationality=nationality,
                platform_type=platform_type,
                privacy=privacy,
                change_id=change_id,
            )
            _ = self.data_store.get_platform(
                platform_name="Test Platform 2",
                nationality=nationality,
                platform_type=platform_type,
                privacy=privacy,
                change_id=change_id,
            )

    def get_table_data(self):
        return self.table_data

    def get_table_objects(self):
        return self.table_objects

    def on_table_select(self, value):
        self.filter_widget.set_column_data(column_data[value])
        self.run_query()

    def on_filter_widget_change(self, value):
        if value != []:
            filter_query = filter_widget_output_to_query(value, "Platforms", self.data_store)
            query_obj = self.data_store.session.query(self.data_store.db_classes.Platform).filter(
                filter_query
            )
            self.filter_query_buffer.text = str(query_obj)
        logger.debug(f"Filter widget output = {value}")
        self.run_query()

    def run_action(self, selected_value):
        if selected_value == "1 - Merge Platforms":
            self.run_merge_platforms()
        elif selected_value == "2 - Test Progressbar":

            async def coroutine():
                dialog = ProgressDialog("Test progressbar", self.run_slowly)
                _ = await self.show_dialog_as_float(dialog)

            ensure_future(coroutine())
        else:
            self.show_messagebox("Action", f"Running action {selected_value}")

    def run_merge_platforms(self):
        display_to_object = {}
        for platform_obj in self.preview_table.current_values:
            display_str = " - ".join(
                [platform_obj.name, platform_obj.nationality_name, platform_obj.identifier]
            )
            display_to_object[display_str] = platform_obj

        def do_merge(platform_list, master_platform, set_percentage=None, is_cancelled=None):
            set_percentage(10)
            with self.data_store.session_scope():
                self.data_store.merge_platforms(platform_list, master_platform)
            time.sleep(3)
            set_percentage(90)
            time.sleep(1)
            set_percentage(100)

        async def coroutine():
            dialog = PlatformMergeDialog(list(display_to_object.keys()))
            dialog_result = await self.show_dialog_as_float(dialog)
            if dialog_result is not None:
                master_platform_obj = display_to_object[dialog_result]
                logger.debug("Got result")

                dialog = ProgressDialog(
                    "Merging platforms",
                    partial(do_merge, self.preview_table.current_values, master_platform_obj),
                    show_cancel=False,
                )
                _ = await self.show_dialog_as_float(dialog)
                await self.show_messagebox_async("Merge completed")
                self.run_query()
                logger.debug("Ran query")

        ensure_future(coroutine())

    async def async_run_slowly(self, set_percentage, is_cancelled):
        for i in range(11):
            await asyncio.sleep(0.4)
            logger.debug(f"At iteration {i}")
            set_percentage((i / 10.0) * 100.0)
            if is_cancelled():
                return

    def run_slowly(self, set_percentage, is_cancelled):
        for i in range(11):
            time.sleep(1)
            logger.debug(f"At iteration {i}")
            set_percentage((i / 10.0) * 100.0)
            if is_cancelled():
                return

    def get_keybindings(self):
        kb = KeyBindings()

        @kb.add("c-q")
        @kb.add("escape")
        def _(event):
            async def coroutine():
                dialog = ConfirmationDialog("Exit?", "Do you want to exit?")
                result = await self.show_dialog_as_float(dialog)
                if result:
                    event.app.exit()

            ensure_future(coroutine())

        kb.add("tab")(focus_next)
        kb.add("s-tab")(focus_previous)

        @kb.add("c-r")
        def _(event):
            self.run_query()

        @kb.add("c-f")
        def _(event):
            async def coroutine():
                (
                    system_name_to_display_name,
                    display_name_to_system_name,
                ) = self.get_system_name_mappings(column_data["Platform"])

                # Get lists of left-hand and right-hand side entries
                # The left-hand entries are all available fields (minus those that already appear on the right)
                # and the right-hand entries are the currently selected fields
                left_entries = list(display_name_to_system_name.keys())
                right_entries = [
                    system_name_to_display_name[entry] for entry in self.preview_selected_fields
                ]

                left_entries = list(set(left_entries).difference(set(right_entries)))

                dialog = SelectionDialog(left_entries, right_entries, "Select fields")
                selected_fields = await self.show_dialog_as_float(dialog)

                # Convert these back to system names
                self.preview_selected_fields = [
                    display_name_to_system_name[entry] for entry in selected_fields
                ]
                self.run_query()

            ensure_future(coroutine())

        @kb.add("f1")
        def _(event):
            async def coroutine():
                dialog = HelpDialog("Help", "Help text here\n" * 50)
                await self.show_dialog_as_float(dialog)

            ensure_future(coroutine())

        @kb.add("f2")
        def _(event):
            event.app.layout.focus(self.data_type_container)

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

        @kb.add("f6")
        def _(event):
            self.preview_tab = "table"
            self.status_bar_shortcuts = ["Ctrl-F - Select fields"]
            event.app.layout.focus(self.preview_container)

        @kb.add("f7")
        def _(event):
            self.preview_tab = "graph"
            self.status_bar_shortcuts = ["Ctrl-U - Update graph"]
            event.app.layout.focus(self.preview_container)

        @kb.add("f8")
        def _(event):
            event.app.layout.focus(self.actions_container)

        return kb

    def get_system_name_mappings(self, column_data):
        system_name_to_display_name = {}
        display_name_to_system_name = {}

        for key, entry in column_data.items():
            if entry.get("system_name", None) is not None:
                system_name = entry.get("system_name")
            else:
                system_name = key

            system_name_to_display_name[system_name] = key
            display_name_to_system_name[key] = system_name

        return system_name_to_display_name, display_name_to_system_name

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
                ("status-bar-text", "bg:ansigray"),
            ]
        )
        return style

    async def show_dialog_as_float(self, dialog):
        " Coroutine. "
        float_ = Float(content=dialog)
        self.root_container.floats.insert(0, float_)

        app = get_app()

        focused_before = app.layout.current_window
        try:
            app.layout.focus(dialog)
        except ValueError:
            pass

        result = await dialog.future

        try:
            app.layout.focus(focused_before)
        except Exception:
            pass

        if float_ in self.root_container.floats:
            self.root_container.floats.remove(float_)

        return result

    async def show_messagebox_async(self, title, text=None):
        dialog = MessageDialog(title, text)
        await self.show_dialog_as_float(dialog)

    def show_messagebox(self, title, text=None):
        ensure_future(self.show_messagebox_async(title, text))

    def get_filter_container(self):
        # top_label = VSplit(
        #     [
        #         Label(
        #             text="Build filters  F3",
        #             style="class:title-line",
        #             dont_extend_width=True
        #         ),
        #         Label(text=" | ", style="class:title-line", width=3),
        #         Label(text="Show Filter Query  F4", style="class:title-line", dont_extend_width=True),
        #         Label(text=" | ", style="class:title-line", width=3),
        #         Label(text="Show complete query  F5", style="class:title-line", dont_extend_width=True),
        #         Label(" ", style="class:title-line", width=Dimension(weight=10))
        #     ],
        #     align=HorizontalAlign.LEFT,
        #     padding=0
        # )
        top_label = Label(
            text="Build filters  F3 | Show Filter Query  F4 | Show complete query  F5",
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
                height=Dimension(weight=0.70),
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

    def get_preview_container(self):
        title_label = Label(text="Preview List   F6 | Preview Graph  F7", style="class:title-line")
        if self.preview_tab == "table":
            return HSplit(
                children=[
                    title_label,
                    Label(
                        text="Use Ctrl-F to select fields to display",
                        style="fg:ansiblue",
                    ),
                    self.preview_table,
                ],
                padding=1,
                width=Dimension(weight=0.4),
            )
        elif self.preview_tab == "graph":
            return HSplit(
                children=[
                    title_label,
                    self.preview_graph,
                ],
                padding=1,
                width=Dimension(weight=0.4),
            )

    def get_status_bar_container(self):
        return VSplit(
            [
                VSplit(
                    [
                        Label("ESC - Exit", style="class:status-bar-text", dont_extend_width=True),
                        Label("F1 - Help", style="class:status-bar-text", dont_extend_width=True),
                    ],
                    padding=3,
                    align=HorizontalAlign.LEFT,
                    height=1,
                ),
                VSplit(
                    [
                        Label(
                            text,
                            style="class:status-bar-text",
                            dont_extend_width=True,
                        )
                        for text in self.status_bar_shortcuts
                    ],
                    padding=3,
                    align=HorizontalAlign.RIGHT,
                    height=1,
                ),
            ]
        )


if __name__ == "__main__":
    gui = MaintenanceGUI()
    gui.app.run()
