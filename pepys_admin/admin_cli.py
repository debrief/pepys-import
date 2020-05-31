import cmd
import os
import sys
from datetime import datetime

from alembic import command
from alembic.config import Config
from iterfzf import iterfzf
from prompt_toolkit import prompt as ptk_prompt
from prompt_toolkit.completion.filesystem import PathCompleter

from paths import ROOT_DIRECTORY
from pepys_admin.export_by_platform_cli import ExportByPlatformNameShell
from pepys_admin.export_snapshot import export_metadata_tables, export_reference_tables
from pepys_admin.initialise_cli import InitialiseShell
from pepys_admin.utils import get_default_export_folder
from pepys_admin.view_data_cli import ViewDataShell
from pepys_import.core.store.data_store import DataStore
from pepys_import.core.store.db_status import TableTypes
from pepys_import.utils.data_store_utils import is_schema_created

DIR_PATH = os.path.dirname(os.path.abspath(__file__))


class AdminShell(cmd.Cmd):
    intro = """--- Menu ---
(1) Initialise/Clear
(2) Status
(3) Export
(4) Export by Platform and sensor
(5) Migrate
(6) View Data
(7) Export Reference Data
(8) Export Reference and Metadata Data
(0) Exit
"""
    prompt = "(pepys-admin) "

    def __init__(self, data_store, csv_path=DIR_PATH):
        super(AdminShell, self).__init__()
        self.data_store = data_store
        self.csv_path = csv_path
        self.aliases = {
            "0": self.do_exit,
            "1": self.do_initialise,
            "2": self.do_status,
            "3": self.do_export,
            "4": self.do_export_by_platform_name,
            "5": self.do_migrate,
            "6": self.do_view_data,
            "7": self.do_export_reference_data,
            "8": self.do_export_reference_and_metadata_data,
            "9": self.do_export_all,
        }

        self.cfg = Config(os.path.join(ROOT_DIRECTORY, "alembic.ini"))
        script_location = os.path.join(ROOT_DIRECTORY, "migrations")
        self.cfg.set_main_option("script_location", script_location)
        self.cfg.attributes["db_type"] = data_store.db_type
        self.cfg.attributes["connection"] = data_store.engine

    def do_export(self):
        """Start the export process"""
        if is_schema_created(self.data_store.engine, self.data_store.db_type) is False:
            return

        with self.data_store.session_scope():
            datafiles = self.data_store.get_all_datafiles()
            if not datafiles:
                print("There is no datafile found in the database!")
                return
            datafiles_dict = {d.reference: d.datafile_id for d in datafiles}
        selected_datafile = iterfzf(datafiles_dict.keys())

        if selected_datafile is None or selected_datafile not in datafiles_dict.keys():
            print(f"You haven't selected a valid option!")
            return

        export_flag = input(f"Do you want to export {selected_datafile}? (Y/n)\n")
        if export_flag in ["", "Y", "y"]:
            folder_completer = PathCompleter(only_directories=True, expanduser=True)
            folder_path = ptk_prompt(
                "Please provide a folder path for the exported file: ",
                default=get_default_export_folder(),
                completer=folder_completer,
                complete_while_typing=True,
            )

            datafile_name = f"exported_{selected_datafile.replace('.', '_')}.rep"
            print(f"'{selected_datafile}' is going to be exported.")
            selected_datafile_id = datafiles_dict[selected_datafile]

            export_file_full_path = os.path.expanduser(os.path.join(folder_path, datafile_name))

            with self.data_store.session_scope():
                self.data_store.export_datafile(selected_datafile_id, export_file_full_path)
            print(f"Datafile successfully exported to {export_file_full_path}.")
        elif export_flag in ["N", "n"]:
            print("You selected not to export!")
        else:
            print(f"Please enter a valid input.")

    def do_export_by_platform_name(self):
        if is_schema_created(self.data_store.engine, self.data_store.db_type) is False:
            return

        Sensor = self.data_store.db_classes.Sensor
        with self.data_store.session_scope():
            platforms = self.data_store.session.query(self.data_store.db_classes.Platform).all()
            if not platforms:
                print("There is no platform found in the database!")
                return
            platforms_dict = {p.name: p.platform_id for p in platforms}
        selected_platform = iterfzf(platforms_dict.keys())

        if selected_platform is None or selected_platform not in platforms_dict.keys():
            print(f"You haven't selected a valid option!")
            return

        # Find related sensors to the selected platform
        platform_id = platforms_dict[selected_platform]
        sensors = self.data_store.session.query(Sensor).filter(Sensor.host == platform_id).all()
        sensors_dict = {s.name: s.sensor_id for s in sorted(sensors, key=lambda x: x.name)}
        with self.data_store.session_scope():
            objects = self.data_store.find_related_datafile_objects(platform_id, sensors_dict)
        # Create a dynamic menu for the found datafile objects
        text = "--- Menu ---\n"
        options = [
            "0",
        ]
        for index, obj in enumerate(objects, 1):
            text += f"({index}) {obj['name']} {obj['filename']} {obj['min']}-{obj['max']}\n"
            options.append(str(index))
        text += "(0) Cancel\n"
        # Initialise a new menu
        export_platform = ExportByPlatformNameShell(self.data_store, options, objects)
        export_platform.cmdloop(intro=text)

    def do_export_all(self):
        """Start the export all datafiles process"""
        if is_schema_created(self.data_store.engine, self.data_store.db_type) is False:
            return
        export_flag = input("Do you want to export all Datafiles. (Y/n)\n")
        if export_flag in ["", "Y", "y"]:
            while True:
                folder_name = input(
                    "Please provide folder name (Press Enter for auto generated folder):"
                )
                if folder_name:
                    if os.path.isdir(folder_name):
                        print(f"{folder_name} already exists.")
                    else:
                        os.mkdir(folder_name)
                        break
                else:
                    folder_name = datetime.utcnow().strftime("exported_datafiles_%Y%m%d_%H%M%S")
                    os.mkdir(folder_name)
                    break

            print(f"Datafiles are going to be exported to '{folder_name}' folder.")
            with self.data_store.session_scope():
                datafiles = self.data_store.get_all_datafiles()
                if not datafiles:
                    print("There is no datafile found in the database!")
                    return
                for datafile in datafiles:
                    datafile_name = f"exported_{datafile.reference.replace('.', '_')}.rep"
                    print(f"'{datafile_name}' is going to be exported.")
                    datafile_filename = os.path.join(folder_name, datafile_name)
                    datafile_id = datafile.datafile_id
                    self.data_store.export_datafile(datafile_id, datafile_filename)
                    print(f"Datafile successfully exported to {datafile_name}.")
            print("All datafiles are successfully exported!")
        elif export_flag in ["N", "n"]:
            print("You selected not to export!")
        else:
            print(f"Please enter a valid input.")

    def do_initialise(self):
        """Allow the currently connected database to be configured"""
        print("-" * 61)
        initialise = InitialiseShell(self.data_store, self, self.csv_path)
        initialise.cmdloop()

    def do_status(self):
        """Report on the database contents"""
        if is_schema_created(self.data_store.engine, self.data_store.db_type) is False:
            return

        with self.data_store.session_scope():
            measurement_summary = self.data_store.get_status(report_measurement=True)
            report = measurement_summary.report()
            print(f"## Measurements\n{report}\n")

            metadata_summary = self.data_store.get_status(report_metadata=True)
            report = metadata_summary.report()
            print(f"## Metadata\n{report}\n")

            reference_summary = self.data_store.get_status(report_reference=True)
            report = reference_summary.report()
            print(f"## Reference\n{report}\n")

        print(f"## Database Version")
        command.current(self.cfg, verbose=True)

    def do_migrate(self):
        print("Alembic migration command running, see output below.")
        command.upgrade(self.cfg, "head")

    def do_view_data(self):
        if is_schema_created(self.data_store.engine, self.data_store.db_type) is False:
            return
        print("-" * 61)
        shell = ViewDataShell(self.data_store)
        shell.cmdloop()

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

    def do_export_reference_and_metadata_data(self):
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
        selected_privacies = iterfzf(privacy_dict.keys(), multi=True)
        privacy_ids = [privacy_dict[name] for name in selected_privacies]
        export_metadata_tables(self.data_store, destination_store, privacy_ids)
        print(
            f"Reference and metadata tables are successfully exported!\nYou can find it here: '{path}'."
        )

    @staticmethod
    def do_exit():
        """Exit the application"""
        print("Thank you for using Pepys Admin")
        sys.exit()

    def default(self, line):
        command_, arg, line = self.parseline(line)
        if command_ in self.aliases:
            self.aliases[command_]()
        else:
            print(f"*** Unknown syntax: {line}")

    def postcmd(self, stop, line):
        if line != "0":
            print("-" * 61)
            print(self.intro)
        return cmd.Cmd.postcmd(self, stop, line)
