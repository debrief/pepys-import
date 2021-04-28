from prompt_toolkit.layout.containers import DynamicContainer, HorizontalAlign, HSplit, VSplit
from prompt_toolkit.widgets.base import Button, Checkbox, Label, TextArea
from prompt_toolkit.widgets.toolbars import ValidationToolbar

from pepys_admin.maintenance.utils import empty_str_if_none
from pepys_admin.maintenance.widgets.DatetimeWidget import DatetimeWidget
from pepys_admin.maintenance.widgets.dropdown_box import DropdownBox
from pepys_admin.maintenance.widgets.participants_widget import ParticipantsWidget
from pepys_import.core.store.common_db import SerialMixin, SeriesMixin, WargameMixin


class TaskEditWidget:
    def __init__(
        self,
        task_object,
        privacies,
        platforms,
        save_button_handler,
        delete_button_handler,
        duplicate_button_handler,
        data_store,
        show_dialog_as_float,
    ):
        self.privacies = privacies
        self.platforms = platforms
        self.save_button_handler = save_button_handler
        self.delete_button_handler = delete_button_handler
        self.duplicate_button_handler = duplicate_button_handler
        self.data_store = data_store
        # Reference to the main show_dialog_as_float method, so we can show a dialog from
        # the ParticipantsWidget
        self.show_dialog_as_float = show_dialog_as_float

        self.set_task_object(task_object)

        self.container = DynamicContainer(self.get_widgets)

    def get_widgets(self):
        return HSplit(self.all_rows, padding=1)

    def get_updated_fields(self):
        updated_fields = {}

        if self.privacy_field.text != self.task_object.privacy_name:
            index = self.privacies["values"].index(self.privacy_field.text)
            updated_fields["privacy_id"] = str(self.privacies["ids"][index])

        if isinstance(self.task_object, SeriesMixin):
            if self.name_field.text != empty_str_if_none(self.task_object.name):
                updated_fields["name"] = self.name_field.text
        elif isinstance(self.task_object, WargameMixin):
            if self.name_field.text != empty_str_if_none(self.task_object.name):
                updated_fields["name"] = self.name_field.text

            if self.start_field.datetime_value != self.task_object.start:
                updated_fields["start"] = self.start_field.datetime_value

            if self.end_field.datetime_value != self.task_object.end:
                updated_fields["end"] = self.end_field.datetime_value
        elif isinstance(self.task_object, SerialMixin):
            if self.number_field.text != empty_str_if_none(self.task_object.serial_number):
                updated_fields["serial_number"] = self.number_field.text

            if self.exercise_field.text != empty_str_if_none(self.task_object.exercise):
                updated_fields["exercise"] = self.exercise_field.text

            if self.start_field.datetime_value != self.task_object.start:
                updated_fields["start"] = self.start_field.datetime_value

            if self.end_field.datetime_value != self.task_object.end:
                updated_fields["end"] = self.end_field.datetime_value

            if self.include_in_timeline.checked != self.task_object.include_in_timeline:
                updated_fields["include_in_timeline"] = self.include_in_timeline.checked

        return updated_fields

    def create_widgets(self):
        if self.task_object is None:
            self.all_rows = [Label("Please select a Task")]
            return

        if isinstance(self.task_object, self.data_store.db_classes.Series):
            object_name = "series"
        elif isinstance(self.task_object, self.data_store.db_classes.Serial):
            object_name = "serial"
        elif isinstance(self.task_object, self.data_store.db_classes.Wargame):
            object_name = "wargame"

        self.save_button = Button(f"Save {object_name}", self.save_button_handler, width=15)
        self.delete_button = Button(f"Delete {object_name}", self.delete_button_handler, width=20)
        self.duplicate_button = Button(
            f"Duplicate {object_name}", self.duplicate_button_handler, width=20
        )

        if isinstance(self.task_object, self.data_store.db_classes.Serial):
            buttons = [self.save_button, self.delete_button, self.duplicate_button]
        else:
            buttons = [self.save_button, self.delete_button]

        self.buttons_row = VSplit(buttons, padding=3, align=HorizontalAlign.LEFT)

        try:
            if self.task_object.privacy_name is not None:
                privacy_text = self.task_object.privacy_name
            else:
                privacy_text = self.privacies["values"][0]
        except Exception:
            privacy_text = self.privacies["values"][0]
        self.privacy_field = DropdownBox(privacy_text, self.privacies["values"])
        self.privacy_row = VSplit(
            [Label("Privacy (*):", width=21), self.privacy_field],
            padding=2,
            align=HorizontalAlign.LEFT,
        )

        self.validation_toolbar = ValidationToolbar()

        # We check the instances against the Mixins here, as we don't know if we're running
        # Postgres or SQLite, and we have different instances of the actual objects for different
        # databases - but the mixins are always the same. (This stops us having to have a data_store
        # instance accessible here too)
        if isinstance(self.task_object, SeriesMixin):
            self.name_field = TextArea(
                text=empty_str_if_none(self.task_object.name), multiline=False, focus_on_click=True
            )
            self.name_row = VSplit(
                [Label("Series Name (*):", width=21), self.name_field],
                padding=2,
                align=HorizontalAlign.LEFT,
            )

            self.all_rows = [
                self.name_row,
                self.privacy_row,
                self.validation_toolbar,
                self.buttons_row,
            ]
        elif isinstance(self.task_object, WargameMixin):
            self.name_field = TextArea(
                text=empty_str_if_none(self.task_object.name), multiline=False, focus_on_click=True
            )
            self.name_row = VSplit(
                [Label("Wargame Name (*):", width=21), self.name_field],
                padding=2,
                align=HorizontalAlign.LEFT,
            )

            self.start_field = DatetimeWidget(self.task_object.start, no_seconds=True)
            self.start_row = VSplit(
                [Label("Start (*):", width=21), self.start_field],
                padding=2,
                align=HorizontalAlign.LEFT,
            )

            self.end_field = DatetimeWidget(self.task_object.end, no_seconds=True)

            self.end_row = VSplit(
                [Label("End (*):", width=21), self.end_field], padding=2, align=HorizontalAlign.LEFT
            )

            self.participants_widget = ParticipantsWidget(self, self.platforms, combo_height=15)

            self.participants_row = VSplit(
                [Label("Participants:", width=21), self.participants_widget], padding=2
            )

            self.all_rows = [
                self.name_row,
                self.start_row,
                self.end_row,
                self.privacy_row,
                self.participants_row,
                self.validation_toolbar,
                self.buttons_row,
            ]
        elif isinstance(self.task_object, SerialMixin):
            self.number_field = TextArea(
                text=empty_str_if_none(self.task_object.serial_number),
                multiline=False,
                focus_on_click=True,
            )
            self.number_row = VSplit(
                [Label("Serial Number (*):", width=25), self.number_field],
                padding=2,
                align=HorizontalAlign.LEFT,
            )

            self.exercise_field = TextArea(
                text=empty_str_if_none(self.task_object.exercise),
                multiline=False,
                focus_on_click=True,
            )
            self.exercise_row = VSplit(
                [Label("Serial Exercise:", width=25), self.exercise_field],
                padding=2,
                align=HorizontalAlign.LEFT,
            )

            self.start_field = DatetimeWidget(self.task_object.start, no_seconds=True)
            self.start_row = VSplit(
                [Label("Start (*):", width=25), self.start_field],
                padding=2,
                align=HorizontalAlign.LEFT,
            )

            self.end_field = DatetimeWidget(self.task_object.end, no_seconds=True)

            self.end_row = VSplit(
                [Label("End (*):", width=25), self.end_field], padding=2, align=HorizontalAlign.LEFT
            )

            self.blue_participants_widget = ParticipantsWidget(self, force="Blue", combo_height=15)

            self.blue_participants_row = VSplit(
                [
                    Label("Blue Force Participants:", width=25),
                    self.blue_participants_widget,
                ],
                padding=2,
                align=HorizontalAlign.LEFT,
            )

            self.red_participants_widget = ParticipantsWidget(self, force="Red", combo_height=5)

            self.red_participants_row = VSplit(
                [
                    Label("Red Force Participants:", width=25),
                    self.red_participants_widget,
                ],
                padding=2,
                align=HorizontalAlign.LEFT,
            )

            # An empty string is given here as the text for the checkbox, as we're using
            # a separate label, so that we can get the text on the LH side
            self.include_in_timeline = Checkbox("", checked=self.task_object.include_in_timeline)
            self.include_in_timeline_row = VSplit(
                [Label("Include in timeline (*):", width=25), self.include_in_timeline],
                padding=2,
                align=HorizontalAlign.LEFT,
            )

            self.all_rows = [
                self.number_row,
                self.exercise_row,
                self.start_row,
                self.end_row,
                self.privacy_row,
                self.include_in_timeline_row,
                self.blue_participants_row,
                self.red_participants_row,
                self.validation_toolbar,
                self.buttons_row,
            ]

    def set_task_object(self, task_object):
        self.task_object = task_object

        self.create_widgets()

    def __pt_container__(self):
        return self.container
