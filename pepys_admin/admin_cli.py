# TODO: we have to keep these statements on top to load pepys_import.
# We will see better approach to access modules inside the other module.
import sys
import datetime

sys.path.append(".")

import argparse  # noqa: E402
import cmd  # noqa: E402
from iterfzf import iterfzf  # noqa: E402
import os  # noqa: E402

from config import DB_USERNAME, DB_PASSWORD, DB_HOST, DB_NAME, DB_PORT, DB_TYPE
from pepys_import.core.store.data_store import DataStore  # noqa: E402

dirpath = os.path.dirname(os.path.abspath(__file__))


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

    def __init__(self, datastore, parentShell, csv_path):
        super(InitialiseShell, self).__init__()
        self.datastore = datastore
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

        if parentShell:
            self.prompt = parentShell.prompt.strip() + "/" + self.prompt

    def do_cleardb_contents(self, args):
        self.datastore.clear_db_contents()
        print("Cleared database contents")

    def do_cleardb_schema(self, args):
        self.datastore.clear_db_schema()
        print("Cleared database schema")

    def do_create_pepys_schema(self, args):
        self.datastore.initialise()
        print("Initialised database")

    def do_import_reference_data(self, args):
        with self.datastore.session_scope():
            self.datastore.populate_reference(self.csv_path)
        print("Reference data imported")

    def do_import_metadata(self, args):
        with self.datastore.session_scope():
            self.datastore.populate_metadata(self.csv_path)
        print("Metadata imported")

    def do_import_sample_measurements(self, args):
        with self.datastore.session_scope():
            self.datastore.populate_measurement(self.csv_path)
        print("Sample measurements imported")

    def do_cancel(self, *args):
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

    def __init__(self, datastore, csv_path=dirpath):
        super(AdminShell, self).__init__()
        self.datastore = datastore
        self.csv_path = csv_path
        self.aliases = {
            "0": self.do_exit,
            "1": self.do_export,
            "2": self.do_initialise,
            "3": self.do_status,
            "9": self.do_export_all,
        }

    def do_export(self, arg):
        "Start the export process"
        with self.datastore.session_scope():
            datafiles = self.datastore.get_all_datafiles()
            datafiles_dict = {}
            for datafile in datafiles:
                datafiles_dict[datafile.reference] = datafile.datafile_id
        datafile_references = datafiles_dict.keys()
        datafile_reference = iterfzf(datafile_references)

        if datafile_reference is None:
            return

        export_flag = input(
            "Do you want to export {} Datafile. (Y/n)\n".format(datafile_reference)
        )
        if export_flag in ["", "Y", "y"]:
            datafilename = datafile_reference.replace(".", "_")
            print("Exported Datafile is: {}.rep.".format(datafilename))

            selected_datafile_id = datafiles_dict[datafile_reference]
            with self.datastore.session_scope():
                self.datastore.export_datafile(selected_datafile_id, datafilename)

    def do_export_all(self, arg):
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

            print(
                "Datafiles are going to be exported in '{}' folder.".format(folder_name)
            )

            with self.datastore.session_scope():
                datafiles = self.datastore.get_all_datafiles()
                for datafile in datafiles:
                    datafile_id = datafile.datafile_id
                    datafile_filename = os.path.join(
                        folder_name, datafile.reference.replace(".", "_")
                    )
                    self.datastore.export_datafile(datafile_id, datafile_filename)

    def do_initialise(self, arg):
        "Allow the currently connected database to be configured"
        initialise = InitialiseShell(self.datastore, self, self.csv_path)
        initialise.cmdloop()

    def do_status(self, arg):
        "Report on the database contents"
        with self.datastore.session_scope():
            measurement_summary = self.datastore.get_status(report_measurement=True)
            report = measurement_summary.report()
            print("## Measurements")
            print(report)
            print("\n")

            metadata_summary = self.datastore.get_status(report_metadata=True)
            report = metadata_summary.report()
            print("## Metadata")
            print(report)
            print("\n")

            reference_summary = self.datastore.get_status(report_reference=True)
            report = reference_summary.report()
            print("## Reference")
            print(report)
            print("\n")

    def do_exit(self, arg):
        "Exit the application"
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


if __name__ == "__main__":
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
