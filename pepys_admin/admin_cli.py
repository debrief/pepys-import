from pepys_import.core.store.data_store import DataStore

import argparse
import cmd
import sys
from iterfzf import iterfzf
import os

sys.path.append(".")


dirpath = os.path.dirname(os.path.abspath(__file__))


def postgres_initialise():
    """Test whether schemas created successfully on PostgresSQL"""
    data_store_postgres = DataStore(
        db_username="postgres",
        db_password="postgres",
        db_host="localhost",
        db_port=5432,
        db_name="pepys",
        welcome_text="Pepys_Admin",
    )
    return data_store_postgres


def sqlite_initialise():
    """Test whether schemas created successfully on PostgresSQL"""
    print("SQLITE")


class InitialiseShell(cmd.Cmd):
    prompt = "(initialise) "

    def __init__(self, datastore):
        super(InitialiseShell, self).__init__()
        self.datastore = datastore
        self.aliases = {
            "0": self.do_cancel,
            "1": self.do_cleardb,
            "2": self.do_create_pepys_schema,
            "3": self.do_import_reference_data,
            "4": self.do_import_metadata,
            "5": self.do_import_sample_measurements,
        }

    def do_cleardb(self, args):
        pass

    def do_create_pepys_schema(self, args):
        self.datastore.initialise()

    def do_import_reference_data(self, args):
        self.datastore.populate_reference(dirpath)

    def do_import_metadata(self, args):
        self.datastore.populate_metadata(dirpath)

    def do_import_sample_measurements(self, args):
        self.datastore.populate_measurement(dirpath)

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
        intro = "--- Menu --- \n (1) Clear database\n (2) Create Pepys schema\n "
        "(3) Import Reference data\n (4) Import Metadata\n "
        "(5) Import Sample Measurements\n (0) Exit\n"
        if line != "0":
            print(intro)
        return cmd.Cmd.postcmd(self, stop, line)


class AdminShell(cmd.Cmd):
    intro = "Welcome to the Pepys Admin shell.   Type help or ? to list commands.\n"
    prompt = "(pepys-admin) "
    file = None

    def __init__(self, datastore):
        super(AdminShell, self).__init__()
        self.datastore = datastore
        self.aliases = {
            "0": self.do_exit,
            "1": self.do_export,
            "2": self.do_initialise,
            "3": self.do_status,
        }

    def do_export(self, arg):
        "Start the export process"
        # datafile_name = input("Please enter Datafile name:")
        with self.datastore.session_scope():
            datafiles = self.datastore.get_all_datafiles()
            datafiles_dict = {}
            for datafile in datafiles:
                datafiles_dict[datafile.reference] = datafile.datafile_id
        datafile_references = list(datafiles_dict.keys())
        datafile_reference = iterfzf(datafile_references)

        if datafile_reference is None:
            return

        export_flag = input(
            "Do you want to export {} Datafile. (Y/n)\n".format(datafile_reference)
        )
        if export_flag in ["", "Y", "y"]:
            print("Exported Datafile is: {} TODO".format(datafile_reference))

        selected_datafile = datafiles_dict[datafile_reference]
        with self.datastore.session_scope():
            self.datastore.export_datafile(selected_datafile)

    def do_initialise(self, arg):
        "Allow the currently connected database to be configured"
        initialise = InitialiseShell(self.datastore)
        intro = "--- Menu --- \n (1) Clear database\n (2) Create Pepys schema\n"
        " (3) Import Reference data\n (4) Import Metadata\n "
        "(5) Import Sample Measurements\n (0) Exit\n"
        initialise.cmdloop(intro=intro)

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
        self.close()
        return True

    def close(self):
        if self.file:
            self.file.close()
            self.file = None

    def default(self, line):
        cmd, arg, line = self.parseline(line)
        if cmd in self.aliases:
            self.aliases[cmd](arg)
            if cmd == "0":
                self.close()
                return True
        else:
            print("*** Unknown syntax: %s" % line)

    def postcmd(self, stop, line):
        intro = "--- Menu --- \n (1) Export\n (2) Initialise\n (3) Status\n (0) Exit\n"
        if line != "0":
            print(intro)
        return cmd.Cmd.postcmd(self, stop, line)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DB Selection!")
    parser.add_argument("--db", type=str, help="Db Path")

    args = parser.parse_args()
    db_flag = args.db

    if db_flag:
        datastore = sqlite_initialise()
    else:
        datastore = postgres_initialise()

    intro = "Welcome to the Pepys Admin shell.\n --- Menu --- \n (1) Export\n "
    "(2) Initialise\n (3) Status\n (0) Exit\n"
    admin = AdminShell(datastore).cmdloop(intro=intro)
