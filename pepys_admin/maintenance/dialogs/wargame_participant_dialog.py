from asyncio import Future

from prompt_toolkit.layout.containers import HSplit, VSplit
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.widgets import Button, Label
from prompt_toolkit.widgets.dialogs import Dialog

from pepys_admin.maintenance.widgets.dropdown_box import DropdownBox


class WargameParticipantDialog:
    def __init__(self, task_object, platforms, privacies, object_to_edit=None):
        """Dialog for editing a SerialParticipant

        :param task_object: Task object that is being edited
        :type task_object: Wargame
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

        title = "Add participant"

        if self.object_to_edit is None:
            self.platform_field = DropdownBox("Select a platform", self.platforms["values"])
        else:
            self.platform_field = DropdownBox(self.platforms["values"][0], self.platforms["values"])
        platform_row = VSplit([Label("Platform (*):", width=15), self.platform_field], padding=1)

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

        self.body = HSplit([platform_row, privacy_row, self.error_label], padding=2, width=78)

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

        values["privacy"] = self.privacy_field.text

        self.future.set_result(values)

    def handle_cancel(self):
        self.future.set_result(None)

    def __pt_container__(self):
        return self.dialog
