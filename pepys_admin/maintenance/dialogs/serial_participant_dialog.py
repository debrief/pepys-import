from asyncio import Future

from prompt_toolkit.layout.containers import HSplit, VSplit
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.widgets import Button, Label
from prompt_toolkit.widgets.dialogs import Dialog

from pepys_admin.maintenance.widgets.DatetimeWidget import DatetimeWidget
from pepys_admin.maintenance.widgets.dropdown_box import DropdownBox


class SerialParticipantDialog:
    def __init__(self, task_object, force, platforms, privacies):
        self.future = Future()

        self.task_object = task_object
        self.force = force
        self.platforms = platforms
        self.privacies = privacies

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

        self.end_field = DatetimeWidget()
        end_row = VSplit([Label("End:", width=15), self.end_field], padding=1)

        self.privacy_field = DropdownBox(self.privacies["values"][0], self.privacies["values"])
        privacy_row = VSplit(
            [Label("Privacy (*):", width=15), self.privacy_field],
            padding=1,
        )

        self.error_label = Label("")

        self.body = HSplit(
            [platform_row, privacy_row, start_row, end_row, self.error_label], padding=2, width=78
        )

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
        values = {}

        if self.platform_field.text == "Select a platform":
            self.error_label.text = "You must select a platform"
            return
        else:
            self.error_label.text = ""

        platform_index = self.platforms["values"].index(self.platform_field.text)
        values["platform"] = self.platforms["ids"][platform_index]

        values["start"] = self.start_field.datetime_value
        values["end"] = self.end_field.datetime_value

        values["privacy"] = self.privacy_field.text

        self.future.set_result(values)

    def handle_cancel(self):
        self.future.set_result(None)

    def __pt_container__(self):
        return self.dialog
