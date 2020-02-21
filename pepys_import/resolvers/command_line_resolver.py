import sys

from prompt_toolkit import prompt
from prompt_toolkit.completion import FuzzyWordCompleter
from sqlalchemy import or_

from pepys_import.resolvers.data_resolver import DataResolver
from pepys_import.resolvers.command_line_input import create_menu


class CommandLineResolver(DataResolver):
    def __init__(self):
        super().__init__()

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

    # Helper methods
    def fuzzy_search_datafile(self, data_store, datafile_name, datafile_type, privacy):
        """
        This method parses all datafiles in the DB, and uses fuzzy search when
        user is typing. If user enters a new value, it adds to Synonym or Datafiles
        according to user's choice. If user selects an existing value, it returns the
        selected Datafile entity.

        :param data_store: A :class:`DataStore` object
        :type data_store: :class:`DataStore`
        :param datafile_name:  Name of Datafile
        :type datafile_name: String
        :param datafile_type: Type of Datafile
        :type datafile_type: DatafileType
        :param privacy: Name of :class:`Privacy`
        :type privacy: Privacy
        :return:
        """
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

    def fuzzy_search_platform(
        self, data_store, platform_name, platform_type, nationality, privacy
    ):
        """
        This method parses all platforms in the DB, and uses fuzzy search when
        user is typing. If user enters a new value, it adds to Synonym or Platforms
        according to user's choice. If user selects an existing value, it returns the
        selected Platform entity.

        :param data_store: A :class:`DataStore` object
        :type data_store: :class:`DataStore`
        :param platform_name: Name of :class:`Platform`
        :type platform_name: String
        :param nationality: Name of :class:`Nationality`
        :type nationality: Nationality
        :param platform_type: Name of :class:`PlatformType`
        :type platform_type: PlatformType
        :param privacy: Name of :class:`Privacy`
        :type privacy: Privacy
        :return:
        """
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

    def fuzzy_search_sensor(self, data_store, sensor_type, privacy):
        """
        This method parses all sensors in the DB, and uses fuzzy search when
        user is typing. If user enters a new value, it adds to Sensor table or searches
        for an existing sensor again. If user selects an existing value, it returns the
        selected Sensor entity.

        :param data_store: A :class:`DataStore` object
        :type data_store: :class:`DataStore`
        :param sensor_type: Type of :class:`Sensor`
        :type sensor_type: SensorType
        :param privacy: Name of :class:`Privacy`
        :type privacy: Privacy
        :return:
        """
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

    def fuzzy_search_privacy(self, data_store):
        """
        This method parses all privacies in the DB, and uses fuzzy search when
        user is typing. If user enters a new value, it adds to Privacy table or searches
        for an existing privacy again. If user selects an existing value, it returns the
        selected Privacy entity.

        :param data_store: A :class:`DataStore` object
        :type data_store: :class:`DataStore`
        :return:
        """

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

    def fuzzy_search_datafile_type(self, data_store):
        """
        This method parses all datafile types in the DB, and uses fuzzy search when
        user is typing. If user enters a new value, it adds to DatafileType table or
        searches for an existing privacy again. If user selects an existing value,
        it returns the selected DatafileType entity.

        :param data_store: A :class:`DataStore` object
        :type data_store: :class:`DataStore`
        :return:
        """

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

    def fuzzy_search_nationality(self, data_store):
        """
        This method parses all Nationalities in the DB, and uses fuzzy search when
        user is typing. If user enters a new value, it adds to Nationality table or
        searches for an existing nationality again. If user selects an existing value,
        it returns the selected Nationality entity.

        :param data_store: A :class:`DataStore` object
        :type data_store: :class:`DataStore`
        :return:
        """
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
        """
        This method parses all platform types in the DB, and uses fuzzy search when
        user is typing. If user enters a new value, it adds to PlatformType table or
        searches for an existing privacy again. If user selects an existing value,
        it returns the selected PlatformType entity.

        :param data_store: A :class:`DataStore` object
        :type data_store: :class:`DataStore`
        :return:
        """
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

    def fuzzy_search_sensor_type(self, data_store):
        """
        This method parses all sensor types in the DB, and uses fuzzy search when
        user is typing. If user enters a new value, it adds to SensorType table or
        searches for an existing privacy again. If user selects an existing value,
        it returns the selected SensorType entity.

        :param data_store: A :class:`DataStore` object
        :type data_store: :class:`DataStore`
        :return:
        """
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

    def resolve_nationality(self, data_store):
        """
        This method asks user whether user wants to select from an existing nationality
        or add a new nationality. If user wants to select from an existing nationality,
        it returns the result from fuzzy search method. If user wants to add a new
        nationality, it searches DB first to prevent duplicates. If it is not found,
        it adds it to Nationality table. Finally, it returns the found or created entity

        :param data_store: A :class:`DataStore` object
        :type data_store: :class:`DataStore`
        :return:
        """
        nationality_names = [
            "Search for an existing nationality",
            "Add a new nationality",
        ]
        choice = create_menu("Please provide nationality: ", nationality_names)
        if choice == str(1):
            return self.fuzzy_search_nationality(data_store)
        elif choice == str(2):
            new_nationality = prompt("Please type name of new nationality: ")
            nationality = data_store.search_nationality(new_nationality)
            if nationality:
                return nationality
            else:
                return data_store.add_to_nationalities(new_nationality)
        elif choice == ".":
            print("Quitting")
            sys.exit(1)

    def resolve_platform_type(self, data_store):
        platform_type_names = [
            "Search for an existing platform-type",
            "Add a new platform-type",
        ]
        choice = create_menu("Ok, please provide platform-type: ", platform_type_names)
        if choice == str(1):
            return self.fuzzy_search_platform_type(data_store)
        elif choice == str(2):
            new_platform_type = prompt("Please type name of new platform-type: ")
            platform_type = data_store.search_platform_type(new_platform_type)
            if platform_type:
                return platform_type
            else:
                return data_store.add_to_platform_types(new_platform_type)
        elif choice == ".":
            print("Quitting")
            sys.exit(1)

    def resolve_sensor_type(self, data_store):
        """
        This method asks user whether user wants to select from an existing sensor type
        or add a new sensor type. If user wants to select from an existing sensor type,
        it returns the result from fuzzy search method. If user wants to add a new
        sensor type, it searches DB first to prevent duplicates. If it is not found,
        it adds it to SensorType table. Finally, it returns the found or created entity.

        :param data_store: A :class:`DataStore` object
        :type data_store: :class:`DataStore`
        :return:
        """
        sensor_type_names = [
            "Search for an existing sensor-type",
            "Add a new sensor-type",
        ]
        choice = create_menu("Please provide sensor-type: ", sensor_type_names)

        if choice == str(1):
            return self.fuzzy_search_sensor_type(data_store)
        elif choice == str(2):
            new_input = prompt("Please type name of new sensor-type: ")
            sensor_type = data_store.search_sensor_type(new_input)
            if sensor_type:
                return sensor_type

            return data_store.add_to_sensor_types(new_input)
        elif choice == ".":
            print("Quitting")
            sys.exit(1)

    def add_to_datafiles(self, data_store, datafile_name, datafile_type, privacy):
        """
        This method resolves datafile type and privacy. It asks user whether to create
        a datafile with resolved values or not. If user enters Yes, it returns all
        necessary data to create a datafile. If user enters No, it resolves values again

        :param data_store: A :class:`DataStore` object
        :type data_store: :class:`DataStore`
        :param datafile_name:  Name of Datafile
        :type datafile_name: String
        :param datafile_type: Type of Datafile
        :type datafile_type: DatafileType
        :param privacy: Name of :class:`Privacy`
        :type privacy: Privacy
        :return:
        """
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

    def add_to_platforms(
        self, data_store, platform_name, platform_type, nationality, privacy
    ):
        """
        This method resolves platform type, nationality and privacy. It asks user
        whether to create a platform with resolved values or not. If user enters Yes,
        it returns all necessary data to create a platform.
        If user enters No, it resolves values again.

        :param data_store: A :class:`DataStore` object
        :type data_store: :class:`DataStore`
        :param platform_name: Name of :class:`Platform`
        :type platform_name: String
        :param nationality: Name of :class:`Nationality`
        :type nationality: Nationality
        :param platform_type: Name of :class:`PlatformType`
        :type platform_type: PlatformType
        :param privacy: Name of :class:`Privacy`
        :type privacy: Privacy
        :return:
        """
        print("Ok, adding new platform.")

        # Choose Nationality
        if nationality:
            chosen_nationality = data_store.add_to_nationalities(nationality)
        else:
            chosen_nationality = self.resolve_nationality(data_store)

        # Choose Platform Type
        if platform_type:
            chosen_platform_type = data_store.add_to_platform_types(platform_type)
        else:
            chosen_platform_type = self.resolve_platform_type(data_store)

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

    def add_to_sensors(self, data_store, sensor_type, privacy):
        """
        This method resolves sensor type and privacy. It returns existing or resolved
        sensor type and privacy entities.

        :param data_store: A :class:`DataStore` object
        :type data_store: :class:`DataStore`
        :param sensor_type: Type of :class:`Sensor`
        :type sensor_type: SensorType
        :param privacy: Name of :class:`Privacy`
        :type privacy: Privacy
        :return:
        """
        # Choose Sensor Type
        print("Ok, adding new sensor.")

        if sensor_type:
            sensor_type = data_store.add_to_sensor_types(sensor_type)
        else:
            sensor_type = self.resolve_sensor_type(data_store)

        if privacy:
            privacy = data_store.add_to_privacies(privacy)
        else:
            privacy = self.resolve_privacy(data_store)

        return sensor_type, privacy

    @staticmethod
    def find_datafile(data_store, datafile_name):
        """
        This method tries to find a Datafile entity with the given datafile_name. If it
        finds, it returns the entity. If it is not found, it searches synonyms.

        :param data_store: A :class:`DataStore` object
        :type data_store: :class:`DataStore`
        :param datafile_name:  Name of Datafile
        :type datafile_name: String
        :return:
        """
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

    @staticmethod
    def find_platform(data_store, platform_name):
        """
        This method tries to find a Platform entity with the given platform_name. If it
        finds, it returns the entity. If it is not found, it searches synonyms.

        :param data_store: A :class:`DataStore` object
        :type data_store: :class:`DataStore`
        :param platform_name: Name of :class:`Platform`
        :type platform_name: String
        :return:
        """
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

    @staticmethod
    def find_sensor(data_store, sensor_name):
        """
        This method tries to find a Sensor entity with the given sensor_name. If it
        finds, it returns the entity. If it is not found, it searches synonyms.

        :param data_store: A :class:`DataStore` object
        :type data_store: :class:`DataStore`
        :param sensor_name: Name of :class:`Sensor`
        :type sensor_name: String
        :return:
        """
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
