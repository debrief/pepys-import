from loguru import logger
from prompt_toolkit.layout.containers import DynamicContainer, HorizontalAlign, HSplit, VSplit
from prompt_toolkit.widgets.base import Button, Label, TextArea
from prompt_toolkit.widgets.toolbars import ValidationToolbar

from pepys_admin.maintenance.utils import empty_str_if_none
from pepys_admin.maintenance.widgets.DatetimeWidget import DatetimeWidget
from pepys_admin.maintenance.widgets.dropdown_box import DropdownBox


class TaskEditWidget:
    def __init__(self, task_object, level, privacies, save_button_handler, delete_button_handler):
        self.privacies = privacies
        self.save_button_handler = save_button_handler
        self.delete_button_handler = delete_button_handler

        self.set_task_object(task_object, level)

        self.container = DynamicContainer(self.get_widgets)

    def get_widgets(self):
        return HSplit(self.all_rows, padding=1)

    def get_updated_fields(self):
        updated_fields = {}

        if self.name_field.text != empty_str_if_none(self.task_object.name):
            updated_fields["name"] = self.name_field.text

        if self.start_field.datetime_value != self.task_object.start:
            updated_fields["start"] = self.start_field.datetime_value

        if self.end_field.datetime_value != self.task_object.end:
            updated_fields["end"] = self.end_field.datetime_value

        if self.privacy_field.text != self.task_object.privacy_name:
            index = self.privacies["values"].index(self.privacy_field.text)
            updated_fields["privacy_id"] = str(self.privacies["ids"][index])

        return updated_fields

    def create_widgets(self):
        if self.task_object is None:
            self.all_rows = [Label("Please select a Task")]
            return

        self.save_button = Button("Save task", self.save_button_handler, width=15)
        self.delete_button = Button("Delete task", self.delete_button_handler, width=15)
        self.buttons_row = VSplit(
            [self.save_button, self.delete_button], padding=3, align=HorizontalAlign.LEFT
        )

        self.name_field = TextArea(
            text=empty_str_if_none(self.task_object.name), multiline=False, focus_on_click=True
        )
        self.name_row = VSplit(
            [Label("Name:", width=15), self.name_field], padding=2, align=HorizontalAlign.LEFT
        )

        self.start_field = DatetimeWidget(self.task_object.start)
        self.start_row = VSplit(
            [Label("Start:", width=15), self.start_field], padding=2, align=HorizontalAlign.LEFT
        )

        self.end_field = DatetimeWidget(self.task_object.end)

        self.end_row = VSplit(
            [Label("End:", width=15), self.end_field], padding=2, align=HorizontalAlign.LEFT
        )
        logger.debug(f"{self.task_object.privacy_name=}")
        try:
            if self.task_object.privacy_name is not None:
                privacy_text = self.task_object.privacy_name
            else:
                privacy_text = "Select privacy"
        except Exception:
            privacy_text = "Select privacy"
        self.privacy_field = DropdownBox(privacy_text, self.privacies["values"])
        self.privacy_row = VSplit(
            [Label("Privacy:", width=15), self.privacy_field], padding=2, align=HorizontalAlign.LEFT
        )

        self.validation_toolbar = ValidationToolbar()

        if self.level == 1:
            # 1st level task, so no start/end or participants
            self.all_rows = [
                self.name_row,
                self.privacy_row,
                self.validation_toolbar,
                self.buttons_row,
            ]
        else:
            self.all_rows = [
                self.name_row,
                self.start_row,
                self.end_row,
                self.privacy_row,
                self.validation_toolbar,
                self.buttons_row,
            ]

    def set_task_object(self, task_object, level):
        self.task_object = task_object
        self.level = level

        self.create_widgets()

    def __pt_container__(self):
        return self.container
