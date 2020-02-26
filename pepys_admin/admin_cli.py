# TODO: we have to keep these statements on top to load pepys_import.
# We will see better approach to access modules inside the other module.
import sys

sys.path.append(".")

import argparse
import cmd
from iterfzf import iterfzf
import os
from pepys_import.core.store.data_store import DataStore

dirpath = os.path.dirname(os.path.abspath(__file__))


def create_postgres_data_store():
    """
    Create configured PostgresSQL data store.
    
    :return: Postgres data store
    :rtype: DataStore 
    """
    return DataStore(
        db_username="postgres",
        db_password="postgres",
        db_host="localhost",
        db_port=5432,
        db_name="pepys",
        welcome_text="Pepys_Admin",
    )


def create_sqlite_data_store(file):
    """
    Create and Initialise SQLite data store at provided location (file).
    
    :param file:  absolute/relative file path
    :type file: String
    
    :return:  Created Datafile entity
    :rtype: Datafile
    """
    store = DataStore("", "", "", 0, file, db_type="sqlite")
    if not os.path.isfile(file):
        store.initialise()
    return store


class InitialiseShell(cmd.Cmd):
    intro = (
        "\n--- Menu --- \n (1) Clear database\n (2) Create Pepys schema\n"
        " (3) Import Reference data\n (4) Import Metadata\n "
        "(5) Import Sample Measurements\n (0) Exit\n"
    )
    prompt = "(initialise) "

    def __init__(self, datastore, parentShell):
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

        if parentShell:
            self.prompt = parentShell.prompt.strip() + "/" + self.prompt

    def do_cleardb(self, args):
        self.datastore.clear_db()

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
        if line != "0":
            print(self.intro)
        return cmd.Cmd.postcmd(self, stop, line)


class AdminShell(cmd.Cmd):
    intro = "\n--- Menu --- \n (1) Export\n " "(2) Initialise\n (3) Status\n (0) Exit\n"
    prompt = "(pepys-admin) "

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
            print("Exported Datafile is: {}.".format(datafile_reference))

        selected_datafile_id = datafiles_dict[datafile_reference]
        with self.datastore.session_scope():
            self.datastore.export_datafile(selected_datafile_id)

    def do_initialise(self, arg):
        "Allow the currently connected database to be configured"
        initialise = InitialiseShell(self.datastore, self)
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
        if line != "0":
            print(self.intro)
        return cmd.Cmd.postcmd(self, stop, line)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SQLite file path!")
    parser.add_argument("--db", type=str, help="Db Path")

    args = parser.parse_args()
    db_file = args.db

    if db_file:
        datastore = create_sqlite_data_store(db_file)
    else:
        datastore = create_postgres_data_store()

    AdminShell(datastore).cmdloop()
