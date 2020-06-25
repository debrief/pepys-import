import cmd
import os
from datetime import datetime

from iterfzf import iterfzf
from prompt_toolkit import prompt as ptk_prompt
from prompt_toolkit.completion import PathCompleter

from pepys_admin.utils import get_default_export_folder
from pepys_import.utils.data_store_utils import is_schema_created


class ExportShell(cmd.Cmd):
    """Offers to export datafiles by name, by platform and sensor"""

    intro = """--- Menu ---
    (1) Export by name
    (2) Export by Platform and sensor
    (.) Back
    """

    prompt = "(pepys-admin) (export) "

    @staticmethod
    def do_cancel():
        """Returns to the previous menu"""
        print("Returning to the previous menu...")

    def __init__(self, data_store):
        super(ExportShell, self).__init__()
        self.data_store = data_store
        self.aliases = {
            ".": self.do_cancel,
            "1": self.do_export,
            "2": self.do_export_by_platform_name,
            "9": self.do_export_all,
        }

    def do_export(self):
        """Exports datafiles by name."""
        if is_schema_created(self.data_store.engine, self.data_store.db_type) is False:
            return

        with self.data_store.session_scope():
            datafiles = self.data_store.get_all_datafiles()
            if not datafiles:
                print("There is no datafile found in the database!")
                return
            datafiles_dict = {d.reference: d.datafile_id for d in datafiles}
        message = "Select a datafile to export > "
        selected_datafile = iterfzf(datafiles_dict.keys(), prompt=message)

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
        """Exports datafiles by platform and sensor names. It asks user to select an existing
        :code:`Platform` first. Then, it finds all datafile objects which include the selected
        :code:`Platform`. Creates a dynamic intro (menu) from the found datafile objects, runs
        :code:`ExportByPlatformNameShell`
        """
        if is_schema_created(self.data_store.engine, self.data_store.db_type) is False:
            return

        Sensor = self.data_store.db_classes.Sensor
        with self.data_store.session_scope():
            platforms = self.data_store.session.query(self.data_store.db_classes.Platform).all()
            if not platforms:
                print("There is no platform found in the database!")
                return
            platforms_dict = {p.name: p.platform_id for p in platforms}
        message = "Select a platform name to export datafiles that include it > "
        selected_platform = iterfzf(platforms_dict.keys(), prompt=message)

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
        text = "Select from the found datafile objects.\n"
        text += "--- Menu ---\n"
        options = [
            ".",
        ]
        for index, obj in enumerate(objects, 1):
            text += f"({index}) {obj['name']} {obj['filename']} {obj['min']}-{obj['max']}\n"
            options.append(str(index))
        text += "(.) Cancel\n"
        # Initialise a new menu
        export_platform = ExportByPlatformNameShell(self.data_store, options, objects)
        export_platform.cmdloop(intro=text)

    def do_export_all(self):
        """Exports all datafiles."""
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

    def default(self, line):
        cmd_, arg, line = self.parseline(line)
        # Python accepts letters, digits, and "_" character as a command.
        # Therefore, "." is interpreted as an argument.
        if arg == "." and line == ".":
            return True
        elif cmd_ in self.aliases:
            self.aliases[cmd_]()
        else:
            print(f"*** Unknown syntax: {line}")

    def postcmd(self, stop, line):
        if line != ".":
            print("-" * 61)
            print(self.intro)
        return cmd.Cmd.postcmd(self, stop, line)


class ExportByPlatformNameShell(cmd.Cmd):
    """Offers to export datafiles by platform and sensor"""

    prompt = "(pepys-admin) (export by platform) "

    def __init__(self, data_store, options, objects):
        super(ExportByPlatformNameShell, self).__init__()
        self.data_store = data_store
        self.options = options
        self.objects = objects

    @staticmethod
    def do_cancel():
        """Returns to the previous menu"""
        print("Returning to the previous menu...")

    def do_export(self, option):
        """Asks user for a file name, then calls :code:`DataStore.export_datafile` to export Datafiles."""
        datafile_id = option["datafile_id"]
        sensor_id = option.get("sensor_id")  # May be missing if it's a Comment object
        platform_id = option.get("platform_id")  # May be missing if it's a State or Contact object
        default_export_name = f"exported_{option['name']}.rep"

        file_name = input(
            f"Please provide a name (Press Enter for default value " f"({default_export_name})):"
        )
        if file_name:
            if not file_name.endswith(".rep"):
                file_name += ".rep"
        export_file_name = file_name or default_export_name

        folder_completer = PathCompleter(only_directories=True, expanduser=True)
        folder_path = ptk_prompt(
            "Please provide a folder path for the exported file: ",
            default=get_default_export_folder(),
            completer=folder_completer,
            complete_while_typing=True,
        )

        export_file_full_path = os.path.expanduser(os.path.join(folder_path, export_file_name))
        print(f"Objects are going to be exported to '{export_file_full_path}'.")
        with self.data_store.session_scope():
            self.data_store.export_datafile(
                datafile_id, export_file_full_path, sensor_id, platform_id
            )
            print(f"Objects successfully exported to {export_file_full_path}.")
        return True

    def default(self, line):
        cmd_, arg, line = self.parseline(line)
        # Python accepts letters, digits, and "_" character as a command.
        # Therefore, "." is interpreted as an argument.
        if arg == "." and line == ".":
            return True
        elif cmd_ in self.options:
            selected_option = self.objects[int(cmd_) - 1]
            return self.do_export(selected_option)
        else:
            print(f"*** Unknown syntax: {line}")

    def postcmd(self, stop, line):
        if stop is False:
            print("-" * 61)
            print(self.intro)
        return cmd.Cmd.postcmd(self, stop, line)
