from asyncio.tasks import ensure_future
from datetime import datetime

from loguru import logger
from prompt_toolkit.application.current import get_app
from prompt_toolkit.layout.containers import DynamicContainer, HSplit, VSplit
from prompt_toolkit.widgets.base import Button

from pepys_admin.maintenance.dialogs.serial_participant_dialog import SerialParticipantDialog
from pepys_admin.maintenance.dialogs.wargame_participant_dialog import WargameParticipantDialog
from pepys_admin.maintenance.widgets.combo_box import ComboBox
from pepys_import.core.store.data_store import USER
from pepys_import.utils.sqlalchemy_utils import get_primary_key_for_table


class ParticipantsWidget:
    def __init__(self, task_edit_widget, platforms=None, force=None):
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
        async def coroutine_wargame():
            participant_platform_ids = [
                p.platform.platform_id for p in self.task_edit_widget.task_object.participants
            ]

            all_platforms = self.platforms
            filtered_platforms = {"ids": [], "values": []}
            for i in range(len(all_platforms["ids"])):
                if all_platforms["ids"][i] not in participant_platform_ids:
                    filtered_platforms["ids"].append(all_platforms["ids"][i])
                    filtered_platforms["values"].append(all_platforms["values"][i])

            dialog = WargameParticipantDialog(
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

        async def coroutine_serial():
            ds = self.task_edit_widget.data_store

            with ds.session_scope():
                ds.session.add(self.task_edit_widget.task_object)
                ds.session.refresh(self.task_edit_widget.task_object)

                participant_platform_ids = [
                    p.platform.platform_id for p in self.task_edit_widget.task_object.participants
                ]

                wargame_participants = self.task_edit_widget.task_object.wargame.participants
                wargame_platforms = {}
                wargame_platforms["ids"] = [
                    wgp.wargame_participant_id for wgp in wargame_participants
                ]
                wargame_platforms["platform_ids"] = [
                    wgp.platform.platform_id for wgp in wargame_participants
                ]
                wargame_platforms["values"] = [
                    f"{wgp.platform.name} / {wgp.platform.identifier} / {wgp.platform.nationality_name}"
                    for wgp in wargame_participants
                ]
                filtered_platforms = {"ids": [], "values": []}
                for i in range(len(wargame_platforms["ids"])):
                    if wargame_platforms["platform_ids"][i] not in participant_platform_ids:
                        filtered_platforms["ids"].append(wargame_platforms["ids"][i])
                        filtered_platforms["values"].append(wargame_platforms["values"][i])

            dialog = SerialParticipantDialog(
                self.task_edit_widget.task_object,
                self.force,
                filtered_platforms,
                self.task_edit_widget.privacies,
            )
            result = await self.task_edit_widget.show_dialog_as_float(dialog)
            if result is None:
                return

            logger.debug(f"Serial Dialog result {result=}")

            with ds.session_scope():
                change_id = ds.add_to_changes(
                    USER, datetime.utcnow(), "Manual edit in Tasks GUI"
                ).change_id

                self.task_edit_widget.task_object.add_participant(
                    data_store=ds,
                    wargame_participant=result["platform"],
                    force_type=self.force,
                    privacy=result["privacy"],
                    start=result["start"],
                    end=result["end"],
                    change_id=change_id,
                )

        # We need to save the task before adding a participant, or we don't have the database
        # ID to link the participant to the task. So we call the save method.
        # However, if the save_button_handler method returns False then there has been a validation
        # error, and we shouldn't try and add a participant - and then the user will see the validation
        # dialog.
        if not self.task_edit_widget.save_button_handler():
            return

        if isinstance(
            self.task_edit_widget.task_object, self.task_edit_widget.data_store.db_classes.Wargame
        ):
            ensure_future(coroutine_wargame())
        elif isinstance(
            self.task_edit_widget.task_object, self.task_edit_widget.data_store.db_classes.Serial
        ):
            ensure_future(coroutine_serial())

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
