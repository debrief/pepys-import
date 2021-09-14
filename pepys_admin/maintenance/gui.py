import os
import textwrap
import traceback
import uuid
from asyncio.tasks import ensure_future
from datetime import datetime
from functools import partial

import sqlalchemy
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
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.lexers.pygments import PygmentsLexer
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets.base import Border, Label
from pygments.lexers.sql import SqlLexer
from sqlalchemy.orm import undefer

from pepys_admin.maintenance.column_data import convert_column_data_to_edit_data, create_column_data
from pepys_admin.maintenance.dialogs.add_dialog import AddDialog
from pepys_admin.maintenance.dialogs.confirmation_dialog import ConfirmationDialog
from pepys_admin.maintenance.dialogs.edit_dialog import EditDialog
from pepys_admin.maintenance.dialogs.export_csv_dialog import ExportCSVDialog
from pepys_admin.maintenance.dialogs.help_dialog import HelpDialog
from pepys_admin.maintenance.dialogs.initial_help_dialog import InitialHelpDialog
from pepys_admin.maintenance.dialogs.merge_dialog import MergeDialog
from pepys_admin.maintenance.dialogs.message_dialog import MessageDialog
from pepys_admin.maintenance.dialogs.progress_dialog import ProgressDialog
from pepys_admin.maintenance.dialogs.selection_dialog import SelectionDialog
from pepys_admin.maintenance.dialogs.view_dialog import ViewDialog
from pepys_admin.maintenance.help import HELP_TEXT, INTRO_HELP_TEXT
from pepys_admin.maintenance.utils import (
    get_display_names,
    get_str_for_field,
    get_system_name_mappings,
)
from pepys_admin.maintenance.widgets.advanced_combo_box import AdvancedComboBox
from pepys_admin.maintenance.widgets.blank_border import BlankBorder
from pepys_admin.maintenance.widgets.checkbox_table import CheckboxTable
from pepys_admin.maintenance.widgets.dropdown_box import DropdownBox
from pepys_admin.maintenance.widgets.filter_widget import FilterWidget
from pepys_admin.maintenance.widgets.filter_widget_utils import filter_widget_output_to_query
from pepys_import.core.store.data_store import USER, DataStore
from pepys_import.core.store.db_status import TableTypes
from pepys_import.utils.data_store_utils import convert_objects_to_ids
from pepys_import.utils.sqlalchemy_utils import get_primary_key_for_table
from pepys_import.utils.table_name_utils import table_name_to_class_name

logger.remove()
logger.add("gui.log")

# Uncomment the lines below to get logging of the SQL queries run by SQLAlchemy
# to the file sql.log
# import logging
# logging.basicConfig(filename='sql.log', level=logging.DEBUG)
# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

MAX_PREVIEW_TABLE_RESULTS = 100


class MaintenanceGUI:
    def __init__(self, data_store=None):
        if data_store is not None:
            self.data_store = data_store
        else:
            # This is for testing/development.
            # It won't cause problems for users, as they will access via Pepys Admin
            # where data store will be defined
            self.data_store = DataStore(
                "", "", "", 0, "test_gui.db", db_type="sqlite", show_status=False, welcome_text=""
            )
            self.data_store.initialise()
            with self.data_store.session_scope():
                self.data_store.populate_reference()
                self.data_store.populate_metadata()

        if self.data_store.in_memory_database:
            raise ValueError("Cannot run the GUI on an in-memory SQLite database")

        self.data_store.setup_table_type_mapping()

        try:
            # This calls a simple function to check if the Privacies table has entries
            # We don't actually care if it has entries, but it is a good simple query
            # to run which checks if the database has been initialised
            with self.data_store.session_scope():
                _ = self.data_store.is_empty()
        except Exception:
            raise ValueError(
                "Cannot run GUI on a non-initialised database. Please run initialise first."
            )

        # Start with an empty table
        self.table_data = []
        self.table_objects = []

        self.filters_tab = "filters"
        self.preview_tab = "table"

        # A dict to link Window objects to strings to search for in the help
        # text. This is used to display contextual help by getting the current
        # window, looking up the text to search for, and displaying a help dialog
        # focused on that text
        self.contextual_help = {}
        self.current_dialog = None

        self.init_ui_components()

        self.current_table_object = None

        self.column_data = None
        self.edit_data = None
        self.preview_selected_fields = []

        self.filter_widget.set_column_data(self.column_data)
        self.run_query()

        self.app = Application(
            layout=self.layout,
            key_bindings=self.get_keybindings(),
            full_screen=True,
            mouse_support=True,
            style=self.get_style(),
        )

        self.app.dropdown_opened = False

    def init_ui_components(self):
        """Initialise all of the UI components, controls, containers and widgets"""
        # Dropdown box to select table, plus pane that it is in
        metadata_tables = [
            "Platforms",
            "Sensors",
            "Datafiles",
            "Series",
            "Wargames",
            "Serials",
            "WargameParticipants",
            "SerialParticipants",
            "ConfigOptions",
        ]
        measurement_tables = sorted(
            [mc.__tablename__ for mc in self.data_store.meta_classes[TableTypes.MEASUREMENT]]
        )
        reference_tables = sorted(
            [mc.__tablename__ for mc in self.data_store.meta_classes[TableTypes.REFERENCE]]
        )
        reference_tables.remove("HelpTexts")
        tables_list = metadata_tables + measurement_tables + reference_tables
        self.dropdown_table = DropdownBox(
            text="Select a table",
            entries=tables_list,
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
            height=Dimension(weight=0.1),
        )

        # Filter pane, containing FilterWidget plus buffers for the
        # text showing the SQL
        self.filter_widget = FilterWidget(
            on_change_handler=self.on_filter_widget_change,
            max_filters=None,
            contextual_help_setter=self.set_contextual_help,
            filter_function=self.filter_column_data,
        )
        self.set_contextual_help(self.filter_widget, "# Second panel: Build filters F3")
        self.filter_container = DynamicContainer(self.get_filter_container)

        lexer = PygmentsLexer(SqlLexer)

        # Buffer to hold just the filter part of the query in SQL form
        self.filter_query_buffer = Buffer()
        self.filter_query = BufferControl(self.filter_query_buffer, lexer=lexer)
        self.filter_query_window = Window(self.filter_query)

        # Buffer to hold the complete query in SQL form
        self.complete_query_buffer = Buffer()
        self.complete_query = BufferControl(self.complete_query_buffer, lexer=lexer)
        self.complete_query_window = Window(self.complete_query)

        # Actions container, containing a list of actions that can be run
        self.actions_combo = AdvancedComboBox(
            entries=self.get_actions_list,
            enter_handler=self.run_action,
        )
        self.set_contextual_help(self.actions_combo, "# Fourth panel: Choose actions (F8)")
        self.actions_container = HSplit(
            [
                Label(
                    text="Choose actions  F8",
                    style="class:title-line",
                ),
                self.actions_combo,
            ],
            padding=1,
            height=Dimension(weight=0.23),
        )

        # Preview container, with two tabs: a preview table and a preview graph
        self.preview_table_message = Label("")
        self.preview_table = CheckboxTable(
            table_data=self.get_table_data,
            table_objects=self.get_table_objects,
            any_keybinding=self.handle_preview_table_keypress,
            on_select=self.update_selected_items_label,
        )
        self.set_contextual_help(self.preview_table, "# Third panel: Preview List (F6)")
        self.preview_graph = Window(
            BufferControl(Buffer(document=Document("Graph here", 0), read_only=True))
        )
        self.preview_container = DynamicContainer(self.get_preview_container)

        # Status bar
        self.status_bar_shortcuts = ["Ctrl-F - Select fields"]
        self.status_bar_container = DynamicContainer(self.get_status_bar_container)

        initial_floats = [
            Float(
                xcursor=True,
                ycursor=True,
                content=CompletionsMenu(max_height=16, scroll_offset=1),
            )
        ]

        show_initial_help = not os.path.exists(
            os.path.expanduser(os.path.join("~", ".pepys_maintenance_help.txt"))
        )

        if show_initial_help:
            initial_help_dialog = InitialHelpDialog("Getting started", INTRO_HELP_TEXT)
            initial_floats.append(Float(initial_help_dialog))

        # Putting everything together in panes
        self.root_container = FloatContainer(
            BlankBorder(
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
                )
            ),
            floats=initial_floats,
        )

        if show_initial_help:
            self.layout = Layout(
                self.root_container, focused_element=initial_help_dialog.close_button
            )
        else:
            self.layout = Layout(self.root_container)

    def handle_preview_table_keypress(self, event):
        self.actions_combo.handle_numeric_key(event)

    def update_selected_items_label(self):
        # The `- 1` is because table_objects has a None entry for the header row
        total_items = len(self.table_objects) - 1 + self.preview_table.non_visible_items_count
        visible_items = len(self.table_objects) - 1
        selected_items = len(self.preview_table.current_values)
        if self.preview_table.non_visible_selected:
            selected_items += self.preview_table.non_visible_items_count

        self.preview_table_message.text = f"{visible_items} of {total_items} matching entries displayed, {selected_items} selected"
        get_app().invalidate()

    def get_actions_list(self):
        def is_merge_enabled():
            return (
                len(self.preview_table.current_values) > 1
                and self.current_table_object.table_type != TableTypes.MEASUREMENT
            )

        def is_split_platform_enabled():
            return (self.current_table_object == self.data_store.db_classes.Platform) and (
                len(self.preview_table.current_values) == 1
            )

        def is_edit_values_enabled():
            return len(self.preview_table.current_values) > 0

        def is_delete_entries_enabled():
            return len(self.preview_table.current_values) > 0

        def is_add_entries_enabled():
            return self.current_table_object is not None

        def is_view_entry_enabled():
            return len(self.preview_table.current_values) == 1

        def is_csv_export_enabled():
            return len(self.preview_table.current_values) > 0

        return [
            ("1 - Merge", is_merge_enabled()),
            ("2 - Split platform", is_split_platform_enabled()),
            ("3 - Edit values", is_edit_values_enabled()),
            ("4 - Delete entries", is_delete_entries_enabled()),
            ("5 - Add entry", is_add_entries_enabled()),
            ("6 - View entry", is_view_entry_enabled()),
            ("7 - Export as CSV", is_csv_export_enabled()),
        ]

    def set_contextual_help(self, widget, text):
        """Sets the contextual help dictionary based on the widget's
        container"""
        self.contextual_help[widget.__pt_container__()] = text

    def get_default_preview_fields(self):
        self.preview_selected_fields = self.current_table_object._default_preview_fields

    def filter_column_data(self, column_data):
        """
        Filters the column_data dict in the FilterWidget to remove entries
        that we don't currently want the user to be able to select - such as location,
        or float columns
        """
        # FUTURE: Remove this when we want to be able to filter by measurements or location
        new_column_data = {}
        for display_name, col_config in column_data.items():
            # Don't allow the location field
            if display_name == "location":
                continue
            # Don't allow any float columns
            elif col_config["type"] == "float":
                continue
            # Don't allow any relationship columns to reference tables - we deal with those by their association proxies
            elif (
                col_config["sqlalchemy_type"] == "relationship"
                and col_config["foreign_table_type"] == TableTypes.REFERENCE
            ):
                continue
            new_column_data[display_name] = col_config

        return new_column_data

    def run_query(self):
        """Runs the query as defined by the FilterWidget,
        and displays the result in the preview table."""
        if self.current_table_object is None:
            return

        app = get_app()
        # As this property is computed each time we access it, get the output and store it
        # to save time
        filters = self.filter_widget.filters

        # Convert the selected fields to sensible table titles
        self.table_data = [get_display_names(self.preview_selected_fields, capitalized=True)]
        # The first of the table objects should be None, as that is the header field
        # and doesn't have a table object associated with it
        self.table_objects = [None]

        try:
            with self.data_store.session_scope():
                if filters == []:
                    # If there are no filters then just return the table with no filtering
                    query_obj = self.data_store.session.query(self.current_table_object)
                else:
                    # Otherwise, convert the filter widget output to a SQLAlchemy filter and run it
                    filter_query = filter_widget_output_to_query(
                        filters, self.dropdown_table.text, self.data_store
                    )
                    if filter_query is None:
                        app.invalidate()
                        return
                    query_obj = self.data_store.session.query(self.current_table_object).filter(
                        filter_query
                    )

                count = query_obj.count()

                # Get the first 100 results, while undefering all fields to make sure everything is
                # available once it's been expunged (disconnected) from the database
                results = query_obj.options(undefer("*")).limit(MAX_PREVIEW_TABLE_RESULTS).all()

                if len(results) == 0:
                    self.preview_table_message.text = ""
                    # If we've got no results then just update the app display
                    # which will just show the headers that we mentioned above
                    app.invalidate()
                    return

                for result in results[:MAX_PREVIEW_TABLE_RESULTS]:
                    # Get the right fields and append them
                    self.table_data.append(
                        [
                            get_str_for_field(getattr(result, field_name))
                            for field_name in self.preview_selected_fields
                        ]
                    )
                    self.table_objects.append(result)

                # Disconnect all the objects we've returned in our query from the database
                # so we can store them outside of the session without any problems
                self.data_store.session.expunge_all()

                if count > MAX_PREVIEW_TABLE_RESULTS:
                    self.preview_table.non_visible_items_count = count - MAX_PREVIEW_TABLE_RESULTS
                else:
                    self.preview_table.non_visible_items_count = 0
                    self.preview_table.non_visible_selected = False
        except Exception:
            # Just ignore it if the query doesn't work - as we're updating live
            # and the user might type something correct soon anyway
            pass

        # Force the list of currently selected rows to be empty here
        # This is also done in CheckboxTable itself, but because of the async nature of the code
        # it isn't always run in the right order. This forces this to be empty before updating
        # the selected items label
        self.preview_table.current_values = []
        self.update_selected_items_label()

    def get_table_data(self):
        return self.table_data

    def get_table_objects(self):
        return self.table_objects

    def get_non_visible_entries_from_database(self, set_percentage=None, is_cancelled=None):
        """Queries the database to return IDs (UUIDs) for items that aren't shown in the preview table.

        This is only called when getting a full list of entries ready to perform an action, and if
        the non-visible items have been selected, which saves loading all of the non-visible items
        from the database if we don't need them. It also only loads IDs, as this is significantly quicker than
        loading full objects (eg. for around 100,000 State items, a test showed it took around 25-30s to load
        all of the entries into objects, but less than 1s to load the IDs)
        """
        filters = self.filter_widget.filters

        id_column = getattr(
            self.current_table_object,
            get_primary_key_for_table(self.current_table_object),
        )

        set_percentage(10)

        with self.data_store.session_scope():
            if filters == []:
                # If there are no filters then just return the table primary key with no filtering
                query_obj = self.data_store.session.query(id_column)
            else:
                # Otherwise, convert the filter widget output to a SQLAlchemy filter and run it
                filter_query = filter_widget_output_to_query(
                    filters, self.dropdown_table.text, self.data_store
                )
                query_obj = self.data_store.session.query(id_column).filter(filter_query)

            set_percentage(20)

            # Get all result IDs
            results = query_obj.all()
            results = [result[0] for result in results]

            set_percentage(90)

            # Remove the IDs that we already have in the preview table
            visible_ids = [
                getattr(entry, get_primary_key_for_table(self.current_table_object))
                for entry in self.preview_table.current_values
            ]
            just_non_visible_ids = list(set(results) - set(visible_ids))

        set_percentage(100)

        return just_non_visible_ids

    async def get_all_selected_entries(self):
        """Gets a list of all currently-selected items, which includes all selected items in the preview table,
        plus all the non-visible items if those are selected too.

        The result will be a mixture of item objects (eg. Platform objects) and item IDs (UUID objects) - and
        any function that does processing based on the output of this function must be able to deal with a mixed
        list.
        (The list is mixed as we still need the full information on the first few items, for displaying previews/confirmation
        dialogs, but we don't need to load the full items from the database for all the non-visible items as we're only
        going to use the IDs in the actual processing - and there may be lots of items to load)
        """
        if not self.preview_table.non_visible_selected:
            # No non-visible selected, so just return the selected ones from the preview table
            return self.preview_table.current_values

        dialog = ProgressDialog(
            "Loading selected items data",
            self.get_non_visible_entries_from_database,
            show_cancel=False,
        )
        result = await self.show_dialog_as_float(dialog)

        if isinstance(result, Exception):
            await self.show_messagebox_async(
                "Error",
                f"Error accessing database\n\nOriginal error:{str(result)}",
            )

        return self.preview_table.current_values + result

    def get_column_data(self, table_object, set_percentage=None, is_cancelled=None):
        self.column_data = create_column_data(self.data_store, table_object, set_percentage)
        # Reset this to None now that we've got new column data (basically invalidating
        # the cache of the edit data)
        self.edit_data = None

    def on_table_select(self, value):
        """Called when an entry is selected from the Table dropdown at the top-left."""
        class_name = table_name_to_class_name(value)
        self.current_table_object = getattr(self.data_store.db_classes, class_name)

        # Set the data used to parameterise the FilterWidget
        async def coroutine():
            dialog = ProgressDialog(
                "Loading table data",
                partial(self.get_column_data, self.current_table_object),
                show_cancel=False,
            )
            result = await self.show_dialog_as_float(dialog)

            if isinstance(result, Exception):
                await self.show_messagebox_async(
                    "Error",
                    f"Error accessing database - is it initialised?\n\nOriginal error:{textwrap.fill(str(result), 30)}",
                )

            self.filter_widget.set_column_data(self.column_data)
            self.get_default_preview_fields()
            self.run_query()

        ensure_future(coroutine())

    def on_filter_widget_change(self, value):
        """Called when the filter widget notifies us that it has changed. The filter
        widget is sensible about this and only raises this event if there has actually been
        a change in the output of the filters property. That means we can run a query
        each time this is called, and the query shouldn't get run more often than is needed."""
        # Convert the filter object to a SQL string to display in the Complete Query tab
        if value != []:
            filter_query = filter_widget_output_to_query(
                value, self.dropdown_table.text, self.data_store
            )
            query_obj = self.data_store.session.query(self.data_store.db_classes.Platform).filter(
                filter_query
            )
            sql_string = str(query_obj.statement.compile(compile_kwargs={"literal_binds": True}))
            self.complete_query_buffer.text = textwrap.fill(sql_string, width=70)
            just_where_clause = sql_string[sql_string.index("WHERE") :]
            self.filter_query_buffer.text = textwrap.fill(just_where_clause, width=70)
        self.run_query()

    def run_action(self, selected_value):
        """Runs an action from the actions ComboBox. Called when Enter is pressed."""
        if selected_value == "1 - Merge":
            self.run_merge()
        elif selected_value == "2 - Split platform":
            self.run_split_platform()
        elif selected_value == "3 - Edit values":
            self.run_edit_values()
        elif selected_value == "4 - Delete entries":
            self.run_delete()
        elif selected_value == "5 - Add entry":
            self.run_add()
        elif selected_value == "6 - View entry":
            self.run_view()
        elif selected_value == "7 - Export as CSV":
            self.run_export_csv()
        else:
            self.show_messagebox("Action", f"Running action {selected_value}")

    def run_export_csv(self):
        def do_export_csv(
            table_object, ids, columns_list, output_filename, set_percentage=None, is_cancelled=None
        ):
            self.data_store.export_objects_to_csv(
                table_object, ids, columns_list, output_filename, set_percentage=set_percentage
            )
            set_percentage(100)

        async def coroutine():
            if len(self.preview_table.current_values) == 0:
                await self.show_messagebox_async(
                    "Error", "You must select at least one entry before exporting."
                )
                return

            entries = await self.get_all_selected_entries()
            selected_ids = convert_objects_to_ids(entries, self.current_table_object)

            dialog = ExportCSVDialog(self.column_data)
            result = await self.show_dialog_as_float(dialog)
            columns_list = result["columns"]
            output_filename = result["filename"]

            dialog = ProgressDialog(
                f"Exporting to {os.path.basename(output_filename)}",
                partial(
                    do_export_csv,
                    self.current_table_object,
                    selected_ids,
                    columns_list,
                    output_filename,
                ),
                show_cancel=True,
            )

            result = await self.show_dialog_as_float(dialog)

            if isinstance(result, Exception):
                await self.show_messagebox_async(
                    "Error",
                    f"Error exporting CSV\n\nOriginal error:{textwrap.fill(str(result), 60)}",
                )
                return

            await self.show_messagebox_async(
                "Export completed", f"CSV export to {os.path.basename(output_filename)} completed"
            )

        ensure_future(coroutine())

    def run_view(self):
        async def coroutine():
            if len(self.preview_table.current_values) != 1:
                await self.show_messagebox_async(
                    "Error", "You must select exactly one entry before editing."
                )
                return

            dialog = ViewDialog(
                self.column_data, self.current_table_object, self.preview_table.current_values
            )
            await self.show_dialog_as_float(dialog)

        ensure_future(coroutine())

    def run_add(self):
        def do_add(table_object, edit_dict, set_percentage=None, is_cancelled=None):
            with self.data_store.session_scope():
                self.data_store.add_item(table_object, edit_dict)
            set_percentage(100)

        async def coroutine():
            if self.current_table_object is None:
                await self.show_messagebox_async(
                    "Error", "You must select a table before adding an entry"
                )
                return

            if self.edit_data is None:
                dialog = ProgressDialog(
                    "Preparing to edit", self.create_edit_data, show_cancel=False
                )
                result = await self.show_dialog_as_float(dialog)

            dialog = AddDialog(self.edit_data, self.current_table_object)
            edit_dict = await self.show_dialog_as_float(dialog)
            if edit_dict is None or len(edit_dict) == 0:
                # Dialog was cancelled
                return

            dialog = ProgressDialog(
                "Adding items",
                partial(do_add, self.current_table_object, edit_dict),
                show_cancel=False,
            )
            result = await self.show_dialog_as_float(dialog)

            if isinstance(result, Exception):
                if isinstance(result, sqlalchemy.exc.IntegrityError):
                    await self.show_messagebox_async(
                        "Constraint Error",
                        "Error setting values in the database due to a database constraint.\n\n"
                        "This probably means you have either not set some required values,\n"
                        "tried to set values which violate a uniqueness constraint (for example,\n"
                        "setting multiple platforms to have the same name, identifier and\n"
                        "nationality), or set an invalid value for a column - for example\n"
                        f"a value which is too long.\n\nOriginal error: {textwrap.fill(str(result), 60)}",
                    )
                    return
                else:
                    await self.show_messagebox_async(
                        "Error",
                        f"Error adding entry\n\nOriginal error:{textwrap.fill(str(result), 60)}",
                    )
                    return
            # Once the platform merge is done, show a message box
            # We use the async version of this function as we're calling
            # from within a coroutine
            await self.show_messagebox_async("Add completed")
            # Re-run the query, so we get an updated list in the preview
            # and can see that a new entry has been added
            self.run_query()

        ensure_future(coroutine())

    def run_delete(self):
        def do_delete(table_object, ids, set_percentage=None, is_cancelled=None):
            with self.data_store.session_scope():
                change_id = self.data_store.add_to_changes(
                    USER, datetime.utcnow(), "Manual delete from Maintenance GUI"
                ).change_id
                self.data_store.delete_objects(table_object, ids, change_id=change_id)
            set_percentage(100)

        def do_find_dependent_objects(
            table_object, selected_ids, set_percentage=None, is_cancelled=None
        ):
            with self.data_store.session_scope():
                dependent_objects = self.data_store.find_dependent_objects(
                    table_object,
                    selected_ids,
                    set_percentage=set_percentage,
                    is_cancelled=is_cancelled,
                )
            set_percentage(100)
            return dependent_objects

        async def coroutine():
            entries = await self.get_all_selected_entries()

            if len(entries) == 0:
                await self.show_messagebox_async(
                    "Error", "You must select at least one item before deleting"
                )
                return

            if len(entries) < 10:
                display_strs = []
                for entry in entries:
                    if isinstance(entry, uuid.UUID):
                        continue
                    display_str = " - ".join(
                        [
                            str(getattr(entry, field_name))
                            for field_name in entry._default_preview_fields
                        ]
                    )
                    display_strs.append(display_str)
                selected_items_text = "\n".join(display_strs)
            else:
                selected_items_text = f"{len(entries)} items selected"

            selected_ids = convert_objects_to_ids(entries, self.current_table_object)

            dialog = ProgressDialog(
                "Finding dependent items (may take a while)",
                partial(do_find_dependent_objects, self.current_table_object, selected_ids),
                show_cancel=True,
            )
            dependent_objects = await self.show_dialog_as_float(dialog)

            if isinstance(dependent_objects, Exception):
                await self.show_messagebox_async(
                    "Error",
                    f"Error deleting values\n\nOriginal error:{textwrap.fill(str(dependent_objects), 60)}",
                )
                return
            elif dependent_objects is None:
                return

            dep_objs_text = "\n".join(
                f"{number} {table_name}" for table_name, number in dependent_objects.items()
            )

            dialog = ConfirmationDialog(
                "Delete?",
                f"Deleting these entries:\n\n{selected_items_text}\n\nwill delete the following dependent objects:\n\n{dep_objs_text}",
            )
            result = await self.show_dialog_as_float(dialog)

            if not result:
                # User cancelled
                return

            dialog = ProgressDialog(
                "Deleting items",
                partial(do_delete, self.current_table_object, selected_ids),
                show_cancel=False,
            )
            result = await self.show_dialog_as_float(dialog)

            if isinstance(result, Exception):
                if isinstance(result, sqlalchemy.exc.IntegrityError):
                    await self.show_messagebox_async(
                        "Constraint Error",
                        "Error deleting entries in the database due to a database constraint.\n\n"
                        "This probably means dependent objects haven't been deleted properly.\n"
                        f"\n\nOriginal error: {textwrap.fill(str(result), 60)}",
                    )
                    return
                else:
                    await self.show_messagebox_async(
                        "Error",
                        f"Error deleting values\n\nOriginal error:{textwrap.fill(str(result), 60)}",
                    )
                    return
            await self.show_messagebox_async("Delete completed")
            self.run_query()

        ensure_future(coroutine())

    def create_edit_data(self, set_percentage=None, is_cancelled=None):
        # Convert the column_data into the structure we need for editing the data
        # This removes un-needed columns, and un-needed values lists
        self.edit_data = convert_column_data_to_edit_data(
            self.column_data,
            set_percentage=set_percentage,
        )
        set_percentage(100)

    def run_edit_values(self):
        def do_edit(items, edit_dict, set_percentage=None, is_cancelled=None):
            with self.data_store.session_scope():
                self.data_store.edit_items(items, edit_dict, self.current_table_object)
            set_percentage(100)

        async def coroutine():
            selected_items = await self.get_all_selected_entries()

            if len(selected_items) == 0:
                await self.show_messagebox_async(
                    "Error", "You must select at least one entry before editing."
                )
                return

            if self.edit_data is None:
                dialog = ProgressDialog(
                    "Preparing to edit", self.create_edit_data, show_cancel=False
                )
                result = await self.show_dialog_as_float(dialog)

                if isinstance(result, BaseException):
                    await self.show_messagebox_async(
                        "Error", f"Error preparing edit data\n\nOriginal error: {str(result)}"
                    )
                    return

            dialog = EditDialog(self.edit_data, self.current_table_object, selected_items)

            edit_dict = await self.show_dialog_as_float(dialog)
            if edit_dict is None or len(edit_dict) == 0:
                # Dialog was cancelled
                return

            dialog = ProgressDialog(
                "Editing items",
                partial(do_edit, selected_items, edit_dict),
                show_cancel=False,
            )
            result = await self.show_dialog_as_float(dialog)

            if isinstance(result, Exception):
                if isinstance(result, sqlalchemy.exc.IntegrityError):
                    await self.show_messagebox_async(
                        "Constraint Error",
                        "Error setting values in the database due to a database constraint.\n\n"
                        "This probably means you have tried to set values which violate a\n"
                        "uniqueness constraint - for example, setting multiple platforms to have the\n"
                        f"same name, identifier and nationality.\n\nOriginal error: {textwrap.fill(str(result), 60)}",
                    )
                    return
                else:
                    await self.show_messagebox_async(
                        "Error",
                        f"Error editing values\n\nOriginal error:{textwrap.fill(str(result), 60)}",
                    )
                    return
            # Once the platform merge is done, show a message box
            # We use the async version of this function as we're calling
            # from within a coroutine
            await self.show_messagebox_async("Edit completed")
            # Re-run the query, so we get an updated list in the preview
            # and can see that some platforms have disappeared
            self.run_query()

        ensure_future(coroutine())

    def run_split_platform(self):
        if self.current_table_object != self.data_store.db_classes.Platform:
            self.show_messagebox(
                "Error",
                "The split platform operation only works on the Platform table.\nPlease select this table first.",
            )
            return
        if len(self.preview_table.current_values) != 1:
            self.show_messagebox("Error", "To split a platform you must select only one platform.")
            return

        def do_split(selected_platform, set_percentage=None, is_cancelled=None):
            with self.data_store.session_scope():
                self.data_store.split_platform(selected_platform)
                set_percentage(100)

        async def coroutine():
            selected_platform = self.preview_table.current_values[0]
            platform_details = " - ".join(
                [
                    selected_platform.name,
                    selected_platform.identifier,
                    selected_platform.nationality_name,
                ]
            )
            conf_dialog = ConfirmationDialog(
                "Split platform", f"Do you want to split platform:\n{platform_details}?"
            )
            result = await self.show_dialog_as_float(conf_dialog)
            if not result:
                return

            dialog = ProgressDialog(
                "Splitting Platform",
                partial(do_split, selected_platform),
                show_cancel=False,
            )
            result = await self.show_dialog_as_float(dialog)
            if isinstance(result, Exception):
                await self.show_messagebox_async(
                    "Error",
                    f"Error running split\n\nOriginal error:{textwrap.fill(str(result), 60)}",
                )
                return
            # Once the platform merge is done, show a message box
            # We use the async version of this function as we're calling
            # from within a coroutine
            await self.show_messagebox_async("Split completed")
            # Re-run the query, so we get an updated list in the preview
            # and can see that some platforms have disappeared
            self.run_query()

        ensure_future(coroutine())

    def run_merge(self):
        """Runs the action to merge entries

        Takes the list of entries to merge from the selected items in the preview table,
        then opens a dialog to select the master entry, then runs the merge with a
        progress dialog, and displays a messagebox when it is finished.
        """

        def do_merge(object_list, master_obj, set_percentage=None, is_cancelled=None):
            # Does the actual merge, while also setting the percentage complete
            with self.data_store.session_scope():
                self.data_store.merge_generic(
                    self.dropdown_table.text, object_list, master_obj, set_percentage
                )
            # Force the percentage complete to 100 in case rounding errors inside the function
            # meant it didn't quite make 100%. Setting to >= 100 causes the progress dialog
            # to close, which is what we want
            set_percentage(100)

        async def coroutine():
            selected_items = await self.get_all_selected_entries()

            if len(selected_items) <= 1:
                await self.show_messagebox_async(
                    "Error",
                    "You must select multiple entries to merge before running the merge action.",
                )
                return

            if self.current_table_object.table_type == TableTypes.MEASUREMENT:
                await self.show_messagebox_async(
                    "Error",
                    "Merging can only be performed on metadata or reference tables.",
                )
                return

            if self.current_table_object == self.data_store.db_classes.Sensor:
                host_ids = set([s.host for s in selected_items])
                if len(host_ids) > 1:
                    self.show_messagebox(
                        "Error", "You can only merge sensors belonging to the same platform."
                    )
                    return

            # Generate a mapping of nice display strings
            # to the actual underlying entry objects
            display_to_object = {}
            for entry_obj in selected_items[:MAX_PREVIEW_TABLE_RESULTS]:
                display_str = " - ".join(
                    [
                        str(getattr(entry_obj, field_name))
                        for field_name in entry_obj._default_preview_fields
                    ]
                )
                display_to_object[display_str] = entry_obj

            # Show the dialog with a list of platforms, to allow the user
            # to choose which platoform should be the master
            table_name = table_name_to_class_name(self.dropdown_table.text)

            dialog = MergeDialog(f"Select target {table_name}", list(display_to_object.keys()))
            dialog_result = await self.show_dialog_as_float(dialog)
            if dialog_result is not None:
                master_obj = display_to_object[dialog_result]

                # This runs the `do_merge` function, passing it the
                # list of selected platforms, and the master platform object
                # This function is defined inline above, and is given extra
                # arguments of set_percentage and is_cancelled to
                # allow the function to return percentage process
                dialog = ProgressDialog(
                    f"Merging {table_name} entries",
                    partial(do_merge, selected_items, master_obj),
                    show_cancel=False,
                )
                result = await self.show_dialog_as_float(dialog)
                if isinstance(result, Exception):
                    await self.show_messagebox_async(
                        "Error",
                        f"Error running merge\n\nOriginal error:{textwrap.fill(str(result), 60)}",
                    )
                    return
                # Once the platform merge is done, show a message box
                # We use the async version of this function as we're calling
                # from within a coroutine
                await self.show_messagebox_async("Merge completed")
                # Re-run the query, so we get an updated list in the preview
                # and can see that some platforms have disappeared
                self.run_query()
                # Regenerate the column_data, so we don't have entries in the dropdowns
                # that don't exist anymore
                self.get_column_data(self.current_table_object)
                self.filter_widget.set_column_data(self.column_data, clear_entries=False)

        ensure_future(coroutine())

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

        @kb.add("c-f")
        def _(event):
            # Don't do anything if we haven't selected a table yet
            if self.current_table_object is not None:
                self.choose_fields()

        @kb.add("f1")
        def _(event):
            app = get_app()
            if self.current_dialog is not None:
                # Look for help in the current dialog, if it exists
                try:
                    help_message = self.current_dialog.contextual_help
                except AttributeError:
                    help_message = None
            else:
                # Otherwise look in the dict using the current window
                help_message = self.contextual_help.get(app.layout.current_window)

            try:
                # Try and find the position of the contextual help string in the
                # main help text string - if we fail, just default to the beginning
                position = HELP_TEXT.index(help_message)
            except (TypeError, ValueError):
                position = 0

            async def coroutine():
                # Show a help dialog, with the dialog scrolled to the position
                # of the text
                dialog = HelpDialog("Help", HELP_TEXT, position)
                await self.show_dialog_as_float(dialog)

            ensure_future(coroutine())

        @kb.add("f12")
        def _(event):
            async def coroutine():
                # Show a help dialog, with the dialog scrolled to the position
                # of the text
                dialog = HelpDialog("General Help", INTRO_HELP_TEXT, 0)
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
            event.app.layout.focus(self.filter_query)

        @kb.add("f5")
        def _(event):
            self.filters_tab = "complete_query"
            event.app.layout.focus(self.complete_query)

        @kb.add("f6")
        def _(event):
            self.preview_tab = "table"
            self.status_bar_shortcuts = ["Ctrl-F - Select fields"]
            event.app.layout.focus(self.preview_container)

        # FUTURE: Not needed until we want to display the graph
        # @kb.add("f7")
        # def _(event):
        #     self.preview_tab = "graph"
        #     self.status_bar_shortcuts = ["Ctrl-U - Update graph"]
        #     event.app.layout.focus(self.preview_container)

        @kb.add("f8")
        def _(event):
            event.app.layout.focus(self.actions_container)

        return kb

    def choose_fields(self):
        async def coroutine():
            (
                system_name_to_display_name,
                display_name_to_system_name,
            ) = get_system_name_mappings(self.column_data)

            # Get lists of left-hand and right-hand side entries
            # The left-hand entries are all available fields (minus those that already appear on the right)
            # and the right-hand entries are the currently selected fields
            all_entries = list(display_name_to_system_name.keys())

            # Exclude entries that are relationships to reference tables, as otherwise
            # we duplicate the relevant association proxy
            # (ie. we don't want `nationality` (the relationship) and `nationality_name` (the association proxy)
            # to both appear in the list of fields to choose - so we get rid of the relationship one)
            left_entries = []
            for entry in all_entries:
                col_config = self.column_data[entry]
                if (
                    col_config["sqlalchemy_type"] == "relationship"
                    and col_config["foreign_table_type"] == TableTypes.REFERENCE
                ):
                    continue
                left_entries.append(entry)

            right_entries = [
                system_name_to_display_name[entry] for entry in self.preview_selected_fields
            ]
            left_entries = list(set(left_entries).difference(set(right_entries)))

            dialog = SelectionDialog(left_entries, right_entries, "Select fields")
            selected_fields = await self.show_dialog_as_float(dialog)

            if selected_fields is None:
                return

            # Convert these back to system names
            self.preview_selected_fields = [
                display_name_to_system_name[entry] for entry in selected_fields
            ]
            # Re-run the query with the new fields
            self.run_query()

        ensure_future(coroutine())

    def get_style(self):
        # We deliberately use the 'ansiXXX' colours here, as they are the standard
        # colours that are available on the Windows Command Prompt
        # See https://python-prompt-toolkit.readthedocs.io/en/master/pages/advanced_topics/styling.html
        # for a list of them
        style = Style(
            [
                ("title-line", "bg:ansibrightblack fg:ansiwhite"),
                ("button", "fg:ansibrightblack"),
                ("button.focused button.text", "fg:ansiwhite"),
                ("button.focused button.arrow", "fg:ansiwhite"),
                ("button.focused", "bg:ansiblue"),
                ("dropdown.focused", "bg:ansiblue fg:ansiwhite"),
                ("text-area focused", "bg:ansiblue"),
                ("dropdown-highlight", "fg:ansibrightgreen"),
                ("filter-text", "fg:ansibrightcyan"),
                ("table-title", "fg:ansibrightmagenta"),
                ("checkbox-selected", "bg:ansiyellow"),
                ("status-bar-text", "bg:ansibrightblack"),
                ("instruction-text", "fg:ansibrightcyan"),
                ("instruction-text-dark", "fg:ansicyan"),
                ("dropdown.box", "bg:ansibrightblack fg:ansiblack"),
                ("combobox-highlight", "bg:ansiyellow"),
                ("frame dialog.body text-area", "nounderline bg:ansiwhite"),
                ("frame dialog.body text-area last-line", "nounderline bg:ansiwhite"),
                ("frame dialog.body button.text", "fg:ansiblack"),
                ("frame dialog.body button.focused button.text", "fg:ansiwhite"),
                ("error-message", "fg:ansibrightred"),
                ("disabled-entry", "fg:ansibrightblack"),
            ]
        )
        return style

    async def show_dialog_as_float(self, dialog):
        """Function to show a dialog as a float.

        Taken mostly from the text-editor.py example
        that comes with prompt_toolkit.

        This is an async function, and thus must be awaited
        from within another async function.
        """
        float_ = Float(content=dialog)
        # We want to put this dialog as the penultimate float in the list of floats
        # This is because we want it to appear above any other dialogs (eg. if we are opening
        # the help dialog when another dialog is already open), but we don't want it to be
        # above the CompletionsMenu float (added in the initialisation), as then the completion
        # menu appears in the wrong place
        self.root_container.floats.insert(len(self.root_container.floats) - 1, float_)

        app = get_app()

        focused_before = app.layout.current_window
        # Make sure we don't crash if we can't set the focus
        # on the dialog - as some dialogs have no focusable elements
        # (eg. a progress bar dialog with no cancel button)
        try:
            app.layout.focus(dialog)
        except ValueError:
            pass

        # Keep track of the last dialog, in case we have dialogs on top of dialogs
        prev_current_dialog = self.current_dialog
        self.current_dialog = dialog

        # Wait for the dialog to return
        result = await dialog.future

        # Reset to the previous dialog, in case we have dialogs on top of dialogs
        self.current_dialog = prev_current_dialog

        # Make sure we don't give an error if we can't put the focus back
        # to previous location, as if we're exiting the app at the time
        # this gives an error
        try:
            app.layout.focus(focused_before)
        except Exception:
            pass

        if float_ in self.root_container.floats:
            self.root_container.floats.remove(float_)

        app.invalidate()

        return result

    async def show_messagebox_async(self, title, text=None):
        # This is the async function, for awaiting within another
        # coroutine
        dialog = MessageDialog(title, text)
        await self.show_dialog_as_float(dialog)

    def show_messagebox(self, title, text=None):
        # This is the non-async version, that just runs a task to
        # ensure the output of the async version
        ensure_future(self.show_messagebox_async(title, text))

    def get_filter_container(self):
        """Called by the DynamicContainer which displays the filter container"""
        top_label = Label(
            text="Build filters  F3 | Show Filter Query  F4 | Show complete query  F5",
            style="class:title-line",
        )
        # Show different widgets, depending on the tab selected
        if self.filters_tab == "filters":
            return HSplit(
                [
                    top_label,
                    Label(
                        text="Press TAB to go to next dropdown or line\nPress Shift + TAB to go to the previous dropdown or line",
                        style="class:instruction-text",
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
                    self.filter_query_window,
                ],
                padding=1,
                height=Dimension(weight=0.5),
            )
        elif self.filters_tab == "complete_query":
            return HSplit(
                [
                    top_label,
                    self.complete_query_window,
                ],
                padding=1,
                height=Dimension(weight=0.5),
            )

    def get_preview_container(self):
        """Called by the DynamicContainer that displays the preview pane"""
        # title_label = Label(text="Preview List   F6 | Preview Graph  F7", style="class:title-line")
        title_label = Label(text="Preview List   F6", style="class:title-line")
        if self.preview_tab == "table":
            return HSplit(
                children=[
                    title_label,
                    Label(
                        text="Use Ctrl-F to select fields to display",
                        style="class:instruction-text",
                    ),
                    self.preview_table,
                    self.preview_table_message,
                ],
                padding=1,
                width=Dimension(weight=0.4),
            )
        # FUTURE: Not needed until we want to display a graph
        # elif self.preview_tab == "graph":
        #     return HSplit(
        #         children=[
        #             title_label,
        #             self.preview_graph,
        #         ],
        #         padding=1,
        #         width=Dimension(weight=0.4),
        #     )

    def get_status_bar_container(self):
        """Called by the DynamicContainer that displays the status bar"""
        return VSplit(
            [
                VSplit(
                    [
                        Label("ESC - Exit", style="class:status-bar-text", dont_extend_width=True),
                        Label(
                            "F1 - Contextual Help",
                            style="class:status-bar-text",
                            dont_extend_width=True,
                        ),
                        Label(
                            "F12 - General Help",
                            style="class:status-bar-text",
                            dont_extend_width=True,
                        ),
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
    try:
        gui = MaintenanceGUI()
        gui.app.run()
    except Exception as e:
        print(traceback.format_exc())
        print(str(e))
        print("Error running GUI, see error message above")
