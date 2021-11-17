from asyncio import Future

from prompt_toolkit.layout.containers import HSplit, VSplit
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.widgets import Button, Label
from prompt_toolkit.widgets.dialogs import Dialog

from pepys_admin.maintenance.widgets.DatetimeWidget import DatetimeWidget
from pepys_admin.maintenance.widgets.dropdown_box import DropdownBox


class SerialParticipantDialog:
    def __init__(self, task_object, force, platforms, privacies, object_to_edit=None):
        """Dialog for editing a SerialParticipant

        :param task_object: Task object that is being edited
        :type task_object: Serial
        :param force: Force that the new/edited Task object should belong to
        :type force: str
        :param platforms: List of platforms for the user to select from in the Dropdown - this is passed rather than
        generated here to save generating the same lists of platforms over and over again. This should include just
        the platforms that are able to be selected - ie. ones that aren't already participating in the serial
        :type platforms: dict with 'values' and 'ids' keys
        :param privacies: List of privacies for the user to select from - again, passed rather than generated each time
        :type privacies: list
        :param object_to_edit: SerialParticipant object to edit in this dialog, defaults to None. If passed, it will pre-populate
        the edit widgets with the values from this object.
        :type object_to_edit: SerialParticipant, optional
        """
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
            self.start_field = DatetimeWidget(no_seconds=True)
        else:
            self.start_field = DatetimeWidget(
                datetime_value=self.object_to_edit.start, no_seconds=True
            )
        start_row = VSplit(
            [Label("Start:", width=15), self.start_field],
            padding=1,
        )

        if self.object_to_edit is None:
            self.end_field = DatetimeWidget(no_seconds=True)
        else:
            self.end_field = DatetimeWidget(datetime_value=self.object_to_edit.end, no_seconds=True)
        end_row = VSplit([Label("End:", width=15), self.end_field], padding=1)

        if self.object_to_edit is None:
            self.privacy_field = DropdownBox(self.privacies["values"][0], self.privacies["values"])
        else:
            self.privacy_field = DropdownBox(
                self.object_to_edit.privacy_name, self.privacies["values"]
            )
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
        """Handles the add button from the dialog box"""
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

        if values["start"] is not None and values["end"] is not None:
            if values["start"] > values["end"]:
                self.error_label.text = "The end time must be after the start time"
                return

        values["privacy"] = self.privacy_field.text

        self.future.set_result(values)

    def handle_cancel(self):
        """Handles the cancel button from the dialog"""
        self.future.set_result(None)

    def __pt_container__(self):
        return self.dialog
