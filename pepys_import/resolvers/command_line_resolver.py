import sys

from prompt_toolkit.completion import FuzzyWordCompleter
from sqlalchemy import or_

from pepys_import.resolvers.data_resolver import DataResolver
from pepys_import.resolvers.command_line_input import create_menu

from prompt_toolkit import prompt


class CommandLineResolver(DataResolver):
    def __init__(self):
        super().__init__()

    # def synonym_search(self, data_store, platform_name):
    #     input_ = prompt("Please type word stem to search for: ")
    #     result = data_store.search_platform(input_)
    #     if result is None:
    #         # couldn't find it
    #         not_found = create_menu(
    #             f"Platform with '{input_}' not found. Do you wish to: ",
    #             [
    #                 "Search for another synonym of this name",
    #                 f"Add a new platform, titled '{platform_name}'",
    #                 "Cancel import",
    #             ],
    #         )
    #
    #         if not_found == 1:
    #             self.synonym_search(data_store, platform_name)
    #         elif not_found == 2:
    #             return 2
    #         elif not_found == 3:
    #             print("Quitting")
    #             sys.exit(1)
    #     else:
    #         # found something
    #         found = create_menu(
    #             f"Platform '{result}' found. Would you like to add this as a synonym: ",
    #             ["Yes", "No, find other synonym", "Cancel import"],
    #         )
    #         if found == 1:
    #             return result
    #         elif found == 2:
    #             self.synonym_search(data_store, platform_name)
    #         elif found == 3:
    #             print("Quitting")
    #             sys.exit(1)

    @staticmethod
    def find_platform(data_store, platform_name):
        platform = (
            data_store.session.query(data_store.db_classes.Platform)
            .filter(
                or_(
                    data_store.db_classes.Platform.name == platform_name,
                    data_store.db_classes.Platform.trigraph == platform_name,
                    data_store.db_classes.Platform.quadgraph == platform_name,
                )
            )
            .first()
        )
        if platform:
            return platform

        synonyms = (
            data_store.session.query(data_store.db_classes.Synonym)
            .filter(data_store.db_classes.Synonym.synonym == platform_name)
            .all()
        )
        for synonym in synonyms:
            platform = (
                data_store.session.query(data_store.db_classes.Platform)
                .filter(
                    or_(
                        data_store.db_classes.Platform.name == synonym,
                        data_store.db_classes.Platform.trigraph == synonym,
                        data_store.db_classes.Platform.quadgraph == synonym,
                    )
                )
                .first()
            )
            if platform:
                return platform

        return None

    @staticmethod
    def fuzzy_search_platform(data_store, platform_name):
        completer = list()
        platforms = (
            data_store.session.query(data_store.db_classes.Platform)
            .filter(
                or_(
                    data_store.db_classes.Platform.name == platform_name,
                    data_store.db_classes.Platform.trigraph == platform_name,
                    data_store.db_classes.Platform.quadgraph == platform_name,
                )
            )
            .all()
        )
        for platform in platforms:
            completer.append(platform.name)
            completer.append(platform.trigraph)
            completer.append(platform.quadgraph)

        choice = create_menu(
            "Please start typing to show suggested values",
            choices=[],
            completer=FuzzyWordCompleter(completer),
        )
        print(choice)
        return choice

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
                    new_input = prompt("Please type name of new nationality: ")
                    nationality_check_ok = data_store.search_nationality(new_input)
                chosen_nationality = data_store.add_to_nationalities(new_input)

        # Choose Platform Type
        chosen_platform_type = None
        if platform_type:
            chosen_platform_type = data_store.add_to_platform_types(platform_type)
        else:
            platform_type_names = ["Add a new platform-type"]
            choice = create_menu(
                "Ok, please provide platform-type: ", platform_type_names
            )
            if choice == ".":
                print("Quitting")
                sys.exit(1)
            elif choice == str(1):
                platform_type = False
                while not platform_type:
                    new_input = prompt("Please type name of new platform-type: ")
                    platform_type = data_store.search_platform_type(new_input)
                chosen_platform_type = data_store.add_to_platform_types(new_input)

        # Choose Privacy
        chosen_privacy = None
        if privacy:
            chosen_privacy = data_store.add_to_privacies(privacy)
        else:
            privacy_names = ["Add a new classification"]
            choice = create_menu(
                "Ok, please provide classification for this platform: ", privacy_names
            )

            if choice == ".":
                print("Quitting")
                sys.exit(1)
            elif choice == str(1):
                privacy_check = False
                while not privacy_check:
                    new_input = prompt("Please type name of new classification: ")
                    privacy_check = data_store.search_privacy(new_input)
                chosen_privacy = data_store.add_to_privacies(new_input)

        print("Input complete. About to create this platform:")
        print(f"Name: {platform_name}")
        print(f"Nationality: {chosen_nationality.name}")
        print(f"Class: {chosen_platform_type.name}")
        print(f"Classification: {chosen_privacy.name}")

        choice = create_menu(
            "Create this platform?: ", ["Yes", "No, make further edits"]
        )

        if choice == str(1):
            return (
                platform_name,
                chosen_platform_type,
                chosen_nationality,
                chosen_privacy,
            )
        elif choice == str(2):
            return self.add_to_platforms(data_store, platform_name, None, None, None)
        elif choice == ".":
            print("Quitting")
            sys.exit(1)

    def resolve_platform(
        self, data_store, platform_name, platform_type, nationality, privacy
    ):
        if platform_name:
            platform = self.find_platform(data_store, platform_name)
            if platform:
                return platform

        choice = create_menu(
            f"Platform '{platform_name}' not found. Do you wish to: ",
            [
                f"Search for existing platform",
                f"Add a new platform, titled '{platform_name}'",
            ],
        )

        if choice == str(1):
            result = self.fuzzy_search_platform(data_store, platform_name)
            if result and platform_name:
                synonym_choice = create_menu(
                    f"Do you wish to keep {platform_name} as synonym?", ["Yes", "No"]
                )
                if synonym_choice == str(1):
                    return data_store.add_to_synonyms("Platforms", platform_name)
                elif synonym_choice == str(2):
                    return self.add_to_platforms(
                        data_store, platform_name, platform_type, nationality, privacy
                    )
                elif synonym_choice == ".":
                    print("Quitting")
                    sys.exit(1)
        elif choice == str(2):
            return self.add_to_platforms(
                data_store, platform_name, platform_type, nationality, privacy
            )
        elif choice == ".":
            print("Quitting")
            sys.exit(1)

    def add_to_sensors(self, data_store, sensor_type, privacy):
        # Choose Sensor Type
        print("Ok, adding new sensor.")
        sensor_type_names = ["Add a new sensor-type"]
        choice = create_menu("Please provide sensor-type: ", sensor_type_names)

        if choice == str(1):
            if not sensor_type:
                new_input = prompt("Please type name of new sensor-type: ")
                sensor_type = data_store.search_sensor_type(new_input)
            if not privacy:
                privacy = self.resolve_privacy(data_store)

            return sensor_type, privacy
        elif choice == ".":
            print("Quitting")
            sys.exit(1)

    def resolve_sensor(self, data_store, sensor_name, sensor_type, privacy):
        # Check for name match in Sensor Table
        sensor = data_store.search_sensor(sensor_name.upper())
        if sensor:
            return sensor
        # Check for synonym match
        # TODO: search_synonym not implemented yet
        # sensor_synonym = data_store.search_synonym(sensor_name.upper())
        # if sensor_synonym:
        #     return sensor_synonym

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
            return self.add_to_sensors(data_store, sensor_type, privacy)
        elif choice == ".":
            print("Quitting")
            sys.exit(1)

    def resolve_privacy(self, data_store):
        # Choose Privacy
        privacy_names = ["Add a new classification"]
        choice = create_menu(
            f"Ok, please provide classification for new entry: ", privacy_names
        )

        if choice == str(1):
            new_privacy = prompt("Please type name of new classification: ")
            privacy = data_store.search_privacy(new_privacy)
            if privacy:
                return privacy
            else:
                return data_store.add_to_privacies(new_privacy)
        elif choice == ".":
            print("Quitting")
            sys.exit(1)
