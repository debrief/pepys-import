from asyncio.tasks import ensure_future
from datetime import datetime

from prompt_toolkit.application.current import get_app
from prompt_toolkit.layout.containers import DynamicContainer, HSplit, VSplit
from prompt_toolkit.widgets.base import Button

from pepys_admin.maintenance.dialogs.serial_participant_dialog import SerialParticipantDialog
from pepys_admin.maintenance.dialogs.wargame_participant_dialog import WargameParticipantDialog
from pepys_admin.maintenance.utils import load_participants_attribute, trim_string
from pepys_admin.maintenance.widgets.combo_box import ComboBox
from pepys_import.core.store import constants
from pepys_import.core.store.data_store import USER
from pepys_import.utils.sqlalchemy_utils import get_primary_key_for_table

from loguru import logger

class ParticipantsWidget:
    def __init__(
        self, task_edit_widget, platforms=None, force=None, combo_height=8, combo_width=80
    ):
        """Widget for showing a list of participants, with Add/Edit/Delete buttons

        :param task_edit_widget: Reference to the TaskEditWidget instance that this widget is contained within
        :type task_edit_widget: TaskEditWidget
        :param platforms: List of platforms that the user can select from when adding/editing a participant, defaults to None
        :type platforms: dict with 'ids' and 'values' keys, optional
        :param force: Force to show/add/edit participants for, defaults to None. If None then show all participants (used for
        WargameParticipants that do not have a force), otherwise if a string then show all participants where force_name == the string.
        :type force: str, optional
        :param combo_height: Height of the ComboBox used to display participants list, defaults to 8
        :type combo_height: int, optional
        :param combo_width: Width of the ComboBox used to display participants list, defaults to 80
        :type combo_width: int, optional
        """
        self.task_edit_widget = task_edit_widget
        self.force = force
        self.platforms = platforms
        self.combo_height = combo_height
        self.combo_width = combo_width

        self.create_widgets()

        self.container = DynamicContainer(self.get_widgets)

    def create_widgets(self):
        self.combo_box = ComboBox(
            self.get_combo_box_entries,
            height=self.combo_height,
            width=self.combo_width,
            highlight_without_focus=True,
        )
        self.add_button = Button("Add", handler=self.handle_add_button)
        self.edit_button = Button("Edit", handler=self.handle_edit_button)
        self.delete_button = Button("Delete", handler=self.handle_delete_button)
        self.switch_button = Button("Switch force", width=20, handler=self.handle_switch_button)

    def get_combo_box_entries(self):
        if self.force is None:
            self.participants = self.task_edit_widget.task_object.participants
        else:
            self.participants = [
                p
                for p in self.task_edit_widget.task_object.participants
                if p.force_type_name == self.force
            ]

        # We have to sort here rather than in an ORDER BY clause when querying the database
        # as we want to sort by a SQLAlchemy association proxy (platform_name), which is a field
        # which isn't actually in the WargameParticipants/SerialParticipants table
        # (the alternative is a more complex join that does the sort, but this is simpler to
        # implement and works well)
        self.participants = sorted(self.participants, key=lambda x: x.platform_name)

        entries = []

        for p in self.participants:
            trimmed_identifier = trim_string(p.platform_identifier, 5)
            trimmed_nationality = trim_string(p.platform_nationality_name, 4)

            new_entry = f"{p.platform_name} - {trimmed_identifier} - {trimmed_nationality}"
            if (
                isinstance(
                    self.task_edit_widget.task_object,
                    self.task_edit_widget.data_store.db_classes.Serial,
                )
                and p.start is not None
                and p.end is not None
            ):
                start = datetime.strftime(p.start, "%Y-%m-%d %H:%M")
                end = datetime.strftime(p.end, "%Y-%m-%d %H:%M")
                new_entry += f" - {start} - {end}"
            entries.append(new_entry)

        return entries

    def filter_serial_participants(self, include_participant=None):
        participant_platform_ids = [
            p.platform.platform_id for p in self.task_edit_widget.task_object.participants
        ]

        wargame_participants = self.task_edit_widget.task_object.wargame.participants
        wargame_platforms = {}
        wargame_platforms["ids"] = [wgp.wargame_participant_id for wgp in wargame_participants]
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

        if include_participant is not None:
            wgp = include_participant.wargame_participant
            # Add it to the beginning of the list, so we can easily select it
            filtered_platforms["ids"].insert(0, wgp.wargame_participant_id)
            filtered_platforms["values"].insert(
                0,
                f"{wgp.platform.name} / {wgp.platform.identifier} / {wgp.platform.nationality_name}",
            )

        return filtered_platforms

    def filter_wargame_participants(self, include_participant=None):
        participant_platform_ids = [
            p.platform.platform_id for p in self.task_edit_widget.task_object.participants
        ]

        all_platforms = self.platforms
        filtered_platforms = {"ids": [], "values": []}
        for i in range(len(all_platforms["ids"])):
            if all_platforms["ids"][i] not in participant_platform_ids:
                filtered_platforms["ids"].append(all_platforms["ids"][i])
                filtered_platforms["values"].append(all_platforms["values"][i])

        if include_participant is not None:
            index = all_platforms["ids"].index(include_participant.platform.platform_id)
            filtered_platforms["ids"].insert(0, include_participant.platform.platform_id)
            filtered_platforms["values"].insert(0, all_platforms["values"][index])

        return filtered_platforms

    def handle_add_button(self):
        async def coroutine_wargame():
            ds = self.task_edit_widget.data_store

            with ds.session_scope():
                self.task_edit_widget.task_object = ds.session.merge(
                    self.task_edit_widget.task_object
                )
                ds.session.refresh(self.task_edit_widget.task_object)
                filtered_platforms = self.filter_wargame_participants()

            dialog = WargameParticipantDialog(
                self.task_edit_widget.task_object,
                filtered_platforms,
                self.task_edit_widget.privacies,
            )
            result = await self.task_edit_widget.show_dialog_as_float(dialog)
            if result is None:
                return

            ds = self.task_edit_widget.data_store

            with ds.session_scope():
                change_id = ds.add_to_changes(
                    USER, datetime.utcnow(), "Manual edit in Tasks GUI"
                ).change_id

                self.task_edit_widget.task_object.add_participant(
                    ds, result["platform"], result["privacy"], change_id
                )

            self.task_edit_widget.update_tree_object_handler()

        async def coroutine_serial():
            ds = self.task_edit_widget.data_store

            with ds.session_scope():
                self.task_edit_widget.task_object = ds.session.merge(
                    self.task_edit_widget.task_object
                )
                ds.session.refresh(self.task_edit_widget.task_object)

                filtered_platforms = self.filter_serial_participants()

            dialog = SerialParticipantDialog(
                self.task_edit_widget.task_object,
                self.force,
                filtered_platforms,
                self.task_edit_widget.privacies,
            )
            result = await self.task_edit_widget.show_dialog_as_float(dialog)
            if result is None:
                return

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

            self.task_edit_widget.update_tree_object_handler()

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

    def handle_edit_button(self):
        async def coroutine_serial():
            ds = self.task_edit_widget.data_store
            participant = self.participants[self.combo_box.selected_entry]

            with ds.session_scope():
                change_id = ds.add_to_changes(
                    USER, datetime.utcnow(), "Manual edit from Tasks GUI"
                ).change_id
                self.task_edit_widget.task_object = ds.session.merge(
                    self.task_edit_widget.task_object
                )
                ds.session.refresh(self.task_edit_widget.task_object)

                filtered_platforms = self.filter_serial_participants(
                    include_participant=participant
                )

            dialog = SerialParticipantDialog(
                self.task_edit_widget.task_object,
                self.force,
                filtered_platforms,
                self.task_edit_widget.privacies,
                object_to_edit=participant,
            )
            result = await self.task_edit_widget.show_dialog_as_float(dialog)
            if result is None:
                return

            participant = ds.session.merge(participant)

            # This set of if statements checks each field to see if it has been changed
            # and if it has been changed then it updates the fields and adds a log entry
            # for the change
            if participant.wargame_participant_id != result["platform"]:
                ds.add_to_logs(
                    table=constants.SERIAL_PARTICIPANT,
                    row_id=participant.serial_participant_id,
                    field="wargame_participant_id",
                    previous_value=str(participant.wargame_participant_id),
                    change_id=change_id,
                )
                wgp = (
                    ds.session.query(ds.db_classes.WargameParticipant)
                    .filter(
                        ds.db_classes.WargameParticipant.wargame_participant_id
                        == result["platform"]
                    )
                    .one()
                )
                participant.wargame_participant = wgp

            if participant.start != result["start"]:
                ds.add_to_logs(
                    table=constants.SERIAL_PARTICIPANT,
                    row_id=participant.serial_participant_id,
                    field="start",
                    previous_value=str(participant.start),
                    change_id=change_id,
                )
                participant.start = result["start"]

            if participant.end != result["end"]:
                ds.add_to_logs(
                    table=constants.SERIAL_PARTICIPANT,
                    row_id=participant.serial_participant_id,
                    field="end",
                    previous_value=str(participant.end),
                    change_id=change_id,
                )

                participant.end = result["end"]

            if participant.privacy_name != result["privacy"]:
                ds.add_to_logs(
                    table=constants.SERIAL_PARTICIPANT,
                    row_id=participant.serial_participant_id,
                    field="privacy_id",
                    previous_value=str(participant.privacy_id),
                    change_id=change_id,
                )
                privacy = ds.search_privacy(result["privacy"])
                if privacy is None:
                    raise ValueError("Specified Privacy does not exist")
                participant.privacy_id = privacy.privacy_id

            # Actually commit the changes to the participant to the database
            with ds.session_scope():
                ds.session.flush()
                self.task_edit_widget.task_object = ds.session.merge(
                    self.task_edit_widget.task_object
                )
                # Merging an object into the session should refresh all of the fields,
                # but we seem to need to do an explicit refresh here - not entirely sure why
                ds.session.refresh(self.task_edit_widget.task_object)
                ds.session.expunge_all()

            self.task_edit_widget.update_tree_object_handler()

        async def coroutine_wargame():
            ds = self.task_edit_widget.data_store
            participant = self.participants[self.combo_box.selected_entry]

            with ds.session_scope():
                change_id = ds.add_to_changes(
                    USER, datetime.utcnow(), "Manual edit from Tasks GUI"
                ).change_id
                self.task_edit_widget.task_object = ds.session.merge(
                    self.task_edit_widget.task_object
                )
                ds.session.refresh(self.task_edit_widget.task_object)

                filtered_platforms = self.filter_wargame_participants(
                    include_participant=participant
                )

            dialog = WargameParticipantDialog(
                self.task_edit_widget.task_object,
                filtered_platforms,
                self.task_edit_widget.privacies,
                object_to_edit=participant,
            )

            result = await self.task_edit_widget.show_dialog_as_float(dialog)
            if result is None:
                return

            participant = ds.session.merge(participant)

            ds = self.task_edit_widget.data_store

            if participant.platform_id != result["platform"]:
                ds.add_to_logs(
                    table=constants.SERIAL_PARTICIPANT,
                    row_id=participant.wargame_participant_id,
                    field="platform_id",
                    previous_value=str(participant.platform_id),
                    change_id=change_id,
                )
                platform = (
                    ds.session.query(ds.db_classes.Platform)
                    .filter(ds.db_classes.Platform.platform_id == result["platform"])
                    .one()
                )
                participant.platform = platform

            if participant.privacy_name != result["privacy"]:
                ds.add_to_logs(
                    table=constants.SERIAL_PARTICIPANT,
                    row_id=participant.wargame_participant_id,
                    field="privacy_id",
                    previous_value=str(participant.privacy_id),
                    change_id=change_id,
                )
                privacy = ds.search_privacy(result["privacy"])
                if privacy is None:
                    raise ValueError("Specified Privacy does not exist")
                participant.privacy_id = privacy.privacy_id

            # Actually commit the changes to the participant to the database
            with ds.session_scope():
                ds.session.flush()
                self.task_edit_widget.task_object = ds.session.merge(
                    self.task_edit_widget.task_object
                )
                # Merging an object into the session should refresh all of the fields,
                # but we seem to need to do an explicit refresh here - not entirely sure why
                ds.session.refresh(self.task_edit_widget.task_object)
                ds.session.expunge_all()

            self.task_edit_widget.update_tree_object_handler()

        if not self.item_selected_in_combo_box():
            return

        if isinstance(
            self.task_edit_widget.task_object, self.task_edit_widget.data_store.db_classes.Wargame
        ):
            ensure_future(coroutine_wargame())
        elif isinstance(
            self.task_edit_widget.task_object, self.task_edit_widget.data_store.db_classes.Serial
        ):
            ensure_future(coroutine_serial())
        get_app().invalidate()

    def handle_delete_button(self):
        if not self.item_selected_in_combo_box():
            return

        ds = self.task_edit_widget.data_store
        participant = self.participants[self.combo_box.selected_entry]

        change_id = ds.add_to_changes(
            USER, datetime.utcnow(), "Manual delete from Tasks GUI"
        ).change_id

        with ds.session_scope():
            ds.delete_objects(
                participant.__tablename__,
                [getattr(participant, get_primary_key_for_table(participant))],
                change_id=change_id,
            )

            self.task_edit_widget.task_object = ds.session.merge(self.task_edit_widget.task_object)
            
            ds.session.refresh(self.task_edit_widget.task_object)
            self.task_edit_widget.task_object = load_participants_attribute(ds, self.task_edit_widget.task_object)
            logger.debug(self.task_edit_widget.task_object.participants)
            ds.session.expunge_all()

        new_selected_entry = self.combo_box.selected_entry - 1
        if new_selected_entry < 0:
            new_selected_entry = 0
        self.combo_box.selected_entry = new_selected_entry

        self.task_edit_widget.update_tree_object_handler()
        get_app().invalidate()

    def handle_switch_button(self):
        if not self.item_selected_in_combo_box():
            return

        ds = self.task_edit_widget.data_store
        participant = self.participants[self.combo_box.selected_entry]

        prev_force_type_id = participant.force_type_id

        if participant.force_type_name == "Blue":
            new_force_type = ds.search_force_type("Red")
        else:
            new_force_type = ds.search_force_type("Blue")

        participant.force_type = new_force_type

        with ds.session_scope():
            participant = ds.session.merge(participant)

            change_id = ds.add_to_changes(
                USER, datetime.utcnow(), "Manual switch of participant force from Tasks GUI"
            ).change_id

            ds.add_to_logs(
                table=constants.SERIAL_PARTICIPANT,
                row_id=participant.serial_participant_id,
                field="force_type_id",
                previous_value=str(prev_force_type_id),
                change_id=change_id,
            )

        self.task_edit_widget.update_tree_object_handler()

    def item_selected_in_combo_box(self):
        if len(self.combo_box.filtered_entries) == 0:
            return False
        else:
            return True

    def get_widgets(self):
        if self.force is not None:
            buttons = [self.add_button, self.edit_button, self.delete_button, self.switch_button]
        else:
            buttons = [self.add_button, self.edit_button, self.delete_button]

        return HSplit([self.combo_box, VSplit(buttons)])

    def __pt_container__(self):
        return self.container
