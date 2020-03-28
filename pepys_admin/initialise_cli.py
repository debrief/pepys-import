import cmd
import os

DIR_PATH = os.path.dirname(os.path.abspath(__file__))


class InitialiseShell(cmd.Cmd):
    intro = """--- Menu ---
(1) Clear database contents
(2) Clear database schema
(3) Create Pepys schema
(4) Import Reference data
(5) Import Metadata
(6) Import Sample Measurements
(0) Exit
"""
    prompt = "(initialise) "

    def __init__(self, data_store, parent_shell, csv_path):
        super(InitialiseShell, self).__init__()
        self.data_store = data_store
        self.csv_path = csv_path
        self.aliases = {
            "0": self.do_cancel,
            "1": self.do_clear_db_contents,
            "2": self.do_clear_db_schema,
            "3": self.do_create_pepys_schema,
            "4": self.do_import_reference_data,
            "5": self.do_import_metadata,
            "6": self.do_import_sample_measurements,
        }

        if parent_shell:
            self.prompt = parent_shell.prompt.strip() + "/" + self.prompt

    def do_clear_db_contents(self):
        if self.data_store.is_schema_created() is False:
            return

        self.data_store.clear_db_contents()
        print("Cleared database contents")

    def do_clear_db_schema(self):
        if self.data_store.is_schema_created() is False:
            return

        self.data_store.clear_db_schema()
        print("Cleared database schema")

    def do_create_pepys_schema(self):
        self.data_store.initialise()
        print("Initialised database")

    def do_import_reference_data(self):
        if self.data_store.is_schema_created() is False:
            return

        with self.data_store.session_scope():
            self.data_store.populate_reference(self.csv_path)
        print("Reference data imported")

    def do_import_metadata(self):
        if self.data_store.is_schema_created() is False:
            return

        with self.data_store.session_scope():
            self.data_store.populate_metadata(self.csv_path)
        print("Metadata imported")

    def do_import_sample_measurements(self):
        if self.data_store.is_schema_created() is False:
            return

        with self.data_store.session_scope():
            self.data_store.populate_measurement(self.csv_path)
        print("Sample measurements imported")

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
