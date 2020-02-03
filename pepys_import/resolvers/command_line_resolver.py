import sys
from .data_resolver import DataResolver
from .command_line_input import get_choice_input


class CommandLineResolver(DataResolver):
    def __init__(self):
        self.table_privacies = {}

    def synonym_search(self, data_store, platform_name):
        input_ = input("Please type word stem to search for: ")
        result = data_store.search_platform(input_)
        if result is None:
            # couldn't find it
            not_found = get_choice_input(
                f"Platform with '{input_}' not found. Do you wish to: ",
                [
                    "Search for another synonym of this name",
                    f"Add a new platform, titled '{platform_name}'",
                    "Cancel import",
                ],
            )

            if not_found == 1:
                self.synonym_search(data_store, platform_name)
            elif not_found == 2:
                return 2
            elif not_found == 3:
                print("Quitting")
                sys.exit(1)
        else:
            # found something
            found = get_choice_input(
                f"Platform '{result}' found. Would you like to add this as a synonym: ",
                ["Yes", "No, find other synonym", "Cancel import"],
            )
            if found == 1:
                return result
            elif found == 2:
                self.synonym_search(data_store, platform_name)
            elif found == 3:
                print("Quitting")
                sys.exit(1)

    def add_to_platforms(
        self, data_store, platform_name, platform_type_str, nationality_str, privacy_str
    ):
        print("Ok, adding new platform.")

        # Choose Nationality
        if nationality_str:
            chosen_nationality = data_store.add_to_nationalities(nationality_str)
        else:
            nationalities = data_store.get_nationalities()
            nationality_names = [n.name for n in nationalities]
            nationality_names.append("Add a new nationality")
            nationality_names.append("Cancel import")
            choice = get_choice_input("Please provide nationality: ", nationality_names)
            if choice == len(nationality_names):
                print("Quitting")
                sys.exit(1)
            elif choice == len(nationality_names) - 1:
                nationality_check_ok = False
                while not nationality_check_ok:
                    new_input = input("Please type name of new nationality: ")
                    nationality_check_ok = data_store.check_nationality(new_input)
                chosen_nationality = data_store.add_to_nationalities(new_input)

        # Choose Platform Type
        if platform_type_str:
            chosen_platform_type = data_store.add_to_platform_types(platform_type_str)
        else:
            platform_types = data_store.get_platform_types()
            platform_type_names = [c.name for c in platform_types]
            platform_type_names.append("Add a new platform-type")
            platform_type_names.append("Cancel import")
            choice = get_choice_input(
                "Ok, please provide platform-type: ", platform_type_names
            )
            if choice == len(platform_type_names):
                print("Quitting")
                sys.exit(1)
            elif choice == len(platform_type_names) - 1:
                platform_type_ok = False
                while not platform_type_ok:
                    new_input = input("Please type name of new platform-type: ")
                    platform_type_ok = data_store.check_platform_type(new_input)
                chosen_platform_type = data_store.add_to_platform_types(new_input)
            else:
                chosen_platform_type = platform_types[choice - 2]

        # Choose Sensor
        sensors = data_store.get_sensors_by_platform_type(chosen_platform_type)
        if len(sensors) > 0:
            sensor_names = [s.Sensor.name for s in sensors]
            sensor_names.append("Cancel import")
            choice = get_choice_input(
                f"We have {len(sensor_names) - 1} other instances of "
                f"{chosen_platform_type.name} class. They contain these "
                f"sensors. Please indicate which you wish to add to "
                f"{platform_name}: ",
                sensor_names,
            )
            if choice == len(sensor_names):
                print("Quitting")
                sys.exit(1)

            chosen_sensor = sensors[choice - 1]
        else:
            print("No sensors found for that class. Skipping Sensor add")
            chosen_sensor = None
            # TODO: Should we delete the code below?
            # choices = ["Add a new sensor", "Cancel import"]
            # choice = get_choice_input(f"No instances of class {chosen_platform_type.name} exist. Please choose an option: ",
            #                                                choices)
            # if choice == len(choices):
            #     print("Quitting")
            #     sys.exit(1)
            # elif choice == len(choices)-1:
            #     sensorCheckOk = False
            #     while not sensorCheckOk:
            #         newSensorInput = input("Please type name of new sensor: ")
            #         sensorCheckOk = data_store.checkSensor(newSensorInput)
            #     #chosen_sensor = data_store.addToSensors(new_input)
            #     chosen_sensor = newSensorInput
            #     newSensor = True

        # Choose Privacy
        if privacy_str:
            chosen_privacy = data_store.add_to_privacies(privacy_str)
        else:
            privacies = data_store.get_privacies()
            privacy_names = [c.name for c in privacies]
            privacy_names.append("Add a new classification")
            privacy_names.append("Cancel import")
            choice = get_choice_input(
                "Ok, please provide classification for this platform: ", privacy_names
            )

            if choice == len(privacy_names):
                print("Quitting")
                sys.exit(1)
            elif choice == len(privacy_names) - 1:
                privacy_check_ok = False
                while not privacy_check_ok:
                    new_input = input("Please type name of new classification: ")
                    privacy_check_ok = data_store.check_privacy(new_input)
                chosen_privacy = data_store.add_to_privacies(new_input)
            else:
                chosen_privacy = privacies[choice - 2]

        print("Input complete. About to create this platform:")
        print(f"Name: {platform_name}")
        print(f"Nationality: {chosen_nationality.name}")
        print(f"Class: {chosen_platform_type.name}")
        if chosen_sensor:
            print(f"Sensors: {chosen_sensor.Sensor.name}")
        else:
            print("Sensors: None")
        print(f"Classification: {chosen_privacy.name}")

        choice = get_choice_input(
            "Create this platform?: ",
            ["Yes", "No, make further edits", "Cancel import"],
        )

        if choice == 1:
            # TODO: pass back sensor and classification when Schema changed
            return (
                platform_name,
                chosen_platform_type,
                chosen_nationality,
                chosen_privacy,
            )
        elif choice == 2:
            return self.add_to_platforms(data_store, platform_name, None, None, None)
        elif choice == 3:
            print("Quitting")
            sys.exit(1)

    def resolve_platform(
        self, data_store, platform_name, platform_type, nationality, privacy
    ):
        choice = get_choice_input(
            f"Platform '{platform_name}' not found. Do you wish to: ",
            [  # "Search for synonym of this name",
                f"Add a new platform, titled '{platform_name}'",
                "Cancel import",
            ],
        )

        if choice == 1:
            # synSearch = self.synonym_search(data_store, platform_name)
            # print(f"Adding {synSearch} as a synonym for {platform_name}")
            return self.add_to_platforms(
                data_store, platform_name, platform_type, nationality, privacy
            )
        else:
            print("Quitting")
            sys.exit(1)

    def add_to_sensors(self, data_store, sensor_name):
        # Choose Sensor Type
        print("Ok, adding new sensor.")
        sensor_types = data_store.get_sensor_types()
        sensor_type_names = [st.name for st in sensor_types]
        sensor_type_names.append("Add a new sensor-type")
        sensor_type_names.append("Cancel import")
        choice = get_choice_input("Please provide sensor-type: ", sensor_type_names)
        if choice == len(sensor_type_names):
            print("Quitting")
            sys.exit(1)
        elif choice == len(sensor_type_names) - 1:
            sensor_type_check_ok = False
            while not sensor_type_check_ok:
                new_input = input("Please type name of new sensor-type: ")
                sensor_type_check_ok = data_store.check_sensor_type(new_input)
            chosen_sensor_type = data_store.add_to_sensor_types(new_input)
        else:
            chosen_sensor_type = sensor_types[choice - 2]

        return sensor_name, chosen_sensor_type

    def resolve_sensor(self, data_store, sensor_name):
        choice = get_choice_input(
            f"Sensor '{sensor_name}' not found. Do you wish to: ",
            [f"Add a new sensor, titled '{sensor_name}'", "Cancel import"],
        )

        if choice == 1:
            return self.add_to_sensors(data_store, sensor_name)
        elif choice == 2:
            print("Quitting")
            sys.exit(1)

    def resolve_privacy(self, data_store, table_type_id, table_name):
        if table_type_id in self.table_privacies:
            return table_type_id, self.table_privacies[table_type_id]

        # Choose Privacy
        privacies = data_store.get_privacies()
        privacy_names = [c.name for c in privacies]
        privacy_names.append("Add a new classification")
        privacy_names.append("Cancel import")
        choice = get_choice_input(
            f"Ok, please provide classification for new entry in {table_name}: ",
            privacy_names,
        )

        if choice == len(privacy_names):
            print("Quitting")
            sys.exit(1)
        elif choice == len(privacy_names) - 1:
            privacy_check_ok = False
            while not privacy_check_ok:
                new_input = input("Please type name of new classification: ")
                privacy_check_ok = data_store.check_privacy(new_input)
            chosen_privacy = data_store.add_to_privacies(new_input)
        else:
            chosen_privacy = privacies[choice - 2]

        self.table_privacies[table_type_id] = chosen_privacy

        return table_type_id, chosen_privacy
