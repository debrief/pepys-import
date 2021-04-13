from asyncio.tasks import ensure_future
from datetime import datetime

from loguru import logger
from prompt_toolkit.application.current import get_app
from prompt_toolkit.layout.containers import DynamicContainer, HSplit, VSplit
from prompt_toolkit.widgets.base import Button

from pepys_admin.maintenance.dialogs.participant_dialog import ParticipantDialog
from pepys_admin.maintenance.widgets.combo_box import ComboBox
from pepys_import.core.store.data_store import USER
from pepys_import.utils.sqlalchemy_utils import get_primary_key_for_table


class ParticipantsWidget:
    def __init__(self, task_edit_widget, platforms, force=None):
        self.task_edit_widget = task_edit_widget
        self.force = force
        self.platforms = platforms

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
            participant_platform_ids = [
                p.platform.platform_id for p in self.task_edit_widget.task_object.participants
            ]

            all_platforms = self.platforms
            filtered_platforms = {"ids": [], "values": []}
            for i in range(len(all_platforms["ids"])):
                if all_platforms["ids"][i] not in participant_platform_ids:
                    filtered_platforms["ids"].append(all_platforms["ids"][i])
                    filtered_platforms["values"].append(all_platforms["values"][i])

            dialog = ParticipantDialog(
                self.task_edit_widget.task_object,
                self.force,
                filtered_platforms,
                self.task_edit_widget.privacies,
            )
            result = await self.task_edit_widget.show_dialog_as_float(dialog)
            if result is None:
                return

            logger.debug(f"{result=}")

            ds = self.task_edit_widget.data_store

            with ds.session_scope():
                change_id = ds.add_to_changes(
                    USER, datetime.utcnow(), "Manual edit in Tasks GUI"
                ).change_id

                self.task_edit_widget.task_object.add_participant(
                    ds, result["platform"], result["privacy"], change_id
                )

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
