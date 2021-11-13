import os
import shutil
import tempfile

from iterfzf import iterfzf
from prompt_toolkit import prompt as ptk_prompt
from prompt_toolkit.completion import PathCompleter

from pepys_admin.base_cli import BaseShell
from pepys_admin.merge import MergeDatabases
from pepys_admin.snapshot_helpers import (
    _select_wargame,
    export_all_measurement_tables,
    export_measurement_tables_filtered_by_location,
    export_measurement_tables_filtered_by_serial_participation,
    export_measurement_tables_filtered_by_time,
    export_measurement_tables_filtered_by_wargame_participation,
    export_metadata_tables,
    export_reference_tables,
    get_number_from_user,
    get_time_from_user,
)
from pepys_admin.utils import database_at_latest_revision, get_default_export_folder
from pepys_import.core.store.data_store import DataStore
from pepys_import.core.store.db_status import TableTypes
from pepys_import.utils.data_store_utils import is_schema_created
from pepys_import.utils.text_formatting_utils import (
    custom_print_formatted_text,
    format_command,
    format_error_message,
)


class SnapshotShell(BaseShell):
    """Offers to create snapshot with Reference data and create snapshot with reference data & metadata."""

    choices = """(1) Create snapshot with Reference data
(2) Create snapshot with Reference data & Metadata
(3) Create snapshot with all data
(4) Create snapshot with all data, filtered by time
(5) Create snapshot with all data, filtered by location
(6) Create snapshot with all data, filtered by wargame
(7) Create snapshot with all data, filtered by serial
(8) Merge databases
(.) Back
"""
    prompt = "(pepys-admin) (snapshot) "

    def __init__(self, data_store):
        super(SnapshotShell, self).__init__()
        self.data_store = data_store
        self.aliases = {
            ".": self.do_cancel,
            "1": self.do_export_reference_data,
            "2": self.do_export_reference_data_and_metadata,
            "3": self.do_export_all_data,
            "4": self.do_export_all_data_filter_time,
            "5": self.do_export_all_data_filter_location,
            "6": self.do_export_all_data_filter_wargame_participation,
            "7": self.do_export_all_data_filter_serial_participation,
            "8": self.do_merge_databases,
        }

    @staticmethod
    def _ask_for_db_name():
        while True:
            destination_db_name = ptk_prompt(format_command("SQLite database file to use: "))
            path = os.path.join(os.getcwd(), destination_db_name)
            if not os.path.exists(path):
                break
            else:
                custom_print_formatted_text(
                    format_error_message(
                        f"There is already a file named '{destination_db_name}' in '{os.getcwd()}'."
                        f"\nPlease enter another name."
                    )
                )
        return destination_db_name, path

    def _create_destination_store(self):
        destination_db_name, path = self._ask_for_db_name()
        destination_store = DataStore(
            "",
            "",
            "",
            0,
            db_name=destination_db_name,
            db_type="sqlite",
            show_status=False,
            welcome_text=None,
        )
        destination_store.initialise()
        return destination_store, path

    def do_export_reference_data(self):
        """Exports reference data."""
        if is_schema_created(self.data_store.engine, self.data_store.db_type) is False:
            return

        destination_store, path = self._create_destination_store()
        reference_table_objects = self.data_store.meta_classes[TableTypes.REFERENCE]
        export_reference_tables(self.data_store, destination_store, reference_table_objects)
        print(f"Reference tables successfully exported!\nYou can find it here: '{path}'.")

    def do_export_reference_data_and_metadata(self):
        """Exports reference data and metadata."""
        if is_schema_created(self.data_store.engine, self.data_store.db_type) is False:
            return

        destination_store, path = self._create_destination_store()
        reference_table_objects = self.data_store.meta_classes[TableTypes.REFERENCE]
        export_reference_tables(self.data_store, destination_store, reference_table_objects)

        with self.data_store.session_scope():
            privacies = self.data_store.session.query(
                self.data_store.db_classes.Privacy.privacy_id,
                self.data_store.db_classes.Privacy.name,
            ).all()
            privacy_dict = {name: privacy_id for privacy_id, name in privacies}
        message = (
            "Export all data with the selected classification(s). (Press TAB for multi-select) >"
        )
        selected_privacies = iterfzf(privacy_dict.keys(), multi=True, prompt=message)
        if selected_privacies is None:
            print("Returning to the previous menu")
            return
        privacy_ids = [privacy_dict[name] for name in selected_privacies]
        export_metadata_tables(self.data_store, destination_store, privacy_ids)
        print(
            f"Reference and metadata tables successfully exported!\nYou can find it here: '{path}'."
        )

    def _export_all_ref_and_metadata(self):
        if is_schema_created(self.data_store.engine, self.data_store.db_type) is False:
            print("Cannot export data from an empty database")
            return None, ""

        destination_store, path = self._create_destination_store()

        print("Exporting reference and metadata tables")
        # Export reference tables
        reference_table_objects = self.data_store.meta_classes[TableTypes.REFERENCE]
        export_reference_tables(self.data_store, destination_store, reference_table_objects)

        # Export metadata tables
        export_metadata_tables(self.data_store, destination_store)

        return destination_store, path

    def do_export_all_data(self):
        destination_store, path = self._export_all_ref_and_metadata()
        if destination_store is None:
            return

        export_all_measurement_tables(self.data_store, destination_store)
        print(f"Data successfully exported!\nYou can find it here: '{path}'.")

    def do_export_all_data_filter_time(self):
        start_time = get_time_from_user("Start time")
        end_time = get_time_from_user("End time")

        destination_store, path = self._export_all_ref_and_metadata()
        if destination_store is None:
            return

        export_measurement_tables_filtered_by_time(
            self.data_store, destination_store, start_time, end_time
        )
        print(f"Data successfully exported!\nYou can find it here: '{path}'.")

    def do_export_all_data_filter_location(self):
        ymin = get_number_from_user("Enter bottom latitude: ")
        ymax = get_number_from_user("Enter top latitude: ")
        xmin = get_number_from_user("Enter left longitude: ")
        xmax = get_number_from_user("Enter right longitude: ")

        destination_store, path = self._export_all_ref_and_metadata()
        if destination_store is None:
            return

        export_measurement_tables_filtered_by_location(
            self.data_store, destination_store, xmin, ymin, xmax, ymax
        )
        print(f"Data successfully exported!\nYou can find it here: '{path}'.")

    def do_export_all_data_filter_serial_participation(self):
        with self.data_store.session_scope():
            selected_wargame_id = _select_wargame(self.data_store)
            if selected_wargame_id is None:
                return

            results = (
                self.data_store.session.query(
                    self.data_store.db_classes.Serial.serial_number,
                    self.data_store.db_classes.Serial.serial_id,
                )
                .filter(self.data_store.db_classes.Serial.wargame_id == selected_wargame_id)
                .all()
            )
            serial_dict = dict(results)

            if len(serial_dict) == 0:
                print("No serials defined in selected wargame")
                return

            selected_serial_number = iterfzf(serial_dict.keys(), prompt="Select serial: ")
            selected_serial_id = serial_dict[selected_serial_number]

            selected_serial = (
                self.data_store.session.query(self.data_store.db_classes.Serial)
                .filter(self.data_store.db_classes.Serial.serial_id == selected_serial_id)
                .one()
            )

        destination_store, path = self._export_all_ref_and_metadata()
        if destination_store is None:
            return

        export_measurement_tables_filtered_by_serial_participation(
            self.data_store, destination_store, selected_serial
        )
        print(f"Data successfully exported!\nYou can find it here: '{path}'.")

    def do_export_all_data_filter_wargame_participation(self):
        with self.data_store.session_scope():
            selected_wargame_id = _select_wargame(self.data_store)

            if selected_wargame_id is None:
                return

            selected_wargame = (
                self.data_store.session.query(self.data_store.db_classes.Wargame)
                .filter(self.data_store.db_classes.Wargame.wargame_id == selected_wargame_id)
                .one()
            )

        destination_store, path = self._export_all_ref_and_metadata()
        if destination_store is None:
            return

        export_measurement_tables_filtered_by_wargame_participation(
            self.data_store, destination_store, selected_wargame
        )
        print(f"Data successfully exported!\nYou can find it here: '{path}'.")

    def do_merge_databases(self):
        file_completer = PathCompleter(expanduser=True)
        while True:
            slave_db_path = ptk_prompt(
                "Please enter the full path to the database file to be merged",
                default=get_default_export_folder(),
                completer=file_completer,
                complete_while_typing=True,
            )
            if os.path.exists(slave_db_path):
                break
            else:
                custom_print_formatted_text(
                    format_error_message("Invalid path entered, please try again")
                )

        # Check whether slave database is at latest revision
        if not database_at_latest_revision(slave_db_path):
            custom_print_formatted_text(
                format_error_message(
                    "The schema of the selected slave database is not at the latest revision. Before merging can go ahead "
                    "you must connect to this database with Pepys Admin and run the 'Migrate' option."
                )
            )
            return

        confirmation = ptk_prompt(
            format_command(
                f"Database to merge: {slave_db_path}\n"
                f"Merging a snapshot can introduce significant volumes of new data, are you sure you want to perform merge? (y/N)"
            )
        )
        if confirmation.lower() == "y":
            # Copy the SQLite db to a temporary location, as the merge function modifies the slave
            # and we don't want to modify the actual file the user provided
            temp_dir = tempfile.gettempdir()
            temp_slave_db_path = os.path.join(temp_dir, "PepysMergingSlaveDB.sqlite")
            shutil.copy2(slave_db_path, temp_slave_db_path)

            print("Starting merge")

            slave_store = DataStore(
                "", "", "", 0, db_name=temp_slave_db_path, db_type="sqlite", show_status=False
            )
            merge_class = MergeDatabases(self.data_store, slave_store)
            merge_class.merge_all_tables()

            # Delete the temporary DB
            os.remove(temp_slave_db_path)

            print("Merge completed")
        else:
            print("Ok, returning to previous menu")
            # Don't go ahead with merge unless we got "y"
            return

    @staticmethod
    def do_cancel():
        """Returns to the previous menu"""
        print("Returning to the previous menu...")
