import argparse
import cmd, sys
from iterfzf import iterfzf

sys.path.append(".")

from pepys_import.core.store.data_store import DataStore


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


class AdminShell(cmd.Cmd):
    intro = "Welcome to the Pepys Admin shell.   Type help or ? to list commands.\n"
    prompt = "(pepys-admin) "
    file = None

    def __init__(self, datastore):
        super(AdminShell, self).__init__()
        self.datastore = datastore
        self.aliases = {"0": self.do_exit, "1": self.do_export, "2": self.do_status}

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
        print(selected_datafile)
        with self.datastore.session_scope():
            self.datastore.export_datafile(selected_datafile)

    def do_status(self, arg):
        "Report on the database contents"
        print("status")

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
        intro = "--- Menu --- \n (1) Export\n (2) Status\n (0) Exit\n"
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

    intro = "Welcome to the Pepys Admin shell.\n --- Menu --- \n (1) Export\n (2) Status\n (0) Exit\n"
    admin = AdminShell(datastore).cmdloop(intro=intro)
