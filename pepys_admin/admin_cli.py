import argparse
import cmd
import datetime
import os

from iterfzf import iterfzf

from config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_TYPE, DB_USERNAME
from pepys_import.core.store.data_store import DataStore

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
            "1": self.do_cleardb_contents,
            "2": self.do_cleardb_schema,
            "3": self.do_create_pepys_schema,
            "4": self.do_import_reference_data,
            "5": self.do_import_metadata,
            "6": self.do_import_sample_measurements,
        }

        if parent_shell:
            self.prompt = parent_shell.prompt.strip() + "/" + self.prompt

    def do_cleardb_contents(self):
        self.data_store.clear_db_contents()
        print("Cleared database contents")

    def do_cleardb_schema(self):
        self.data_store.clear_db_schema()
        print("Cleared database schema")

    def do_create_pepys_schema(self):
        self.data_store.initialise()
        print("Initialised database")

    def do_import_reference_data(self):
        with self.data_store.session_scope():
            self.data_store.populate_reference(self.csv_path)
        print("Reference data imported")

    def do_import_metadata(self):
        with self.data_store.session_scope():
            self.data_store.populate_metadata(self.csv_path)
        print("Metadata imported")

    def do_import_sample_measurements(self):
        with self.data_store.session_scope():
            self.data_store.populate_measurement(self.csv_path)
        print("Sample measurements imported")

    @staticmethod
    def do_cancel():
        return True

    do_EOF = do_cancel

    def default(self, line):
        cmd, arg, line = self.parseline(line)
        if cmd in self.aliases:
            self.aliases[cmd](arg)
            if cmd == "0":
                self.do_cancel()
                return True
        else:
            print("*** Unknown syntax: %s" % line)

    def postcmd(self, stop, line):
        if line != "0":
            print(self.intro)
        return cmd.Cmd.postcmd(self, stop, line)


class AdminShell(cmd.Cmd):
    intro = """--- Menu ---
(1) Export
(2) Initialise/Clear
(3) Status
(0) Exit
"""
    prompt = "(pepys-admin) "

    def __init__(self, data_store, csv_path=DIR_PATH):
        super(AdminShell, self).__init__()
        self.data_store = data_store
        self.csv_path = csv_path
        self.aliases = {
            "0": self.do_exit,
            "1": self.do_export,
            "2": self.do_initialise,
            "3": self.do_status,
            "9": self.do_export_all,
        }

    def do_export(self):
        "Start the export process"
        with self.data_store.session_scope():
            datafiles = self.data_store.get_all_datafiles()
            datafiles_dict = {}
            for datafile in datafiles:
                datafiles_dict[datafile.reference] = datafile.datafile_id
        datafile_references = datafiles_dict.keys()
        datafile_reference = iterfzf(datafile_references)

        if datafile_reference is None:
            return

        export_flag = input("Do you want to export {} Datafile. (Y/n)\n".format(datafile_reference))
        if export_flag in ["", "Y", "y"]:
            datafilename = datafile_reference.replace(".", "_")
            print("Exported Datafile is: {}.rep.".format(datafilename))

            selected_datafile_id = datafiles_dict[datafile_reference]
            with self.data_store.session_scope():
                self.data_store.export_datafile(selected_datafile_id, datafilename)

    def do_export_all(self):
        "Start the export all datafiles process"
        export_flag = input("Do you want to export all Datafiles. (Y/n)\n")
        if export_flag in ["", "Y", "y"]:
            while True:
                folder_name = input(
                    "Please provide folder name (Press Enter for auto generated folder):"
                )
                if folder_name:
                    if os.path.isdir(folder_name):
                        print("{} already exists.\n".format(folder_name))
                    else:
                        os.mkdir(folder_name)
                        break
                else:
                    folder_name = datetime.datetime.now().strftime(
                        "exported_datafiles_%Y%m%d_%H%M%S"
                    )
                    os.mkdir(folder_name)
                    break

            print("Datafiles are going to be exported in '{}' folder.".format(folder_name))

            with self.data_store.session_scope():
                datafiles = self.data_store.get_all_datafiles()
                for datafile in datafiles:
                    datafile_id = datafile.datafile_id
                    datafile_filename = os.path.join(
                        folder_name, datafile.reference.replace(".", "_")
                    )
                    self.data_store.export_datafile(datafile_id, datafile_filename)

    def do_initialise(self):
        "Allow the currently connected database to be configured"
        initialise = InitialiseShell(self.data_store, self, self.csv_path)
        initialise.cmdloop()

    def do_status(self):
        "Report on the database contents"
        with self.data_store.session_scope():
            measurement_summary = self.data_store.get_status(report_measurement=True)
            report = measurement_summary.report()
            print("## Measurements")
            print(report)
            print("\n")

            metadata_summary = self.data_store.get_status(report_metadata=True)
            report = metadata_summary.report()
            print("## Metadata")
            print(report)
            print("\n")

            reference_summary = self.data_store.get_status(report_reference=True)
            report = reference_summary.report()
            print("## Reference")
            print(report)
            print("\n")

    @staticmethod
    def do_exit():
        """Exit the application"""
        print("Thank you for using Pepys Admin")
        return True

    def default(self, line):
        cmd, arg, line = self.parseline(line)
        if cmd in self.aliases:
            self.aliases[cmd](arg)
            if cmd == "0":
                return True
        else:
            print("*** Unknown syntax: %s" % line)

    def postcmd(self, stop, line):
        if line != "0":
            print(self.intro)
        return cmd.Cmd.postcmd(self, stop, line)


def main():
    parser = argparse.ArgumentParser(description="Pepys Admin CLI")
    parser.add_argument("--path", type=str, help="CSV files path")
    args = parser.parse_args()

    data_store = DataStore(
        db_username=DB_USERNAME,
        db_password=DB_PASSWORD,
        db_host=DB_HOST,
        db_port=DB_PORT,
        db_name=DB_NAME,
        db_type=DB_TYPE,
    )

    AdminShell(data_store, args.path).cmdloop()


if __name__ == "__main__":
    main()
