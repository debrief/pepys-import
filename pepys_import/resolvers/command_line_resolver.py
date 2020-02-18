import sys
from .data_resolver import DataResolver
from .command_line_input import create_menu
from qprompt import ask_str


class CommandLineResolver(DataResolver):
    def __init__(self):
        super().__init__()

    def synonym_search(self, data_store, platform_name):
        input_ = ask_str("Please type word stem to search for: ")
        result = data_store.search_platform(input_)
        if result is None:
            # couldn't find it
            not_found = create_menu(
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
            found = create_menu(
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
        self, data_store, platform_name, platform_type, nationality, privacy
    ):
        print("Ok, adding new platform.")

        # Choose Nationality
        chosen_nationality = None
        if nationality:
            chosen_nationality = data_store.add_to_nationalities(nationality)
        else:
            nationality_names = ["Add a new nationality"]
            choice = create_menu("Please provide nationality: ", nationality_names)
            if choice == ".":
                print("Quitting")
                sys.exit(1)
            elif choice == str(1):
                nationality_check_ok = False
                while not nationality_check_ok:
                    new_input = ask_str("Please type name of new nationality: ")
                    nationality_check_ok = data_store.search_nationality(new_input)
                chosen_nationality = data_store.add_to_nationalities(new_input)

        # Choose Platform Type
        chosen_platform_type = None
        if platform_type:
            chosen_platform_type = data_store.add_to_platform_types(platform_type)
        else:
            platform_types = data_store.get_platform_types()
            platform_type_names = [c.name for c in platform_types]
            platform_type_names.append("Add a new platform-type")
            platform_type_names.append("Cancel import")
            choice = create_menu(
                "Ok, please provide platform-type: ", platform_type_names
            )
            if choice == ".":
                print("Quitting")
                sys.exit(1)
            elif choice == str(1):
                platform_type_ok = False
                while not platform_type_ok:
                    new_input = ask_str("Please type name of new platform-type: ")
                    platform_type_ok = data_store.check_platform_type(new_input)
                chosen_platform_type = data_store.add_to_platform_types(new_input)

        # Choose Sensor
        chosen_sensor = None
        sensor_names = ["Add a new sensor"]
        choice = create_menu(
            f"Please indicate which sensor you wish to add to {platform_name}: ",
            sensor_names,
        )
        if choice == ".":
            print("Quitting")
            sys.exit(1)
        elif choice == str(1):
            sensor_check_ok = False
            while not sensor_check_ok:
                new_input = ask_str("Please type name of new sensor: ")
                sensor_check_ok = data_store.search_sensor(new_input)
            chosen_sensor = data_store.add_to_sensors(new_input)

        # Choose Privacy
        chosen_privacy = None
        if privacy:
            chosen_privacy = data_store.add_to_privacies(privacy)
        else:
            privacies = data_store.get_privacies()
            privacy_names = [c.name for c in privacies]
            privacy_names.append("Add a new classification")
            privacy_names.append("Cancel import")
            choice = create_menu(
                "Ok, please provide classification for this platform: ", privacy_names
            )

            if choice == ".":
                print("Quitting")
                sys.exit(1)
            elif choice == str(1):
                privacy_check_ok = False
                while not privacy_check_ok:
                    new_input = ask_str("Please type name of new classification: ")
                    privacy_check_ok = data_store.check_privacy(new_input)
                chosen_privacy = data_store.add_to_privacies(new_input)

        print("Input complete. About to create this platform:")
        print(f"Name: {platform_name}")
        print(f"Nationality: {chosen_nationality.name}")
        print(f"Class: {chosen_platform_type.name}")
        if chosen_sensor:
            print(f"Sensors: {chosen_sensor}")
        else:
            print("Sensors: None")
        print(f"Classification: {chosen_privacy.name}")

        choice = create_menu(
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
        if platform_name:
            platform = data_store.search_platform(platform_name)
            if platform:
                return platform

            # platform = self.check_trigraph_and_quadgraph(platform_name)
            # if platform:
            #     return platform
            #
            # platform = self.check_synonym(platform_name)
            # if platform:
            #     return platform

        choice = create_menu(
            f"Platform '{platform_name}' not found. Do you wish to: ",
            [
                f"Search for existing platform",
                f"Add a new platform, titled '{platform_name}'",
            ],
        )

        if choice == str(1):
            # search = fzf_search(input)
            pass
        elif choice == str(2):
            return self.add_to_platforms(
                data_store, platform_name, platform_type, nationality, privacy
            )
        elif choice == ".":
            print("Quitting")
            sys.exit(1)

    def add_to_sensors(self, data_store, sensor_name, privacy):
        # Choose Sensor Type
        print("Ok, adding new sensor.")
        sensor_type_names = ["Add a new sensor-type"]
        choice = create_menu("Please provide sensor-type: ", sensor_type_names)

        if choice == str(1):
            sensor_type = None
            while not sensor_type:
                new_input = ask_str("Please type name of new sensor-type: ")
                sensor_type = data_store.search_sensor_type(new_input)
            chosen_sensor_type = sensor_type

            if not privacy:
                privacy = self.resolve_privacy(data_store)

            return sensor_name, chosen_sensor_type, privacy
        elif choice == ".":
            print("Quitting")
            sys.exit(1)

    def resolve_sensor(self, data_store, sensor_name, privacy):
        # Check for name match in Sensor Table
        sensor = data_store.search_sensor(sensor_name.upper())
        if sensor:
            return sensor
        # Check for synonym match
        # TODO: search_synonym not implemented yet
        sensor_synonym = data_store.search_synonym(sensor_name.upper())
        if sensor_synonym:
            return sensor_synonym

        # Not found, carry on
        choice = create_menu(
            f"Sensor '{sensor_name}' not found. Do you wish to: ",
            [
                f"Search for existing sensor",
                f"Add a new sensor, titled '{sensor_name}'",
            ],
        )

        if choice == str(1):
            # TODO: do fuzzy search of names and synonyms
            # If match found: ask yes/no to add to synonyms table
            pass
        elif choice == str(2):
            return self.add_to_sensors(data_store, sensor_name, privacy)
        elif choice == ".":
            print("Quitting")
            sys.exit(1)

    def resolve_privacy(self, data_store):
        # Choose Privacy
        privacy_names = ["Add a new classification"]
        choice = create_menu(
            f"Ok, please provide classification for new entry: ", privacy_names,
        )

        if choice == str(1):
            privacy = None
            while not privacy:
                new_input = ask_str("Please type name of new classification: ")
                privacy = data_store.check_privacy(new_input)
            chosen_privacy = privacy

            return chosen_privacy
        elif choice == ".":
            print("Quitting")
            sys.exit(1)
