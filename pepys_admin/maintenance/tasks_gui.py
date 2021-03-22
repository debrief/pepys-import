import traceback
from asyncio import ensure_future

from prompt_toolkit.application.application import Application
from prompt_toolkit.application.current import get_app
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.layout.containers import Float, FloatContainer, HSplit, VSplit, Window
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets.base import Border, Label

from pepys_admin.maintenance.dialogs.confirmation_dialog import ConfirmationDialog
from pepys_admin.maintenance.widgets.blank_border import BlankBorder
from pepys_admin.maintenance.widgets.tree_view import TreeElement, TreeView
from pepys_import.core.store.data_store import DataStore

root = TreeElement("root", 42)
root.add_child(TreeElement("first level", 14))
root.add_child(TreeElement("first level - 2", 29))
second_level = root.children[0].add_child(TreeElement("second level", 20))
second_level.add_child(TreeElement("third level", 999))


class TasksGUI:
    def __init__(self, data_store=None):
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

        self.init_ui_components()

        self.app = Application(
            layout=self.layout,
            key_bindings=self.get_keybindings(),
            full_screen=True,
            mouse_support=True,
            style=self.get_style(),
        )

    def init_ui_components(self):
        # Putting everything together in panes
        self.tree_view = TreeView(root, height=Dimension(weight=0.8), hide_root=True)
        self.lh_pane = HSplit(
            [
                Label(text="Tasks   F2", style="class:title-line"),
                self.tree_view,
            ],
            padding=1,
        )

        self.rh_pane = HSplit(
            [
                Label(text="View task   F3", style="class:title-line"),
                Label("Task details shown here"),
            ],
            padding=1,
        )

        self.root_container = FloatContainer(
            BlankBorder(
                VSplit(
                    [
                        HSplit([self.lh_pane], width=Dimension(weight=0.3)),
                        Window(width=1, char=Border.VERTICAL),
                        self.rh_pane,
                    ],
                    padding=1,
                )
            ),
            floats=[],
        )

        self.layout = Layout(self.root_container)

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
