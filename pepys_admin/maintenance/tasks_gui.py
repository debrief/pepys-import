from pepys_admin.maintenance.utils import load_participants_attribute
import textwrap
import traceback
from asyncio import ensure_future
from datetime import datetime

from loguru import logger
from prompt_toolkit.application.application import Application
from prompt_toolkit.application.current import get_app
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.layout.containers import Float, FloatContainer, HSplit, VSplit, Window
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets.base import Border, Button, Label
from sqlalchemy.orm import joinedload, undefer
from sqlalchemy.orm.exc import DetachedInstanceError

from pepys_admin.maintenance.dialogs.confirmation_dialog import ConfirmationDialog
from pepys_admin.maintenance.dialogs.message_dialog import MessageDialog
from pepys_admin.maintenance.widgets.blank_border import BlankBorder
from pepys_admin.maintenance.widgets.custom_text_area import CustomTextArea
from pepys_admin.maintenance.widgets.task_edit_widget import TaskEditWidget
from pepys_admin.maintenance.widgets.tree_view import TreeElement, TreeView
from pepys_import.core.store.data_store import USER, DataStore
from pepys_import.utils.sqlalchemy_utils import clone_model, get_primary_key_for_table

logger.remove()
logger.add("gui.log")

# Uncomment the lines below to get logging of the SQL queries run by SQLAlchemy
# to the file sql.log
# import logging

# logging.basicConfig(filename="sql.log", level=logging.DEBUG)
# logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)


class TasksGUI:
    def __init__(self, data_store=None):
        print("Initialising GUI and loading tasks and platforms...")

        if data_store is not None:
            self.data_store = data_store
        else:
            # This is for testing/development.
            # It won't cause problems for users, as they will access via Pepys Admin
            # where data store will be defined
            self.data_store = DataStore(
                "", "", "", 0, "test_tasks.db", db_type="sqlite", show_status=False, welcome_text=""
            )
            self.data_store.initialise()
            with self.data_store.session_scope():
                self.data_store.populate_reference()
                self.data_store.populate_metadata()

        if self.data_store.in_memory_database:
            raise ValueError("Cannot run the tasks GUI on an in-memory SQLite database")

        # try:
        # This calls a simple function to check if the Privacies table has entries
        # We don't actually care if it has entries, but it is a good simple query
        # to run which checks if the database has been initialised
        with self.data_store.session_scope():
            _ = self.data_store.is_empty()
        # except Exception:
        #     raise ValueError(
        #         "Cannot run GUI on a non-initialised database. Please run initialise first."
        #     )

        self.current_dialog = None

        self.root_task = self.get_tasks_into_treeview()

        self.privacies = self.get_privacies()
        self.platforms = self.get_platforms()

        self.init_ui_components()

        self.app = Application(
            layout=self.layout,
            key_bindings=self.get_keybindings(),
            full_screen=True,
            mouse_support=True,
            style=self.get_style(),
        )
        self.app.dropdown_opened = False

    def get_privacies(self):
        """Get all privacies, storing them ready to be used in the add dialogs"""
        all_privacies = (
            self.data_store.session.query(self.data_store.db_classes.Privacy)
            .order_by(self.data_store.db_classes.Privacy.level)
            .all()
        )
        privacy_strs = [priv.name for priv in all_privacies]
        privacy_ids = [priv.privacy_id for priv in all_privacies]

        return {"values": privacy_strs, "ids": privacy_ids}

    def get_platforms(self):
        """Get all platforms, storing them ready to be used in the add dialogs"""
        all_platforms = self.data_store.session.query(self.data_store.db_classes.Platform).all()

        platform_strs = [
            f"{plat.name} / {plat.identifier} / {plat.nationality_name}" for plat in all_platforms
        ]
        platform_ids = [plat.platform_id for plat in all_platforms]

        return {"values": platform_strs, "ids": platform_ids}

    def get_tasks_into_treeview(self):
        """Iterates through all tasks in the database, and creates the relevant TreeElement
        objects to enable them to be displayed in the TreeView.
        """
        Series = self.data_store.db_classes.Series

        id_to_element = {}

        root = TreeElement("hidden root")
        id_to_element[None] = root

        with self.data_store.session_scope():
            all_series = (
                self.data_store.session.query(Series)
                .order_by(Series.created_date.asc())
                .options(undefer("*"))
                .all()
            )
            self.data_store.session.expunge_all()

            for series in all_series:
                series_el = TreeElement(series.name, series)
                root.add_child(series_el)

                for wargame in series.child_wargames:
                    wargame_el = TreeElement(wargame.name, wargame)
                    series_el.add_child(wargame_el)

                    for serial in wargame.child_serials:
                        serial_el = TreeElement(serial.serial_number, serial)
                        wargame_el.add_child(serial_el)

        return root

    def init_ui_components(self):
        self.tree_view = TreeView(
            self.root_task,
            height=Dimension(weight=0.8),
            hide_root=True,
            on_add=self.handle_tree_add,
            on_select=self.handle_tree_select,
            max_levels=3,
            level_to_name={0: "series", 1: "wargame", 2: "serial"},
        )
        self.filter_text_area = CustomTextArea(
            "Type to filter",
            multiline=False,
            focus_on_click=True,
            on_change=self.on_filter_text_change,
        )
        self.top_level_add_button = Button("Add series", self.handle_top_level_add)
        self.lh_pane = HSplit(
            [
                Label(text="Tasks   F2", style="class:title-line"),
                self.filter_text_area,
                self.tree_view,
                self.top_level_add_button,
            ],
            padding=1,
            width=Dimension(weight=0.2),
        )

        current_task_object = (
            self.tree_view.selected_element.object if self.tree_view.selected_element else None
        )

        self.task_edit_widget = TaskEditWidget(
            current_task_object,
            self.privacies,
            self.platforms,
            self.handle_save,
            self.handle_delete,
            self.handle_duplicate,
            self.update_tree_object,
            self.data_store,
            self.show_dialog_as_float,
        )
        self.rh_pane = HSplit(
            [
                Label(text="View task   F3", style="class:title-line"),
                self.task_edit_widget,
            ],
            padding=1,
            width=Dimension(weight=0.8),
        )

        self.root_container = FloatContainer(
            BlankBorder(
                VSplit(
                    [
                        HSplit([self.lh_pane], width=Dimension(weight=0.4)),
                        Window(width=1, char=Border.VERTICAL),
                        self.rh_pane,
                    ],
                    padding=1,
                )
            ),
            floats=[],
        )

        self.layout = Layout(self.root_container)

    def on_filter_text_change(self):
        if self.filter_text_area.text != "Type to filter":
            self.tree_view.filter(self.filter_text_area.text)

    def show_validation_error(self, missing_fields):
        self.show_messagebox(
            "Validation Error",
            "You must provide valid values for the following fields before saving or\nadding a participant:\n\n"
            + "\n".join(missing_fields),
        )

    def update_tree_object(self):
        """Handles updating the Task object stored in the TreeView when it has changed"""
        self.tree_view.selected_element.object = self.task_edit_widget.task_object

    def validate_fields(self, current_task, updated_fields):
        WARGAME_REQUIRED_FIELDS = set(["name", "start", "end"])
        SERIAL_REQUIRED_FIELDS = set(["serial_number", "start", "end"])
        if isinstance(current_task, self.data_store.db_classes.Series):
            # If this is None then this is a new Series object that we're creating
            # and thus we need to check all fields are filled
            if current_task.name is None:
                if "name" not in updated_fields:
                    self.show_validation_error(missing_fields=["name"])
                    return False
        else:
            if isinstance(current_task, self.data_store.db_classes.Wargame):
                required_fields = WARGAME_REQUIRED_FIELDS
            elif isinstance(current_task, self.data_store.db_classes.Serial):
                required_fields = SERIAL_REQUIRED_FIELDS
            else:
                raise ValueError("Invalid object passed to validate_fields")
            if current_task.start is None:
                provided_fields = set(updated_fields.keys())
                if not required_fields.issubset(provided_fields):
                    missing_fields = required_fields.difference(provided_fields)
                    self.show_validation_error(missing_fields=missing_fields)
                    return False

        # Check that any fields that we're updating to None (ie. NULL) are not
        # required fields
        missing_fields = []
        for field, new_value in updated_fields.items():
            if new_value is None or new_value == "":
                if field in WARGAME_REQUIRED_FIELDS or field in SERIAL_REQUIRED_FIELDS:
                    missing_fields.append(field)

        if len(missing_fields) > 0:
            self.show_validation_error(missing_fields=missing_fields)
            return False

        return True

    def handle_duplicate(self):
        current_task = self.task_edit_widget.task_object

        # Work out a new name, so that if we copy multiple times we will get XXX Copy, XXX Copy 2 etc
        all_serial_numbers_of_this_wargame = [
            el.text for el in self.tree_view.selected_element.parent.children
        ]

        new_name_orig = current_task.serial_number + " Copy"
        new_name = new_name_orig
        i = 2
        while new_name in all_serial_numbers_of_this_wargame:
            new_name = new_name_orig + f" {i}"
            i += 1

        new_serial = clone_model(current_task, serial_number=new_name)

        with self.data_store.session_scope():
            self.data_store.session.add(new_serial)
            # Commit here, so that the new serial gets an ID, which we can reference below
            self.data_store.session.commit()
            self.data_store.session.refresh(new_serial)
            new_serial = load_participants_attribute(self.data_store, new_serial)

            new_serial_id = new_serial.serial_id

            # Copy the participants too
            orig_participants = current_task.participants
            new_participants = [clone_model(p, serial_id=new_serial_id) for p in orig_participants]

            self.data_store.session.add_all(new_participants)
            self.data_store.session.commit()
            self.data_store.session.refresh(new_serial)
            new_serial = load_participants_attribute(self.data_store, new_serial)
            self.data_store.session.expunge_all()

        new_tree_element = TreeElement(new_serial.serial_number, new_serial)
        self.tree_view.selected_element.parent.add_child(new_tree_element)
        self.tree_view.selected_element.parent.sort_children_by_start_time()

    def handle_save(self):
        updated_fields = self.task_edit_widget.get_updated_fields()

        if updated_fields == {}:
            return True

        current_task = self.task_edit_widget.task_object
        primary_key = get_primary_key_for_table(current_task)

        if not self.validate_fields(current_task, updated_fields):
            return False

        # Keep track of the old values for adding to Logs later
        old_values = {}
        for column in updated_fields.keys():
            old_values[column] = getattr(current_task, column)

        # Set the new values
        for column, new_value in updated_fields.items():
            setattr(current_task, column, new_value)

        try:
            with self.data_store.session_scope():
                self.data_store.session.add(current_task)
                # We need to commit the change so that it gets an ID and matches everything up
                # but this 'expires' the attributes, so we need to refresh these from the database
                # before expunging. Overall, this means that the fully up-to-date Task object
                # is detached from the session and available for use in the UI
                self.data_store.session.commit()
                self.data_store.session.refresh(current_task)
                current_task = load_participants_attribute(self.data_store, current_task)
                self.data_store.session.expunge_all()
        except Exception as e:
            self.show_messagebox(
                "Error",
                f"Error saving entry - could be a duplicate Serial number?\nOriginal error:\n{textwrap.fill(str(e), 60)}",
            )
            return

        # Record Change and Logs for this change
        # (we have to do this after adding the Task and committing
        # otherwise the Task won't have a task_id
        with self.data_store.session_scope():
            change_id = self.data_store.add_to_changes(
                USER, datetime.utcnow(), "Manual edit in Tasks GUI"
            ).change_id
            for column, old_value in old_values.items():
                self.data_store.add_to_logs(
                    current_task.__tablename__,
                    getattr(current_task, primary_key),
                    field=column,
                    previous_value=str(old_value),
                    change_id=change_id,
                )

        self.tree_view.selected_element.object = current_task
        if isinstance(current_task, self.data_store.db_classes.Serial):
            self.tree_view.selected_element.text = current_task.serial_number
            self.tree_view.selected_element.parent.sort_children_by_start_time()
        else:
            self.tree_view.selected_element.text = current_task.name
        get_app().invalidate()
        return True

    def handle_delete(self):
        async def coroutine():
            if isinstance(self.task_edit_widget.task_object, self.data_store.db_classes.Serial):
                name = self.task_edit_widget.task_object.serial_number
            else:
                name = self.task_edit_widget.task_object.name

            if name is None:
                name = "New entry"

            dialog = ConfirmationDialog(
                "Delete?",
                f"Are you sure you want to delete the task\n{name}\nand all its sub-tasks?",
            )
            result = await self.show_dialog_as_float(dialog)

            if not result:
                return

            primary_key_name = get_primary_key_for_table(self.task_edit_widget.task_object)
            pri_key_value = getattr(self.task_edit_widget.task_object, primary_key_name)
            if pri_key_value is not None:
                # We've got a task that has been saved in the database,
                # as it has an id, so we need to delete from the database
                with self.data_store.session_scope():
                    change_id = self.data_store.add_to_changes(
                        USER, datetime.utcnow(), "Manual delete from Tasks GUI"
                    ).change_id
                    self.data_store.delete_objects(
                        type(self.task_edit_widget.task_object),
                        [pri_key_value],
                        change_id=change_id,
                    )
                # with self.data_store.session_scope():
                #     self.data_store.session.delete(self.task_edit_widget.task_object)

            self.tree_view.selected_element.parent.remove_child(self.tree_view.selected_element)
            self.tree_view.select_element(self.tree_view.selected_element.parent)
            if self.tree_view.selected_element is None:
                self.task_edit_widget.set_task_object(None)

        ensure_future(coroutine())

    def handle_tree_select(self, selected_element):
        logger.debug("Starting tree select")
        # with self.data_store.session_scope():
        #     table_object = type(selected_element.object)
        #     selected_element.object = (
        #         self.data_store.session.query(table_object)
        #         .filter(
        #             getattr(table_object, get_primary_key_for_table(table_object))
        #             == getattr(selected_element.object, get_primary_key_for_table(table_object))
        #         )
        #         .options(joinedload("*"))
        #         .one()
        #     )
        selected_element.object = load_participants_attribute(self.data_store, selected_element.object)
        self.task_edit_widget.set_task_object(selected_element.object)
        logger.debug("Ending tree select")

    def handle_tree_add(self, parent_element):
        if isinstance(parent_element.object, self.data_store.db_classes.Series):
            # We clicked Add on a Series, so add a Wargame
            new_object = self.data_store.db_classes.Wargame()
            new_object.series_id = parent_element.object.series_id
        elif isinstance(parent_element.object, self.data_store.db_classes.Wargame):
            # We clicked Add on a Wargame, so add a Serial
            new_object = self.data_store.db_classes.Serial()
            new_object.wargame_id = parent_element.object.wargame_id
            new_object.start = parent_element.object.start
            new_object.end = parent_element.object.end
            new_object.include_in_timeline = True
        else:
            # Do nothing - we can't add anything below a Serial
            return
        new_element = TreeElement("New entry", new_object)
        parent_element.add_child(new_element)
        self.tree_view.select_element(new_element)

    def handle_top_level_add(self):
        new_series = self.data_store.db_classes.Series()
        new_element = TreeElement("New entry", new_series)
        self.tree_view.root_element.add_child(new_element)
        self.tree_view.select_element(new_element)

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

        @kb.add("f2")
        def _(event):
            get_app().layout.focus(self.lh_pane)

        @kb.add("f3")
        def _(event):
            if self.task_edit_widget.task_object is not None:
                get_app().layout.focus(self.rh_pane)

        return kb

    def get_style(self):
        style = Style(
            [
                ("title-line", "bg:ansibrightblack fg:ansiwhite"),
                ("button", "fg:ansibrightblack"),
                ("button.focused button.text", "fg:ansiwhite"),
                ("button.focused button.arrow", "fg:ansiwhite"),
                ("button.focused", "bg:ansiblue"),
                ("dropdown.focused", "bg:ansiblue fg:ansiwhite"),
                ("text-area", "bg:ansigray fg:ansiblack"),
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
                ("tree-selected-element", "bg:ansiblue fg:ansiwhite"),
                ("tree-matched-filter", "fg:ansired"),
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


if __name__ == "__main__":
    try:
        gui = TasksGUI()
        gui.app.run()
    except Exception as e:
        print(traceback.format_exc())
        print(str(e))
        print("Error running GUI, see error message above")
