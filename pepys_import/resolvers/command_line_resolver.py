import sys

from prompt_toolkit import prompt
from prompt_toolkit.completion import FuzzyWordCompleter
from sqlalchemy import or_

from pepys_import.resolvers.data_resolver import DataResolver
from pepys_import.resolvers.command_line_input import create_menu


class CommandLineResolver(DataResolver):
    def __init__(self):
        super().__init__()

    def fuzzy_search_datafile_type(self, data_store):
        datafile_types = data_store.session.query(
            data_store.db_classes.DatafileType
        ).all()
        completer = [p.name for p in datafile_types]
        choice = create_menu(
            "Please start typing to show suggested values",
            choices=[],
            completer=FuzzyWordCompleter(completer),
        )
        if choice not in completer:
            new_choice = create_menu(
                f"You didn't select an existing datafile type. "
                f"Do you want to add '{choice}' to it?",
                choices=["Yes", "No, I'd like to select an existing datafile type"],
            )
            if new_choice == str(1):
                return data_store.add_to_datafile_types(choice)
            elif new_choice == str(2):
                return self.fuzzy_search_datafile_type(data_store)
            elif new_choice == ".":
                print("Quitting")
                sys.exit(1)
        else:
            return (
                data_store.session.query(data_store.db_classes.DatafileType)
                .filter(data_store.db_classes.DatafileType.name == choice)
                .first()
            )

    @staticmethod
    def find_datafile(data_store, datafile_name):
        datafile = (
            data_store.session.query(data_store.db_classes.Datafile)
            .filter(data_store.db_classes.Datafile.reference == datafile_name)
            .first()
        )
        if datafile:
            return datafile

        synonyms = (
            data_store.session.query(data_store.db_classes.Synonym)
            .filter(
                data_store.db_classes.Synonym.synonym == datafile_name,
                data_store.db_classes.Synonym.table == "Datafiles",
            )
            .all()
        )
        # TODO: this should change
        # for synonym in synonyms:
        #     platform = (
        #         data_store.session.query(data_store.db_classes.Platform)
        #         .filter(
        #             or_(
        #                 data_store.db_classes.Platform.name == synonym,
        #                 data_store.db_classes.Platform.trigraph == synonym,
        #                 data_store.db_classes.Platform.quadgraph == synonym,
        #             )
        #         )
        #         .first()
        #     )
        #     if platform:
        #         return platform

        return None

    def fuzzy_search_datafile(self, data_store, datafile_name, datafile_type, privacy):
        datafiles = data_store.session.query(data_store.db_classes.Datafile).all()
        completer = [datafile.reference for datafile in datafiles]
        choice = create_menu(
            "Please start typing to show suggested values",
            choices=[],
            completer=FuzzyWordCompleter(completer),
        )
        if choice not in completer:
            new_choice = create_menu(
                f"You didn't select an existing datafile. "
                f"Do you wish to keep {choice} as synonym?",
                ["Yes", "No"],
            )
            if new_choice == str(1):
                return data_store.add_to_synonyms("Datafiles", datafile_name)
            elif new_choice == str(2):
                return self.add_to_datafiles(
                    data_store, datafile_name, datafile_type, privacy
                )
            elif new_choice == ".":
                print("Quitting")
                sys.exit(1)
        else:
            return (
                data_store.session.query(data_store.db_classes.Datafile)
                .filter(data_store.db_classes.Datafile.reference == choice)
                .first()
            )

    def add_to_datafiles(self, data_store, datafile_name, datafile_type, privacy):
        print("Ok, adding new datafile.")

        # Choose Datafile Type
        if datafile_type:
            chosen_datafile_type = data_store.add_to_datafile_types(datafile_type)
        else:
            chosen_datafile_type = self.fuzzy_search_datafile_type(data_store)

        # Choose Privacy
        if privacy:
            chosen_privacy = data_store.add_to_privacies(privacy)
        else:
            chosen_privacy = self.resolve_privacy(data_store)

        print("Input complete. About to create this datafile:")
        print(f"Name: {datafile_name}")
        print(f"Type: {chosen_datafile_type.name}")
        print(f"Classification: {chosen_privacy.name}")

        choice = create_menu(
            "Create this datafile?: ", ["Yes", "No, make further edits"]
        )

        if choice == str(1):
            return datafile_name, chosen_datafile_type, chosen_privacy
        elif choice == str(2):
            return self.add_to_datafiles(data_store, datafile_name, None, None)
        elif choice == ".":
            print("Quitting")
            sys.exit(1)

    def resolve_datafile(self, data_store, datafile_name, datafile_type, privacy):
        if datafile_name:
            datafile = self.find_datafile(data_store, datafile_name)
            if datafile:
                return datafile

        choice = create_menu(
            f"Datafile '{datafile_name}' not found. Do you wish to: ",
            [
                f"Search for existing datafile",
                f"Add a new datafile, titled '{datafile_name}'",
            ],
        )

        if choice == str(1):
            return self.fuzzy_search_datafile(
                data_store, datafile_name, datafile_type, privacy
            )
        elif choice == str(2):
            return self.add_to_datafiles(
                data_store, datafile_name, datafile_type, privacy
            )
        elif choice == ".":
            print("Quitting")
            sys.exit(1)

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
            .filter(
                data_store.db_classes.Synonym.synonym == platform_name,
                data_store.db_classes.Synonym.table == "Platforms",
            )
            .all()
        )
        # TODO: this should change
        # for synonym in synonyms:
        #     platform = (
        #         data_store.session.query(data_store.db_classes.Platform)
        #         .filter(
        #             or_(
        #                 data_store.db_classes.Platform.name == synonym,
        #                 data_store.db_classes.Platform.trigraph == synonym,
        #                 data_store.db_classes.Platform.quadgraph == synonym,
        #             )
        #         )
        #         .first()
        #     )
        #     if platform:
        #         return platform

        return None

    def fuzzy_search_nationality(self, data_store):
        nationalities = data_store.session.query(
            data_store.db_classes.Nationality
        ).all()
        completer = [n.name for n in nationalities]
        choice = create_menu(
            "Please start typing to show suggested values",
            choices=[],
            completer=FuzzyWordCompleter(completer),
        )
        if choice not in completer:
            new_choice = create_menu(
                f"You didn't select an existing nationality. "
                f"Do you want to add '{choice}' to it?",
                choices=["Yes", "No, I'd like to select an existing nationality"],
            )
            if new_choice == str(1):
                return data_store.add_to_nationalities(choice)
            elif new_choice == str(2):
                return self.fuzzy_search_nationality(data_store)
            elif new_choice == ".":
                print("Quitting")
                sys.exit(1)
        else:
            return (
                data_store.session.query(data_store.db_classes.Nationality)
                .filter(data_store.db_classes.Nationality.name == choice)
                .first()
            )

    def fuzzy_search_platform_type(self, data_store):
        platform_types = data_store.session.query(
            data_store.db_classes.PlatformType
        ).all()
        completer = [p.name for p in platform_types]
        choice = create_menu(
            "Please start typing to show suggested values",
            choices=[],
            completer=FuzzyWordCompleter(completer),
        )
        if choice not in completer:
            new_choice = create_menu(
                f"You didn't select an existing platform type. "
                f"Do you want to add '{choice}' to it?",
                choices=["Yes", "No, I'd like to select an existing platform type"],
            )
            if new_choice == str(1):
                return data_store.add_to_platform_types(choice)
            elif new_choice == str(2):
                return self.fuzzy_search_platform_type(data_store)
            elif new_choice == ".":
                print("Quitting")
                sys.exit(1)
        else:
            return (
                data_store.session.query(data_store.db_classes.PlatformType)
                .filter(data_store.db_classes.PlatformType.name == choice)
                .first()
            )

    def add_to_platforms(
        self, data_store, platform_name, platform_type, nationality, privacy
    ):
        print("Ok, adding new platform.")

        # Choose Nationality
        chosen_nationality = None
        if nationality:
            chosen_nationality = data_store.add_to_nationalities(nationality)
        else:
            nationality_names = [
                "Search for an existing nationality",
                "Add a new nationality",
            ]
            choice = create_menu("Please provide nationality: ", nationality_names)
            if choice == str(1):
                chosen_nationality = self.fuzzy_search_nationality(data_store)
            elif choice == str(2):
                new_nationality = prompt("Please type name of new nationality: ")
                chosen_nationality = data_store.search_nationality(new_nationality)
                if not chosen_nationality:
                    chosen_nationality = data_store.add_to_nationalities(
                        new_nationality
                    )
            elif choice == ".":
                print("Quitting")
                sys.exit(1)

        # Choose Platform Type
        chosen_platform_type = None
        if platform_type:
            chosen_platform_type = data_store.add_to_platform_types(platform_type)
        else:
            platform_type_names = [
                "Search for an existing platform-type",
                "Add a new platform-type",
            ]
            choice = create_menu(
                "Ok, please provide platform-type: ", platform_type_names
            )
            if choice == str(1):
                chosen_platform_type = self.fuzzy_search_platform_type(data_store)
            elif choice == str(2):
                new_platform_type = prompt("Please type name of new platform-type: ")
                chosen_platform_type = data_store.search_platform_type(
                    new_platform_type
                )
                if not chosen_platform_type:
                    chosen_platform_type = data_store.add_to_platform_types(
                        new_platform_type
                    )
            elif choice == ".":
                print("Quitting")
                sys.exit(1)

        # Choose Privacy
        if privacy:
            chosen_privacy = data_store.add_to_privacies(privacy)
        else:
            chosen_privacy = self.resolve_privacy(data_store)

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

    def fuzzy_search_platform(
        self, data_store, platform_name, platform_type, nationality, privacy
    ):
        completer = list()
        platforms = data_store.session.query(data_store.db_classes.Platform).all()
        for platform in platforms:
            completer.append(platform.name)
            completer.append(platform.trigraph)
            completer.append(platform.quadgraph)
        choice = create_menu(
            "Please start typing to show suggested values",
            choices=[],
            completer=FuzzyWordCompleter(completer),
        )
        if choice not in completer:
            new_choice = create_menu(
                f"You didn't select an existing platform. "
                f"Do you wish to keep {choice} as synonym?",
                ["Yes", "No"],
            )
            if new_choice == str(1):
                return data_store.add_to_synonyms("Platforms", platform_name)
            elif new_choice == str(2):
                return self.add_to_platforms(
                    data_store, platform_name, platform_type, nationality, privacy
                )
            elif new_choice == ".":
                print("Quitting")
                sys.exit(1)
        else:
            return (
                data_store.session.query(data_store.db_classes.Platform)
                .filter(data_store.db_classes.Platform.name == choice)
                .first()
            )

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
            return self.fuzzy_search_platform(
                data_store, platform_name, platform_type, nationality, privacy
            )
        elif choice == str(2):
            return self.add_to_platforms(
                data_store, platform_name, platform_type, nationality, privacy
            )
        elif choice == ".":
            print("Quitting")
            sys.exit(1)

    def fuzzy_search_sensor_type(self, data_store):
        sensor_types = data_store.session.query(data_store.db_classes.SensorType).all()
        completer = [sensor_type.name for sensor_type in sensor_types]
        choice = create_menu(
            "Please start typing to show suggested values",
            choices=[],
            completer=FuzzyWordCompleter(completer),
        )
        if choice not in completer:
            new_choice = create_menu(
                f"You didn't select an existing sensor type. "
                f"Do you want to add '{choice}' to it?",
                choices=["Yes", "No, I'd like to select an sensor type"],
            )
            if new_choice == str(1):
                return data_store.add_to_sensor_types(choice)
            elif new_choice == str(2):
                return self.fuzzy_search_sensor_type(data_store)
            elif new_choice == ".":
                print("Quitting")
                sys.exit(1)
        else:
            return (
                data_store.session.query(data_store.db_classes.SensorType)
                .filter(data_store.db_classes.SensorType.name == choice)
                .first()
            )

    def add_to_sensors(self, data_store, sensor_type, privacy):
        # Choose Sensor Type
        print("Ok, adding new sensor.")

        if not sensor_type:
            sensor_type_names = [
                "Search for an existing sensor-type",
                "Add a new sensor-type",
            ]
            choice = create_menu("Please provide sensor-type: ", sensor_type_names)

            if choice == str(1):
                sensor_type = self.fuzzy_search_sensor_type(data_store)
            elif choice == str(2):
                new_input = prompt("Please type name of new sensor-type: ")
                sensor_type = data_store.search_sensor_type(new_input)
            elif choice == ".":
                print("Quitting")
                sys.exit(1)

        if not privacy:
            privacy = self.fuzzy_search_privacy(data_store)

        return sensor_type, privacy

    def fuzzy_search_sensor(self, data_store, sensor_type, privacy):
        sensors = data_store.session.query(data_store.db_classes.Sensor).all()
        completer = [sensor.name for sensor in sensors]
        choice = create_menu(
            "Please start typing to show suggested values",
            choices=[],
            completer=FuzzyWordCompleter(completer),
        )
        if choice not in completer:
            new_choice = create_menu(
                f"You didn't select an existing sensor. "
                f"Do you want to add '{choice}' to it?",
                choices=["Yes", "No, I'd like to select an existing sensor"],
            )
            if new_choice == str(1):
                return self.add_to_sensors(data_store, sensor_type, privacy)
            elif new_choice == str(2):
                return self.fuzzy_search_sensor(data_store, sensor_type, privacy)
            elif new_choice == ".":
                print("Quitting")
                sys.exit(1)
        else:
            return (
                data_store.session.query(data_store.db_classes.Sensor)
                .filter(data_store.db_classes.Sensor.name == choice)
                .first()
            )

    @staticmethod
    def find_sensor(data_store, sensor_name):
        sensor = (
            data_store.session.query(data_store.db_classes.Sensor)
            .filter(data_store.db_classes.Sensor.name == sensor_name)
            .first()
        )
        if sensor:
            return sensor

        synonyms = (
            data_store.session.query(data_store.db_classes.Synonym)
            .filter(
                data_store.db_classes.Synonym.synonym == sensor_name,
                data_store.db_classes.Synonym.table == "Sensors",
            )
            .all()
        )
        # TODO: ask questions if this is the use of synonyms table or not
        # for synonym in synonyms:
        #     sensor = (
        #         data_store.session.query(data_store.db_classes.Sensor)
        #         .filter(data_store.db_classes.Sensor.name == synonym)
        #         .first()
        #     )
        #     if sensor:
        #         return sensor

        return None

    def resolve_sensor(self, data_store, sensor_name, sensor_type, privacy):
        # Check for name match in Sensor and Synonym Tables
        sensor = self.find_sensor(data_store, sensor_name)
        if sensor:
            return sensor

        # Not found, carry on
        choice = create_menu(
            f"Sensor '{sensor_name}' not found. Do you wish to: ",
            [
                f"Search for existing sensor",
                f"Add a new sensor, titled '{sensor_name}'",
            ],
        )

        if choice == str(1):
            return self.fuzzy_search_sensor(data_store, sensor_type, privacy)
        elif choice == str(2):
            return self.add_to_sensors(data_store, sensor_type, privacy)
        elif choice == ".":
            print("Quitting")
            sys.exit(1)

    def fuzzy_search_privacy(self, data_store):
        privacies = data_store.session.query(data_store.db_classes.Privacy).all()
        completer = [p.name for p in privacies]
        choice = create_menu(
            "Please start typing to show suggested values",
            choices=[],
            completer=FuzzyWordCompleter(completer),
        )
        if choice not in completer:
            new_choice = create_menu(
                f"You didn't select an existing classification. "
                f"Do you want to add '{choice}' to it?",
                choices=["Yes", "No, I'd like to select an existing classification"],
            )
            if new_choice == str(1):
                return data_store.add_to_privacies(choice)
            elif new_choice == str(2):
                return self.fuzzy_search_privacy(data_store)
            elif new_choice == ".":
                print("Quitting")
                sys.exit(1)
        else:
            return (
                data_store.session.query(data_store.db_classes.Privacy)
                .filter(data_store.db_classes.Privacy.name == choice)
                .first()
            )

    def resolve_privacy(self, data_store):
        # Choose Privacy
        privacy_names = [
            "Search an existing classification",
            "Add a new classification",
        ]
        choice = create_menu(
            f"Ok, please provide classification for new entry: ", privacy_names
        )

        if choice == str(1):
            return self.fuzzy_search_privacy(data_store)
        elif choice == str(2):
            new_privacy = prompt("Please type name of new classification: ")
            privacy = data_store.search_privacy(new_privacy)
            if privacy:
                return privacy
            else:
                return data_store.add_to_privacies(new_privacy)
        elif choice == ".":
            print("Quitting")
            sys.exit(1)
