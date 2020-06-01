import cmd
import os

from iterfzf import iterfzf

from pepys_admin.snapshot_helpers import export_metadata_tables, export_reference_tables
from pepys_import.core.store.data_store import DataStore
from pepys_import.core.store.db_status import TableTypes
from pepys_import.utils.data_store_utils import is_schema_created


class SnapshotShell(cmd.Cmd):
    intro = """--- Menu ---
    (1) Create snapshot with Reference data
    (2) Create snapshot with Reference data & Metadata
    (0) Back
    """
    prompt = "(pepys-admin) (snapshot) "

    def __init__(self, data_store):
        super(SnapshotShell, self).__init__()
        self.data_store = data_store
        self.aliases = {
            "0": self.do_cancel,
            "1": self.do_export_reference_data,
            "2": self.do_export_reference_data_and_metadata,
        }

    @staticmethod
    def _ask_for_db_name():
        while True:
            destination_db_name = input("SQLite database file to use: ")
            path = os.path.join(os.getcwd(), destination_db_name)
            if not os.path.exists(path):
                break
            else:
                print(
                    f"There is already a file named '{destination_db_name}' in '{os.getcwd()}'."
                    f"\nPlease enter another name."
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
        if is_schema_created(self.data_store.engine, self.data_store.db_type) is False:
            return

        destination_store, path = self._create_destination_store()
        reference_table_objects = self.data_store.meta_classes[TableTypes.REFERENCE]
        export_reference_tables(self.data_store, destination_store, reference_table_objects)
        print(f"Reference tables are successfully exported!\nYou can find it here: '{path}'.")

    def do_export_reference_data_and_metadata(self):
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
            f"Reference and metadata tables are successfully exported!\nYou can find it here: '{path}'."
        )

    @staticmethod
    def do_cancel():
        print("Returning to the previous menu...")

    def default(self, line):
        cmd_, arg, line = self.parseline(line)
        if cmd_ in self.aliases:
            self.aliases[cmd_]()
            if cmd_ == "0":
                return True
        else:
            print(f"*** Unknown syntax: {line}")

    def postcmd(self, stop, line):
        if line != "0":
            print("-" * 61)
            print(self.intro)
        return cmd.Cmd.postcmd(self, stop, line)
