import cmd
import os
from datetime import datetime

from iterfzf import iterfzf

from pepys_admin.initialise_cli import InitialiseShell

DIR_PATH = os.path.dirname(os.path.abspath(__file__))


class AdminShell(cmd.Cmd):
    intro = """--- Menu ---
(1) Export
(2) Export by Platform name and date
(3) Initialise/Clear
(4) Status
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
            "2": self.do_export_by_platform_name,
            "3": self.do_initialise,
            "4": self.do_status,
            "9": self.do_export_all,
        }

    def do_export(self):
        """Start the export process"""
        if self.data_store.is_schema_created() is False:
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
            datafile_name = f"exported_{selected_datafile.replace('.', '_')}.rep"
            print(f"'{selected_datafile}' is going to be exported.")

            selected_datafile_id = datafiles_dict[selected_datafile]
            with self.data_store.session_scope():
                self.data_store.export_datafile(selected_datafile_id, datafile_name)
            print(f"Datafile successfully exported to {datafile_name}.")
        elif export_flag in ["N", "n"]:
            print("You selected not to export!")
        else:
            print(f"Please enter a valid input.")

    def do_export_by_platform_name(self):
        if self.data_store.is_schema_created() is False:
            return

        Sensor = self.data_store.db_classes.Sensor
        with self.data_store.session_scope():
            platforms = self.data_store.session.query(self.data_store.db_classes.Platform).all()
            if not platforms:
                print("There is no datafile found in the database!")
                return
            platforms_dict = {p.name: p.platform_id for p in platforms}
        selected_platform = iterfzf(platforms_dict.keys())

        if selected_platform is None or selected_platform not in platforms_dict.keys():
            print(f"You haven't selected a valid option!")
            return

        # Find related sensors to the selected platform
        platform_id = platforms_dict[selected_platform]
        sensors = self.data_store.session.query(Sensor).filter(Sensor.host == platform_id).all()
        sensors_dict = {s.name: s.sensor_id for s in sensors}
        with self.data_store.session_scope():
            objects = self.data_store.find_related_datafile_objects(platform_id, sensors_dict)
        print(objects)

        # export_flag = input(f"Do you want to export {selected_platform}? (Y/n)\n")
        # if export_flag in ["", "Y", "y"]:
        #     datafile_name = f"exported_{selected_platform.replace('.', '_')}.rep"
        #     print(f"'{selected_platform}' is going to be exported.")
        #
        #     selected_datafile_id = platforms_dict[selected_platform]
        #     with self.data_store.session_scope():
        #         self.data_store.export_datafile(selected_datafile_id, datafile_name)
        #     print(f"Datafile successfully exported to {datafile_name}.")
        # elif export_flag in ["N", "n"]:
        #     print("You selected not to export!")
        # else:
        #     print(f"Please enter a valid input.")

    def do_export_all(self):
        """Start the export all datafiles process"""
        if self.data_store.is_schema_created() is False:
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
        if self.data_store.is_schema_created() is False:
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

    @staticmethod
    def do_exit():
        """Exit the application"""
        print("Thank you for using Pepys Admin")
        exit()

    def default(self, line):
        command, arg, line = self.parseline(line)
        if command in self.aliases:
            self.aliases[command]()
        else:
            print(f"*** Unknown syntax: {line}")

    def postcmd(self, stop, line):
        if line != "0":
            print("-" * 61)
            print(self.intro)
        return cmd.Cmd.postcmd(self, stop, line)
