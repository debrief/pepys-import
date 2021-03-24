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
from sqlalchemy.orm import undefer

from pepys_admin.maintenance.dialogs.confirmation_dialog import ConfirmationDialog
from pepys_admin.maintenance.widgets.blank_border import BlankBorder
from pepys_admin.maintenance.widgets.task_edit_widget import TaskEditWidget
from pepys_admin.maintenance.widgets.tree_view import TreeElement, TreeView
from pepys_import.core.store import constants
from pepys_import.core.store.data_store import USER, DataStore

logger.remove()
logger.add("gui.log")

# Uncomment the lines below to get logging of the SQL queries run by SQLAlchemy
# to the file sql.log
# import logging

# logging.basicConfig(filename="sql.log", level=logging.DEBUG)
# logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)


class TasksGUI:
    def __init__(self, data_store=None):
        print("Initialising GUI and loading tasks...")

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

        self.current_dialog = None

        self.root_task = self.get_tasks_into_treeview()

        self.privacies = self.get_privacies()

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
        all_privacies = (
            self.data_store.session.query(self.data_store.db_classes.Privacy)
            .order_by(self.data_store.db_classes.Privacy.level)
            .all()
        )
        privacy_strs = [priv.name for priv in all_privacies]
        privacy_ids = [priv.privacy_id for priv in all_privacies]

        return {"values": privacy_strs, "ids": privacy_ids}

    def get_tasks_into_treeview(self):
        Task = self.data_store.db_classes.Task
        id_to_element = {}

        root = TreeElement("hidden root")
        id_to_element[None] = root

        with self.data_store.session_scope():
            task_queue = (
                self.data_store.session.query(Task)
                .filter(Task.parent_id.is_(None))
                .order_by(Task.created_date.desc())
                .options(undefer("*"))
                .all()
            )
            self.data_store.session.expunge_all()
            while len(task_queue) > 0:
                task = task_queue.pop()
                tree_el = TreeElement(task.name, task)
                id_to_element[task.task_id] = tree_el
                parent_task = id_to_element[task.parent_id]
                parent_task.add_child(tree_el)

                # Add children to queue
                children_of_current_task = (
                    self.data_store.session.query(Task)
                    .filter(Task.parent_id == task.task_id)
                    .order_by(Task.created_date.desc())
                    .options(undefer("*"))
                    .all()
                )
                self.data_store.session.expunge_all()
                task_queue.extend(children_of_current_task)

        return root

    def init_ui_components(self):
        self.tree_view = TreeView(
            self.root_task,
            height=Dimension(weight=0.8),
            hide_root=True,
            on_add=self.handle_tree_add,
            on_select=self.handle_tree_select,
        )
        self.top_level_add_button = Button("Add task", self.handle_top_level_add)
        self.lh_pane = HSplit(
            [
                Label(text="Tasks   F2", style="class:title-line"),
                self.tree_view,
                self.top_level_add_button,
            ],
            padding=1,
        )

        current_task_object = (
            self.tree_view.selected_element.object if self.tree_view.selected_element else None
        )

        self.task_edit_widget = TaskEditWidget(
            current_task_object,
            1,
            self.privacies,
            self.handle_save,
            self.handle_delete,
        )
        self.rh_pane = HSplit(
            [
                Label(text="View task   F3", style="class:title-line"),
                self.task_edit_widget,
            ],
            padding=1,
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

    def handle_save(self):
        updated_fields = self.task_edit_widget.get_updated_fields()
        if updated_fields == {}:
            return

        logger.debug(f"{updated_fields=}")

        current_task = self.task_edit_widget.task_object

        # Keep track of the old values for adding to Logs later
        old_values = {}
        for column in updated_fields.keys():
            old_values[column] = getattr(current_task, column)

        # Set the new values
        for column, new_value in updated_fields.items():
            setattr(current_task, column, new_value)

        with self.data_store.session_scope():
            self.data_store.session.add(current_task)
            # We need to commit the change so that it gets an ID and matches everything up
            # but this 'expires' the attributes, so we need to refresh these from the database
            # before expunging. Overall, this means that the fully up-to-date Task object
            # is detached from the session and available for use in the UI
            self.data_store.session.commit()
            self.data_store.session.refresh(current_task)
            self.data_store.session.expunge_all()

        # Record Change and Logs for this change
        # (we have to do this after adding the Task and committing
        # otherwise the Task won't have a task_id
        with self.data_store.session_scope():
            change_id = self.data_store.add_to_changes(
                USER, datetime.utcnow(), "Manual edit in Tasks GUI"
            ).change_id
            for column, old_value in old_values.items():
                self.data_store.add_to_logs(
                    constants.TASK,
                    current_task.task_id,
                    field=column,
                    previous_value=old_value,
                    change_id=change_id,
                )

        self.tree_view.selected_element.object = current_task
        self.tree_view.selected_element.text = current_task.name
        get_app().invalidate()

    def handle_delete(self):
        pass

    def handle_tree_select(self, selected_element):
        self.task_edit_widget.set_task_object(selected_element.object, level=selected_element.level)

    def handle_tree_add(self, parent_element):
        new_task = self.data_store.db_classes.Task()
        if parent_element.object is not None:
            new_task.parent = parent_element.object
        new_element = TreeElement("New entry", new_task)
        parent_element.add_child(new_element)

    def handle_top_level_add(self):
        new_task = self.data_store.db_classes.Task()
        # As it's a top level task, set stupidly early/late start and end
        # so that any tasks later on can come within these times (and so
        # that it is obvious that they're fake dates)
        new_task.start = datetime(1, 1, 1, 0, 0, 0)
        new_task.end = datetime(9999, 1, 1, 0, 0, 0)
        new_element = TreeElement("New entry", new_task)
        self.tree_view.root_element.add_child(new_element)

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
                ("text-area", "bg:ansigray"),
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
                ("tree-level-1", "fg:ansibrightred"),
                ("tree-level-2", "fg:ansibrightblue"),
                ("tree-level-3", "fg:ansibrightgreen"),
                ("tree-selected-element", "bg:ansigray"),
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


if __name__ == "__main__":
    try:
        gui = TasksGUI()
        gui.app.run()
    except Exception as e:
        print(traceback.format_exc())
        print(str(e))
        print("Error running GUI, see error message above")
