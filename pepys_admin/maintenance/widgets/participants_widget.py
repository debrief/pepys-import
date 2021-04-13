from asyncio.tasks import ensure_future

from loguru import logger
from prompt_toolkit.application.current import get_app
from prompt_toolkit.layout.containers import DynamicContainer, HSplit, VSplit
from prompt_toolkit.widgets.base import Button

from pepys_admin.maintenance.dialogs.participant_dialog import ParticipantDialog
from pepys_admin.maintenance.widgets.combo_box import ComboBox
from pepys_import.utils.sqlalchemy_utils import get_primary_key_for_table


class ParticipantsWidget:
    def __init__(self, task_edit_widget, force=None):
        self.task_edit_widget = task_edit_widget
        self.force = force

        self.create_widgets()

        self.container = DynamicContainer(self.get_widgets)

    def create_widgets(self):
        self.combo_box = ComboBox(
            self.get_combo_box_entries, height=8, highlight_without_focus=True
        )
        self.add_button = Button("Add", handler=self.handle_add_button)
        self.delete_button = Button("Delete", handler=self.handle_delete_button)

    def get_combo_box_entries(self):
        if self.force is None:
            self.participants = self.task_edit_widget.task_object.participants
        else:
            self.participants = [
                p
                for p in self.task_edit_widget.task_object.participants
                if p.force_type_name == self.force
            ]

        return [
            f"{p.platform_name} - {p.platform_identifier} - {p.platform_nationality_name}"
            for p in self.participants
        ]

    def handle_add_button(self):
        async def coroutine():
            dialog = ParticipantDialog(
                self.task_edit_widget.task_object, self.force, {"values": ["Plat 1", "Plat 2"]}
            )
            await self.task_edit_widget.show_dialog_as_float(dialog)

        ensure_future(coroutine())

    def handle_delete_button(self):
        ds = self.task_edit_widget.data_store
        participant = self.participants[self.combo_box.selected_entry]

        logger.debug(f"{self.task_edit_widget.task_object=}")

        with ds.session_scope():
            ds.delete_objects(
                participant.__tablename__,
                [getattr(participant, get_primary_key_for_table(participant))],
            )

            ds.session.add(self.task_edit_widget.task_object)
            ds.session.refresh(self.task_edit_widget.task_object)
            ds.session.expunge_all()
        get_app().invalidate()

    def get_widgets(self):
        return HSplit([self.combo_box, VSplit([self.add_button, self.delete_button])])

    def __pt_container__(self):
        return self.container
