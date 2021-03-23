from prompt_toolkit.layout.containers import DynamicContainer, HorizontalAlign, HSplit, VSplit
from prompt_toolkit.widgets.base import Label, TextArea
from prompt_toolkit.widgets.toolbars import ValidationToolbar

from pepys_admin.maintenance.widgets.DatetimeWidget import DatetimeWidget
from pepys_admin.maintenance.widgets.dropdown_box import DropdownBox


def empty_str_if_none(value):
    if value is None:
        return ""
    else:
        return value


class TaskEditWidget:
    def __init__(self, task_object, level, privacies):
        self.privacies = privacies

        self.set_task_object(task_object, level)

        self.container = DynamicContainer(self.get_widgets)

    def get_widgets(self):
        return HSplit(self.all_rows, padding=1)

    def create_widgets(self):
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

        privacy_text = (
            self.task_object.privacy_name if self.task_object is not None else "Select privacy"
        )
        self.privacy_field = DropdownBox(privacy_text, self.privacies)
        self.privacy_row = VSplit(
            [Label("Privacy:", width=15), self.privacy_field], padding=2, align=HorizontalAlign.LEFT
        )

        self.validation_toolbar = ValidationToolbar()

        if self.level == 1:
            # 1st level task, so no start/end or participants
            self.all_rows = [self.name_row, self.privacy_row, self.validation_toolbar]
        else:
            self.all_rows = [
                self.name_row,
                self.start_row,
                self.end_row,
                self.privacy_row,
                self.validation_toolbar,
            ]

    def set_task_object(self, task_object, level):
        self.task_object = task_object
        self.level = level

        self.create_widgets()

    def __pt_container__(self):
        return self.container
