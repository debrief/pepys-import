from asyncio import Future

from prompt_toolkit.layout.containers import HSplit, VSplit
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.widgets import Button, Label
from prompt_toolkit.widgets.dialogs import Dialog

from pepys_admin.maintenance.widgets.DatetimeWidget import DatetimeWidget
from pepys_admin.maintenance.widgets.dropdown_box import DropdownBox


class SerialParticipantDialog:
    def __init__(self, task_object, force, platforms, privacies, object_to_edit=None):
        self.future = Future()

        self.task_object = task_object
        self.force = force
        self.platforms = platforms
        self.privacies = privacies
        self.object_to_edit = object_to_edit

        add_button = Button(text="Add", handler=self.handle_add)
        save_button = Button(text="Save", handler=self.handle_add)
        cancel_button = Button(text="Cancel", handler=self.handle_cancel)

        if object_to_edit is not None:
            buttons = [save_button, cancel_button]
        else:
            buttons = [add_button, cancel_button]

        if force is None:
            title = "Add participant"
        else:
            title = f"Add {force} participant"

        if self.object_to_edit is None:
            self.platform_field = DropdownBox("Select a platform", self.platforms["values"])
        else:
            self.platform_field = DropdownBox(self.platforms["values"][0], self.platforms["values"])
        platform_row = VSplit([Label("Platform (*):", width=15), self.platform_field], padding=1)

        if self.object_to_edit is None:
            self.start_field = DatetimeWidget()
        else:
            self.start_field = DatetimeWidget(datetime_value=self.object_to_edit.start)
        start_row = VSplit(
            [Label("Start:", width=15), self.start_field],
            padding=1,
        )

        if self.object_to_edit is None:
            self.end_field = DatetimeWidget()
        else:
            self.end_field = DatetimeWidget(datetime_value=self.object_to_edit.end)
        end_row = VSplit([Label("End:", width=15), self.end_field], padding=1)

        if self.object_to_edit is None:
            self.privacy_field = DropdownBox(self.privacies["values"][0], self.privacies["values"])
        else:
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
            buttons=buttons,
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

        try:
            values["start"] = self.start_field.datetime_value
        except ValueError:
            self.error_label.text = "You must enter a valid start time, or leave it empty"
            return
        try:
            values["end"] = self.end_field.datetime_value
        except ValueError:
            self.error_label.text = "You must enter a valid end time, or leave it empty"
            return

        values["privacy"] = self.privacy_field.text

        self.future.set_result(values)

    def handle_cancel(self):
        self.future.set_result(None)

    def __pt_container__(self):
        return self.dialog
