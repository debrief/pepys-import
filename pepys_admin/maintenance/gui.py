import time
from asyncio.tasks import ensure_future
from functools import partial

import sqlalchemy
from loguru import logger
from prompt_toolkit import Application
from prompt_toolkit.application.current import get_app
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.filters.utils import to_filter
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
from sqlalchemy import nullslast
from sqlalchemy.orm import undefer

from pepys_admin.maintenance.dialogs.confirmation_dialog import ConfirmationDialog
from pepys_admin.maintenance.dialogs.help_dialog import HelpDialog
from pepys_admin.maintenance.dialogs.message_dialog import MessageDialog
from pepys_admin.maintenance.dialogs.platform_merge_dialog import PlatformMergeDialog
from pepys_admin.maintenance.dialogs.progress_dialog import ProgressDialog
from pepys_admin.maintenance.dialogs.selection_dialog import SelectionDialog
from pepys_admin.maintenance.utils import (
    get_system_name_mappings,
    get_table_titles,
    remove_duplicates_and_nones,
)
from pepys_admin.maintenance.widgets.blank_border import BlankBorder
from pepys_admin.maintenance.widgets.checkbox_table import CheckboxTable
from pepys_admin.maintenance.widgets.combo_box import ComboBox
from pepys_admin.maintenance.widgets.dropdown_box import DropdownBox
from pepys_admin.maintenance.widgets.filter_widget import FilterWidget
from pepys_admin.maintenance.widgets.filter_widget_utils import filter_widget_output_to_query
from pepys_import.core.store.data_store import DataStore

logger.remove()
logger.add("gui.log")

INTRO_HELP_TEXT = """# Maintenance Interface Documentation
You can use the maintenance interface to build custom queries and
do specific actions such as merging assets, exporting data, etc.

The interface is composed of 4 panels:

## First panel: Select data type F2
You can select the data table you want to query data from.
(Platform table is the only one available for now)

## Second panel: Build filters F3
You can filter the data in the table selected above based by
selecting specific fields and values for these fields. You can
combine several filters using AND or OR operators.

## Third panel: Preview list F6
The selected and filtered data is visible here.

## Fourth panel: Choose actions F8
Through this panel, you can perform several actions on the data you selected.

# Main navigation principles
You can select a specific panel by pressing the corresponding F key:
F2: Select data type
F3: Build filters
F4: Show Filter Query (TBI)
F5: Show Complete Query (TBI)
F6: Preview List
F7: Preview Graph (TBI)
F8: Choose actions

You can also press Tab to go forward or Shift + Tab to go backward.
"""

HELP_TEXT = """# First panel: Select data type (F2)
Type the first letter(s) of the table you are looking for.

Press Enter to expand the list of available tables, use arrow
keys to select the table you want and press Enter again.

# Second panel: Build filters (F3)
Each line is either a query or a standalone operator.

You move from one line or one field to another using TAB or Shift
+ TAB

## Query line:
Each query is built in the following way:

Select column: you can select any field from the table

Operator: = is ‘equal to’ (perfect match), != is ‘not equal to’,
LIKE is ‘contains’

Enter value here: you can start typing and a list of existing
values will be filtered based on your input.

At the end of each line, there is a < Delete > button: select the
button and press Enter to delete the corresponding line.

To add a new line, select < Add a filter condition > button and
press Enter.

## Operator line:
A single dropdown allows you to choose between AND and OR.

# Third panel: Preview List (F6)
This panel displays the list of data contained on the selected
table according to the filter you selected.

In the list, you can go up and down the list using arrow keys,
select/un-select an item using Enter.

You can select the entire list by placing the cursor on the
header row.

## Selecting fields
You can customize which fields are shown in the preview using
Ctrl + F: this opens a popup, where you can add or remove fields.

To add a field: navigate to the field you want to appear using
arrow keys and press Enter to add it.

To remove a field: press TAB to change from one column to the
other, navigate using the arrows to select the field you want to
remove and press Enter.

To validate, navigate to the <  OK  >  button using TAB and press
Enter

# Fourth panel: Choose actions (F8)
Merge Platforms is the only available action for now.

The action applies to the platforms you selected in the preview
list if any. When merging, you will be prompted to select the
target platform in a popup. Select the platform and press Enter.
Once the platforms are merged, press Enter and the Preview List
will be updated.
"""


class MaintenanceGUI:
    def __init__(self, data_store=None):
        if data_store is not None:
            self.data_store = data_store
        else:
            # TODO: Remove this, it's just for ease of testing/development at the moment
            # This won't cause problems for users, as they will access via Pepys Admin
            # where data store will be defined
            self.data_store = DataStore(
                "", "", "", 0, "test_gui.db", db_type="sqlite", show_status=False, welcome_text=""
            )
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

        self.create_column_data()

        self.filter_widget.set_column_data(self.column_data)
        self.run_query()

        layout = Layout(self.root_container)

        self.app = Application(
            layout=layout,
            key_bindings=self.get_keybindings(),
            full_screen=True,
            mouse_support=True,
            style=self.get_style(),
        )

    def init_ui_components(self):
        """Initialise all of the UI components, controls, containers and widgets"""
        # Dropdown box to select table, plus pane that it is in
        self.dropdown_table = DropdownBox(
            text="Platform",  # FUTURE: This is currently hard-coded to Platform
            entries=[
                "Platform",
            ],
            # FUTURE: This is needed to be able to select from this dropdown
            # on_select_handler=self.on_table_select,
        )
        # Makes the dropdown box not focusable, so users can't tab to it
        self.dropdown_table.control.focusable = to_filter(False)
        # Also make it disabled, so clicking doesn't work
        self.dropdown_table.disabled = True

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
        )
        self.set_contextual_help(self.filter_widget, "# Second panel: Build filters F3")
        self.filter_container = DynamicContainer(self.get_filter_container)
        # Buffer to hold just the filter part of the query in SQL form
        self.filter_query_buffer = Buffer(document=Document("Filter query here", 0))
        self.filter_query = BufferControl(self.filter_query_buffer)

        # Buffer to hold the complete query in SQL form
        self.complete_query_buffer = Buffer()
        self.complete_query = BufferControl(self.complete_query_buffer)

        # Actions container, containing a list of actions that can be run
        self.actions_combo = ComboBox(
            entries=["1 - Merge Platforms"],
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
            height=Dimension(weight=0.1),
        )

        # Preview container, with two tabs: a preview table and a preview graph
        self.preview_table = CheckboxTable(
            table_data=self.get_table_data, table_objects=self.get_table_objects
        )
        self.set_contextual_help(self.preview_table, "# Third panel: Preview List (F6)")
        self.preview_graph = Window(
            BufferControl(Buffer(document=Document("Graph here", 0), read_only=True))
        )
        self.preview_container = DynamicContainer(self.get_preview_container)

        # Status bar
        self.status_bar_shortcuts = ["Ctrl-F - Select fields"]
        self.status_bar_container = DynamicContainer(self.get_status_bar_container)

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
            floats=[],
        )

    def set_contextual_help(self, widget, text):
        """Sets the contextual help dictionary based on the widget's
        container"""
        self.contextual_help[widget.__pt_container__()] = text

    def create_column_data(self):
        """Creates the column_data needed for the FilterWidget.

        At the moment this is hard-coded to be the column data for
        the Platforms table, with database queries being used to populate
        the 'values' entry in the dict."""
        Platform = self.data_store.db_classes.Platform
        Nationality = self.data_store.db_classes.Nationality
        PlatformType = self.data_store.db_classes.PlatformType
        Privacy = self.data_store.db_classes.Privacy
        try:
            with self.data_store.session_scope():
                all_platforms = self.data_store.session.query(Platform).all()

                platform_ids = [str(platform.platform_id) for platform in all_platforms]
                platform_names = [platform.name for platform in all_platforms]
                platform_identifiers = [platform.identifier for platform in all_platforms]
                platform_trigraphs = [platform.trigraph for platform in all_platforms]
                platform_quadgraphs = [platform.quadgraph for platform in all_platforms]

                # nullslast in the expression below makes NULL entries appear at the end
                # of the sorted list - if we don't have this then they sort as 'zero'
                # and come before the prioritised ones
                all_nationalities = (
                    self.data_store.session.query(Nationality)
                    .order_by(nullslast(Nationality.priority.asc()))
                    .all()
                )
                nationality_names = [nationality.name for nationality in all_nationalities]

                all_platform_types = self.data_store.session.query(PlatformType).all()
                platform_type_names = [pt.name for pt in all_platform_types]

                all_privacies = self.data_store.session.query(Privacy).order_by(Privacy.level).all()
                privacy_names = [priv.name for priv in all_privacies]
        except sqlalchemy.exc.OperationalError:
            raise Exception("Database not initialised error")

        platform_column_data = {
            "platform_id": {"type": "id", "values": platform_ids},
            "name": {"type": "string", "values": remove_duplicates_and_nones(platform_names)},
            "identifier": {
                "type": "string",
                "values": remove_duplicates_and_nones(platform_identifiers),
            },
            "trigraph": {
                "type": "string",
                "values": remove_duplicates_and_nones(platform_trigraphs),
            },
            "quadgraph": {
                "type": "string",
                "values": remove_duplicates_and_nones(platform_quadgraphs),
            },
            "nationality name": {
                "type": "string",
                "system_name": "nationality_name",
                "values": nationality_names,
            },
            "platform type name": {
                "type": "string",
                "system_name": "platform_type_name",
                "values": platform_type_names,
            },
            "privacy name": {
                "type": "string",
                "system_name": "privacy_name",
                "values": privacy_names,
            },
        }

        self.column_data = platform_column_data

    def run_query(self):
        """Runs the query as defined by the FilterWidget,
        and displays the result in the preview table."""
        app = get_app()
        # As this property is computed each time, get the output and store it
        # to save time
        filters = self.filter_widget.filters
        with self.data_store.session_scope():
            if filters == []:
                # If there are no filters then just return the table with no filtering
                query_obj = self.data_store.session.query(self.data_store.db_classes.Platform)
            else:
                # Otherwise, convert the filter widget output to a SQLAlchemy filter and run it
                filter_query = filter_widget_output_to_query(filters, "Platforms", self.data_store)
                query_obj = self.data_store.session.query(
                    self.data_store.db_classes.Platform
                ).filter(filter_query)

            # Get all the results, while undefering all fields to make sure everything is
            # available once it's been expunged (disconnected) from the database
            results = query_obj.options(undefer("*")).all()
            logger.debug(results)

            # Convert the selected fields to sensible table titles
            self.table_data = [get_table_titles(self.preview_selected_fields)]
            # The first of the table objects should be None, as that is the header field
            # and doesn't have a table object associated with it
            self.table_objects = [None]

            if len(results) == 0:
                # If we've got no results then just update the app display
                # which will just show the headers that we mentioned above
                app.invalidate()
                return

            # Disconnect all the objects we've returned in our query from the database
            # so we can store them outside of the session without any problems
            self.data_store.session.expunge_all()

            for result in results:
                # Get the right fields and append them
                self.table_data.append(
                    [
                        str(getattr(result, field_name))
                        for field_name in self.preview_selected_fields
                    ]
                )
                self.table_objects.append(result)

        # Refresh the app display
        app.invalidate()
        logger.debug("Ran query")
        logger.debug(f"{self.table_data=}")

    def get_table_data(self):
        return self.table_data

    def get_table_objects(self):
        return self.table_objects

    # FUTURE: Not needed until we want to select a table at the top
    # def on_table_select(self, value):
    #     """Called when an entry is selected from the Table dropdown at the top-left."""
    #     # Set the data used to parameterise the FilterWidget
    #     self.filter_widget.set_column_data(column_data[value])
    #     self.run_query()

    def on_filter_widget_change(self, value):
        """Called when the filter widget notifies us that it has changed. The filter
        widget is sensible about this and only raises this event if there has actually been
        a change in the output of the filters property. That means we can run a query
        each time this is called, and the query shouldn't get run more often than is needed."""
        # Convert the filter object to a SQL string to display in the Complete Query tab
        # FUTURE: Not needed until we want to display raw SQL
        # if value != []:
        # filter_query = filter_widget_output_to_query(value, "Platforms", self.data_store)
        # query_obj = self.data_store.session.query(self.data_store.db_classes.Platform).filter(
        #     filter_query
        # )
        # sql_string = str(query_obj.statement.compile(compile_kwargs={"literal_binds": True}))
        # self.filter_query_buffer.text = textwrap.fill(sql_string, width=50)
        self.run_query()

    def run_action(self, selected_value):
        """Runs an action from the actions ComboBox. Called when Enter is pressed."""
        if selected_value == "1 - Merge Platforms":
            self.run_merge_platforms()
        else:
            self.show_messagebox("Action", f"Running action {selected_value}")

    def run_merge_platforms(self):
        """Runs the action to merge platforms.

        Takes the list of platforms to merge from the selected items in the preview table,
        then opens a dialog to select the master platform, then runs the merge with a
        progress dialog, and displays a messagebox when it is finished.
        """
        if len(self.preview_table.current_values) == 0:
            self.show_messagebox(
                "Error", "You must select platforms to merge before running the merge action."
            )
            return
        # Generate a mapping of nice display strings
        # to the actual underlying Platform objects
        display_to_object = {}
        for platform_obj in self.preview_table.current_values:
            display_str = " - ".join(
                [platform_obj.name, platform_obj.nationality_name, platform_obj.identifier]
            )
            display_to_object[display_str] = platform_obj

        def do_merge(platform_list, master_platform, set_percentage=None, is_cancelled=None):
            # Does the actual merge, while also setting the percentage complete
            # TODO: In the future, we can move the set_percentage calls *inside* the merge_platforms
            # function (as an optional argument, only called if it exists, so it works fine
            # outside of the GUI context too)
            set_percentage(10)
            with self.data_store.session_scope():
                self.data_store.merge_platforms(platform_list, master_platform)
            time.sleep(3)
            set_percentage(90)
            time.sleep(1)
            set_percentage(100)

        async def coroutine():
            # Show the dialog with a list of platforms, to allow the user
            # to choose which platoform should be the master
            dialog = PlatformMergeDialog(list(display_to_object.keys()))
            dialog_result = await self.show_dialog_as_float(dialog)
            if dialog_result is not None:
                master_platform_obj = display_to_object[dialog_result]

                # This runs the `do_merge` function, passing it the
                # list of selected platforms, and the master platform object
                # This function is defined inline above, and is given extra
                # arguments of set_percentage and is_cancelled to
                # allow the function to return percentage process
                dialog = ProgressDialog(
                    "Merging platforms",
                    partial(do_merge, self.preview_table.current_values, master_platform_obj),
                    show_cancel=False,
                )
                _ = await self.show_dialog_as_float(dialog)
                # Once the platform merge is done, show a message box
                # We use the async version of this function as we're calling
                # from within a coroutine
                await self.show_messagebox_async("Merge completed")
                # Re-run the query, so we get an updated list in the preview
                # and can see that some platforms have disappeared
                self.run_query()
                # Regenerate the column_data, so we don't have entries in the dropdowns
                # that don't exist anymore
                self.create_column_data()
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

        @kb.add("c-f1")
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

        # FUTURE: Not needed until we want to display the raw SQL
        # @kb.add("f4")
        # def _(event):
        #     self.filters_tab = "filter_query"
        #     event.app.layout.focus(self.filter_container)

        # @kb.add("f5")
        # def _(event):
        #     self.filters_tab = "complete_query"
        #     event.app.layout.focus(self.filter_container)

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
            left_entries = list(display_name_to_system_name.keys())
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
                ("button.focused", "bg:ansired"),
                ("dropdown.focused", "bg:ansired"),
                ("text-area focused", "bg:ansibrightred"),
                ("dropdown-highlight", "fg:ansibrightgreen"),
                ("filter-text", "fg:ansibrightcyan"),
                ("table-title", "fg:ansibrightmagenta"),
                ("checkbox-selected", "bg:ansiyellow"),
                ("status-bar-text", "bg:ansibrightblack"),
                ("instruction-text", "fg:ansibrightcyan"),
                ("dropdown.box", "bg:ansibrightblack fg:ansiblack"),
                ("combobox-highlight", "bg:ansiyellow"),
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
        # Put it at the top of the float list in the root container
        # (which is a FloatContainer)
        # self.root_container.floats.insert(0, float_)
        self.root_container.floats.append(float_)

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
            # text="Build filters  F3 | Show Filter Query  F4 | Show complete query  F5",
            text="Build filters  F3",
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
        # FUTURE: Not needed until we want to display raw SQL queries
        # elif self.filters_tab == "filter_query":
        #     return HSplit(
        #         [
        #             top_label,
        #             Window(self.filter_query),
        #         ],
        #         padding=1,
        #         height=Dimension(weight=0.5),
        #     )
        # elif self.filters_tab == "complete_query":
        #     return HSplit(
        #         [
        #             top_label,
        #             Window(self.complete_query),
        #         ],
        #         padding=1,
        #         height=Dimension(weight=0.5),
        #     )

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
