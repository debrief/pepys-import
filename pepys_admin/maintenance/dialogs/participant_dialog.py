from asyncio import Future

from prompt_toolkit.layout.containers import HSplit, VSplit
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.widgets import Button, Label
from prompt_toolkit.widgets.dialogs import Dialog

from pepys_admin.maintenance.widgets.DatetimeWidget import DatetimeWidget
from pepys_admin.maintenance.widgets.dropdown_box import DropdownBox


class ParticipantDialog:
    def __init__(self, task_object, force, platforms):
        self.future = Future()

        self.task_object = task_object
        self.force = force
        self.platforms = platforms

        add_button = Button(text="Add", handler=self.handle_add)
        cancel_button = Button(text="Cancel", handler=self.handle_cancel)

        if force is None:
            title = "Add participant"
        else:
            title = f"Add {force} participant"

        self.platform_field = DropdownBox("Select a platform", self.platforms["values"])
        platform_row = VSplit([Label("Platform (*):", width=15), self.platform_field], padding=1)

        self.start_field = DatetimeWidget()
        start_row = VSplit(
            [Label("Start:", width=15), self.start_field],
            padding=1,
        )

        self.end_row = DatetimeWidget()
        end_row = VSplit([Label("End:", width=15), self.end_row], padding=1)

        self.body = HSplit([platform_row, start_row, end_row], padding=2, width=78)

        self.dialog = Dialog(
            title=title,
            body=self.body,
            buttons=[add_button, cancel_button],
            width=D(preferred=80),
            modal=True,
        )

        # Get the keybindings for the dialog and add a binding for Esc
        # to close the dialog
        dialog_kb = self.dialog.container.container.content.key_bindings

        @dialog_kb.add("escape")
        def _(event) -> None:
            self.handle_cancel()

    def handle_add(self):
        self.future.set_result(True)

    def handle_cancel(self):
        self.future.set_result(False)

    def __pt_container__(self):
        return self.dialog
