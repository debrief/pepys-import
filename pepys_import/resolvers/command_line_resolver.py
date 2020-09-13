import re
import sys

from prompt_toolkit import prompt
from prompt_toolkit.validation import Validator
from sqlalchemy import or_
from tabulate import tabulate

from pepys_import.core.store import constants
from pepys_import.resolvers.command_line_input import create_menu, get_fuzzy_completer, is_valid
from pepys_import.resolvers.data_resolver import DataResolver


def is_number(text):
    return text.isdigit()


numeric_validator = Validator.from_callable(
    is_number, error_message="This input contains non-numeric characters", move_cursor_to_end=True
)


class CommandLineResolver(DataResolver):
    def resolve_datafile(self, data_store, datafile_name, datafile_type, privacy, change_id):
        """
        This method resolves datafile type and privacy. It asks user whether to create
        a datafile with resolved values or not. If user enters Yes, it returns all
        necessary data to create a datafile. If user enters No, it resolves values again

        :param data_store: A :class:`DataStore` object
        :type data_store: DataStore
        :param datafile_name:  Name of :class`Datafile`
        :type datafile_name: String
        :param datafile_type: Type of :class`Datafile`
        :type datafile_type: String
        :param privacy: Name of :class:`Privacy`
        :type privacy: String
        :param change_id: ID of the :class:`Change` object
        :type change_id: UUID
        :return:
        """
        print("Ok, adding new datafile.")

        datafile_name = prompt("Please enter a name: ", default=datafile_name).strip()

        if datafile_name == "":
            print("You must provide a datafile name. Restarting data file entry.")
            return self.resolve_datafile(
                data_store, datafile_name, datafile_type, privacy, change_id
            )
        if len(datafile_name) > 150:
            print(
                "Datafile name too long, maximum length 150 characters. Restarting data file entry."
            )
            return self.resolve_datafile(
                data_store, datafile_name, datafile_type, privacy, change_id
            )

        # Choose Datafile Type
        if datafile_type:
            chosen_datafile_type = data_store.add_to_datafile_types(datafile_type, change_id)
        else:
            chosen_datafile_type = self.resolve_reference(
                data_store,
                change_id,
                data_type="Datafile",
                db_class=data_store.db_classes.DatafileType,
                field_name="datafile_type",
            )

        if chosen_datafile_type is None:
            print("Quitting")
            sys.exit(1)

        # Choose Privacy
        if privacy:
            chosen_privacy = data_store.search_privacy(privacy)
            if chosen_privacy is None:
                level = prompt(
                    f"Please type level of new classification ({privacy}): ",
                    validator=numeric_validator,
                )
                chosen_privacy = data_store.add_to_privacies(privacy, level, change_id)
        else:
            chosen_privacy = self.resolve_reference(
                data_store,
                change_id,
                data_type="Datafile",
                db_class=data_store.db_classes.Privacy,
                field_name="privacy",
                text_name="classification",
            )

        if chosen_privacy is None:
            print("Quitting")
            sys.exit(1)

        print("-" * 61)
        print("Input complete. About to create this datafile:")
        print(f"Name: {datafile_name}")
        print(f"Type: {chosen_datafile_type.name}")
        print(f"Classification: {chosen_privacy.name}")

        choice = create_menu(
            "Create this datafile?: ",
            ["Yes", "No, make further edits"],
            validate_method=is_valid,
        )

        if choice == str(1):
            return datafile_name, chosen_datafile_type, chosen_privacy
        elif choice == str(2):
            return self.resolve_datafile(data_store, datafile_name, None, None, change_id)
        elif choice == ".":
            print("Quitting")
            sys.exit(1)

    def resolve_platform(
        self, data_store, platform_name, platform_type, nationality, privacy, change_id
    ):
        platform_details = []
        final_options = ["Search for existing platform", "Add a new platform"]
        if platform_name:
            # If we've got a platform_name, then we can search for all platforms
            # with this name, and present a list to the user to choose from,
            # alongside the options to search for an existing platform and add
            # a new platform

            # The order-by clause is important, to get the same ordering of
            # options on different platforms/db backends, so that our tests work
            platforms = (
                data_store.session.query(data_store.db_classes.Platform)
                .join(data_store.db_classes.Nationality)
                .filter(data_store.db_classes.Platform.name == platform_name)
                .order_by(
                    data_store.db_classes.Platform.identifier.asc(),
                    data_store.db_classes.Nationality.priority.asc(),
                    data_store.db_classes.Nationality.name.asc(),
                )
                .all()
            )
            for platform in platforms:
                platform_details.append(
                    f"{platform.name} / {platform.identifier} / {platform.nationality_name}"
                )
            final_options[1] += f", default name '{platform_name}'"
        choices = platform_details + final_options
        choice = create_menu(
            f"Select a platform entry for {platform_name}:",
            choices,
            validate_method=is_valid,
        )
        if choice == ".":
            print("Quitting")
            sys.exit(1)
        if int(choice) <= len(platform_details):
            # One of the pre-existing platforms was chosen
            platform_index = int(choice) - 1
            return platforms[platform_index]
        elif choice == str(len(choices) - 1):
            return self.fuzzy_search_platform(
                data_store,
                platform_name,
                platform_type,
                nationality,
                privacy,
                change_id,
            )
        elif choice == str(len(choices)):
            return self.add_to_platforms(
                data_store,
                platform_name,
                platform_type,
                nationality,
                privacy,
                change_id,
            )

    def resolve_sensor(self, data_store, sensor_name, sensor_type, host_id, privacy, change_id):
        Platform = data_store.db_classes.Platform
        host_platform = (
            data_store.session.query(Platform).filter(Platform.platform_id == host_id).first()
        )
        if not host_platform:
            print("Invalid platform id specified")
            print("Quitting")
            sys.exit(1)

        options = [
            f"Search for existing sensor on platform '{host_platform.name}'",
            "Add a new sensor",
        ]
        objects = (
            data_store.session.query(data_store.db_classes.Sensor)
            .filter(data_store.db_classes.Sensor.host == host_id)
            .all()
        )
        objects_dict = {obj.name: obj for obj in objects}
        if len(objects_dict) <= 7:
            options.extend(objects_dict)
        if sensor_name:
            options[1] += f", default name '{sensor_name}'"
            prompt = f"Sensor '{sensor_name}' on platform '{host_platform.name}' not found. Do you wish to: "
        else:
            prompt = f"Sensor on platform '{host_platform.name}' not found. Do you wish to: "

        def is_valid_dynamic(option):  # pragma: no cover
            return option in [str(i) for i in range(1, len(options) + 1)] or option == "."

        choice = create_menu(prompt, options, validate_method=is_valid_dynamic)
        if choice == ".":
            print("Quitting")
            sys.exit(1)
        elif choice == str(1):
            return self.fuzzy_search_sensor(
                data_store, sensor_name, sensor_type, host_platform.platform_id, privacy, change_id
            )
        elif choice == str(2):
            return self.add_to_sensors(
                data_store, sensor_name, sensor_type, host_id, privacy, change_id
            )
        elif 3 <= int(choice) <= len(options):
            selected_object = objects_dict[options[int(choice) - 1]]
            if selected_object:
                return selected_object

    def resolve_reference(
        self, data_store, change_id, data_type, db_class, field_name, text_name=None
    ):
        """
        This method resolves any reference data according to the given parameters.

        :param data_store: A :class:`DataStore` object
        :type data_store: DataStore
        :param change_id: ID of the :class:`Change` object
        :type change_id: UUID
        :param data_type: For which data type the reference is resolved(Platform, Sensor or Datafile)
        :type data_type: String
        :param db_class: Class of a Reference Table
        :type db_class: SQLAlchemy Declarative Base Class
        :param field_name: Name of the resolved data
        :type field_name: String
        :param text_name: Printed name of the resolved data
        :type text_name: String
        :return:
        """
        if text_name is None:
            text_name = field_name.replace("_", "-")
        options = [f"Search an existing {text_name}", f"Add a new {text_name}"]
        title = f"Ok, please provide {text_name} for new {data_type}: "
        current_values = ""
        if db_class.__tablename__ == constants.NATIONALITY:
            objects = (
                data_store.session.query(db_class)
                .filter(db_class.priority.in_([1, 2]))
                .order_by(db_class.priority, db_class.name)
                .all()
            )
        elif db_class.__tablename__ == constants.PRIVACY:
            all_values = data_store.session.query(db_class).order_by(db_class.level).all()
            objects = all_values[:7]
            current_values = "\nCurrent Privacies in the Database\n"
            headers = ["name", "level"]
            current_values += tabulate(
                [[str(getattr(row, column)) for column in headers] for row in all_values],
                headers=headers,
                tablefmt="github",
                floatfmt=".3f",
            )
            current_values += "\n"
        else:
            objects = data_store.session.query(db_class).limit(7).all()
        objects_dict = {obj.name: obj for obj in objects}
        # CamelCase table names should be split into words, separated by "-" and converted to
        # lowercase for matching with DataStore add methods (i.e. PlatformTypes -> platform_types)
        plural_field = (
            re.sub("([A-Z][a-z]+)", r" \1", re.sub("([A-Z]+)", r"\1", db_class.__tablename__))
            .strip()
            .lower()
            .replace(" ", "_")
        )
        options.extend(objects_dict)

        def is_valid_dynamic(option):  # pragma: no cover
            return option in [str(i) for i in range(1, len(options) + 1)] or option == "."

        choice = create_menu(
            title,
            options,
            validate_method=is_valid_dynamic,
        )
        if choice == ".":
            print("-" * 61, "\nReturning to the previous menu\n")
            return None
        elif choice == str(1):
            result = self.fuzzy_search_reference(
                data_store, change_id, data_type, db_class, field_name, text_name
            )
            if result is None:
                return self.resolve_reference(
                    data_store, change_id, data_type, db_class, field_name, text_name
                )
            else:
                return result
        elif choice == str(2):
            print(current_values)
            while True:
                new_object = prompt(f"Please type name of new {text_name}: ").strip()
                # If not too long for the field
                if len(new_object) <= 150:
                    break
                else:
                    print("Name too long, please enter a name less than 150 characters long")
            search_method = getattr(data_store, f"search_{field_name}")
            obj = search_method(new_object)
            if obj:
                return obj
            elif new_object:
                add_method = getattr(data_store, f"add_to_{plural_field}")
                if plural_field == "privacies":
                    level = prompt(
                        f"Please type level of new {text_name}: ", validator=numeric_validator
                    )
                    return add_method(new_object, level, change_id)
                return add_method(new_object, change_id)
            else:
                print("You haven't entered an input!")
                return self.resolve_reference(
                    data_store, change_id, data_type, db_class, field_name, text_name
                )
        elif 3 <= int(choice) <= len(options):
            selected_object = objects_dict[options[int(choice) - 1]]
            if selected_object:
                return selected_object

    def fuzzy_search_reference(
        self, data_store, change_id, data_type, db_class, field_name, text_name=None
    ):
        """
        This method parses any reference data according to the given parameters, and uses fuzzy
        search when user is typing. If user enters a new value, it adds to the related reference
        table or searches for an existing entity again. If user selects an existing value,
        it returns the selected entity.

        :param data_store: A :class:`DataStore` object
        :type data_store: DataStore
        :param change_id: ID of the :class:`Change` object
        :type change_id: UUID
        :param data_type: For which data type the reference is resolved(Platform, Sensor or Datafile)
        :type data_type: String
        :param db_class: Class of a Reference Table
        :type db_class: SQLAlchemy Declarative Base Class
        :param field_name: Name of the resolved data
        :type field_name: String
        :param text_name: Printed name of the resolved data
        :type text_name: String
        :return:
        """
        objects = data_store.session.query(db_class).all()
        completer = [p.name for p in objects]
        choice = create_menu(
            "Please start typing to show suggested values",
            cancel=f"{text_name} search",
            choices=[],
            completer=get_fuzzy_completer(completer),
        )
        if choice == ".":
            print("-" * 61, "\nReturning to the previous menu\n")
            return None
        elif choice not in completer:
            new_choice = create_menu(
                f"You didn't select an existing {text_name}. " f"Do you want to add '{choice}' ?",
                choices=["Yes", f"No, I'd like to select an existing {text_name}"],
                validate_method=is_valid,
            )
            if new_choice == str(1):
                plural_field = (
                    re.sub(
                        "([A-Z][a-z]+)", r" \1", re.sub("([A-Z]+)", r"\1", db_class.__tablename__)
                    )
                    .strip()
                    .lower()
                    .replace(" ", "_")
                )
                add_method = getattr(data_store, f"add_to_{plural_field}")
                if plural_field == "privacies":
                    level = prompt(
                        f"Please type level of new {text_name}: ", validator=numeric_validator
                    )
                    return add_method(choice, level, change_id)
                return add_method(choice, change_id)
            elif new_choice == str(2):
                return self.fuzzy_search_reference(
                    data_store, change_id, data_type, db_class, field_name, text_name
                )
            elif new_choice == ".":
                print("-" * 61, "\nReturning to the previous menu\n")
                return self.resolve_reference(
                    data_store, change_id, data_type, db_class, field_name, text_name
                )
        else:
            return data_store.session.query(db_class).filter(db_class.name == choice).first()

    # Helper methods
    def fuzzy_search_platform(
        self, data_store, platform_name, platform_type, nationality, privacy, change_id
    ):
        """
        This method parses all platforms in the DB, and uses fuzzy search when
        user is typing. If user enters a new value, it adds to Synonym or Platforms
        according to user's choice. If user selects an existing value, it returns the
        selected Platform entity.

        :param data_store: A :class:`DataStore` object
        :type data_store: DataStore
        :param platform_name: Name of :class:`Platform`
        :type platform_name: String
        :param nationality: Name of :class:`Nationality`
        :type nationality: Nationality
        :param platform_type: Name of :class:`PlatformType`
        :type platform_type: PlatformType
        :param privacy: Name of :class:`Privacy`
        :type privacy: Privacy
        :param change_id: ID of the :class:`Change` object
        :type change_id: UUID
        :return:
        """
        completer = list()
        platforms = data_store.session.query(data_store.db_classes.Platform).all()
        for platform in platforms:
            completer.append(
                f"{platform.name} / {platform.identifier} / {platform.nationality_name}"
            )
            if platform.trigraph:
                completer.append(
                    f"{platform.trigraph} / {platform.identifier} / {platform.nationality_name}"
                )
            if platform.quadgraph:
                completer.append(
                    f"{platform.quadgraph} / {platform.identifier} / {platform.nationality_name}"
                )
        choice = create_menu(
            "Please start typing to show suggested values",
            cancel="platform search",
            choices=[],
            completer=get_fuzzy_completer(completer),
        )
        if choice in completer:
            # Extract the platform details from the string
            name_or_xgraph, identifier, nationality = choice.split(" / ")
            # Get the platform from the database
            platform = (
                data_store.session.query(data_store.db_classes.Platform)
                .filter(
                    or_(
                        data_store.db_classes.Platform.name == name_or_xgraph,
                        data_store.db_classes.Platform.trigraph == name_or_xgraph,
                        data_store.db_classes.Platform.quadgraph == name_or_xgraph,
                    )
                )
                .filter(data_store.db_classes.Platform.identifier == identifier)
                .filter(data_store.db_classes.Platform.nationality_name == nationality)
                .first()
            )
            # If we've been given a platform name, then we might want to link
            # that platform name to the one we've picked, as a synonym
            if platform_name:
                new_choice = create_menu(
                    f"Do you wish to keep {platform_name} as synonym for {choice}?\n"
                    f"Warning: this should only be done when {platform_name} is a completely unique identifier for this platform\n"
                    f"not a name that could be shared across platforms of different nationalities",
                    ["Yes", "No"],
                    validate_method=is_valid,
                )
                if new_choice == str(1):
                    # Add it to synonyms and return existing platform
                    data_store.add_to_synonyms(
                        constants.PLATFORM, platform_name, platform.platform_id, change_id
                    )
                    print(f"'{platform_name}' added to Synonyms!")
                    return platform
                elif new_choice == str(2):
                    return platform
                elif new_choice == ".":
                    print("-" * 61, "\nReturning to the previous menu\n")
                    return self.fuzzy_search_platform(
                        data_store,
                        platform_name,
                        platform_type,
                        nationality,
                        privacy,
                        change_id,
                    )
            return platform
        elif choice == ".":
            print("-" * 61, "\nReturning to the previous menu\n")
            return self.resolve_platform(
                data_store,
                platform_name,
                nationality,
                platform_type,
                privacy,
                change_id,
            )
        elif choice not in completer:
            print(f"'{choice}' could not be found! Redirecting to adding a new platform..")
            return self.add_to_platforms(
                data_store, choice, platform_type, nationality, privacy, change_id
            )

    def fuzzy_search_sensor(
        self, data_store, sensor_name, sensor_type, host_id, privacy, change_id
    ):
        """
        This method parses all sensors in the DB, and uses fuzzy search when
        user is typing. If user enters a new value, it adds to Sensor table or searches
        for an existing sensor again. If user selects an existing value, it returns the
        selected Sensor entity.

        :param data_store: A :class:`DataStore` object
        :type data_store: DataStore
        :param sensor_name: Name of :class:`Sensor`
        :type sensor_name: Sensor
        :param sensor_type: Type of :class:`Sensor`
        :type sensor_type: SensorType
        :param privacy: Name of :class:`Privacy`
        :type privacy: Privacy
        :param change_id: ID of the :class:`Change` object
        :type change_id: UUID
        :return:
        """
        sensors = (
            data_store.session.query(data_store.db_classes.Sensor)
            .filter(data_store.db_classes.Sensor.host == host_id)
            .all()
        )
        completer = [sensor.name for sensor in sensors]

        choice = create_menu(
            "Please start typing to show suggested values",
            cancel="sensor search",
            choices=[],
            completer=get_fuzzy_completer(completer),
        )
        if choice == ".":
            print("-" * 61, "\nReturning to the previous menu\n")
            return self.resolve_sensor(
                data_store, sensor_name, sensor_type, host_id, privacy, change_id
            )
        elif choice not in completer:
            print(f"'{choice}' could not be found! Redirecting to adding a new sensor..")
            return self.add_to_sensors(
                data_store, sensor_name, sensor_type, host_id, privacy, change_id
            )
        else:
            return (
                data_store.session.query(data_store.db_classes.Sensor)
                .filter(data_store.db_classes.Sensor.name == choice)
                .first()
            )

    def add_to_platforms(
        self, data_store, platform_name, platform_type, nationality, privacy, change_id
    ):
        """
        This method resolves platform type, nationality and privacy. It asks user
        whether to create a platform with resolved values or not. If user enters Yes,
        it returns all necessary data to create a platform.
        If user enters No, it resolves values again.

        :param data_store: A :class:`DataStore` object
        :type data_store: DataStore
        :param identifier: Identifier string
        :type identifier: String
        :param platform_name: Name of :class:`Platform`
        :type platform_name: String
        :param nationality: Name of :class:`Nationality`
        :type nationality: Nationality
        :param platform_type: Name of :class:`PlatformType`
        :type platform_type: PlatformType
        :param privacy: Name of :class:`Privacy`
        :type privacy: Privacy
        :param change_id: ID of the :class:`Change` object
        :type change_id: UUID
        :return:
        """
        print("Ok, adding new platform.")
        if platform_name is None:
            platform_name = ""

        platform_name = prompt("Please enter a name: ", default=platform_name).strip()
        if len(platform_name) > 150:
            print(
                "Platform name too long, maximum length 150 characters. Restarting platform data entry."
            )
            return self.add_to_platforms(
                data_store, platform_name, platform_type, nationality, privacy, change_id
            )

        identifier = prompt("Please enter identifier (pennant or tail number): ").strip()
        if len(identifier) > 10:
            print(
                "Identifier too long, maximum length 10 characters. Restarting platform data entry."
            )
            return self.add_to_platforms(
                data_store, platform_name, platform_type, nationality, privacy, change_id
            )

        trigraph = prompt("Please enter trigraph (optional): ", default=platform_name[:3]).strip()
        if len(trigraph) > 3:
            print("Trigraph too long, maximum length 3 characters. Restarting platform data entry.")
            return self.add_to_platforms(
                data_store, platform_name, platform_type, nationality, privacy, change_id
            )

        quadgraph = prompt("Please enter quadgraph (optional): ", default=platform_name[:4]).strip()
        if len(quadgraph) > 4:
            print(
                "Quadgraph too long, maximum length 4 characters. Restarting platform data entry."
            )
            return self.add_to_platforms(
                data_store, platform_name, platform_type, nationality, privacy, change_id
            )

        if platform_name == "" or identifier == "":
            print("You must provide a platform name and identifier! Restarting plaform data entry.")
            return self.add_to_platforms(
                data_store, platform_name, platform_type, nationality, privacy, change_id
            )

        # Choose Nationality
        if nationality:
            chosen_nationality = data_store.add_to_nationalities(nationality, change_id)
        else:
            chosen_nationality = self.resolve_reference(
                data_store,
                change_id,
                "Platform",
                data_store.db_classes.Nationality,
                "nationality",
            )
        if chosen_nationality is None:
            print("Nationality couldn't resolved. Returning to the previous menu!")
            return self.resolve_platform(data_store, platform_name, None, None, None, change_id)

        # Choose Platform Type
        if platform_type:
            chosen_platform_type = data_store.add_to_platform_types(platform_type, change_id)
        else:
            chosen_platform_type = self.resolve_reference(
                data_store,
                change_id,
                data_type="Platform",
                db_class=data_store.db_classes.PlatformType,
                field_name="platform_type",
            )

        if chosen_platform_type is None:
            print("Platform Type couldn't resolved. Returning to the previous menu!")
            return self.resolve_platform(data_store, platform_name, None, None, None, change_id)

        # Choose Privacy
        if privacy:
            chosen_privacy = data_store.search_privacy(privacy)
            if chosen_privacy is None:
                level = prompt(
                    f"Please type level of new classification ({privacy}): ",
                    validator=numeric_validator,
                )
                chosen_privacy = data_store.add_to_privacies(privacy, level, change_id)
        else:
            chosen_privacy = self.resolve_reference(
                data_store,
                change_id,
                data_type="Platform",
                text_name="classification",
                db_class=data_store.db_classes.Privacy,
                field_name="privacy",
            )

        if chosen_privacy is None:
            print("Classification couldn't resolved. Returning to the previous menu!")
            return self.resolve_platform(data_store, platform_name, None, None, None, change_id)

        print("-" * 61)
        print("Input complete. About to create this platform:")
        print(f"Name: {platform_name}")
        print(f"Trigraph: {trigraph}")
        print(f"Quadgraph: {quadgraph}")
        print(f"Identifier: {identifier}")
        print(f"Nationality: {chosen_nationality.name}")
        print(f"Class: {chosen_platform_type.name}")
        print(f"Classification: {chosen_privacy.name}")

        choice = create_menu(
            "Create this platform?: ",
            ["Yes", "No, make further edits"],
            validate_method=is_valid,
        )

        if choice == str(1):
            return (
                platform_name,
                trigraph,
                quadgraph,
                identifier,
                chosen_platform_type,
                chosen_nationality,
                chosen_privacy,
            )
        elif choice == str(2):
            return self.add_to_platforms(data_store, platform_name, None, None, None, change_id)
        elif choice == ".":
            print("-" * 61, "\nReturning to the previous menu\n")
            return self.resolve_platform(data_store, platform_name, None, None, None, change_id)

    def add_to_sensors(self, data_store, sensor_name, sensor_type, host_id, privacy, change_id):
        """
        This method resolves sensor type and privacy. It returns existing or resolved
        sensor type and privacy entities.

        :param data_store: A :class:`DataStore` object
        :type data_store: DataStore
        :param sensor_name: Name of :class:`Sensor`
        :type sensor_name: Sensor
        :param sensor_type: Type of :class:`Sensor`
        :type sensor_type: SensorType
        :param privacy: Name of :class:`Privacy`
        :type privacy: Privacy
        :param change_id: ID of the :class:`Change` object
        :type change_id: UUID
        :return:
        """
        # Choose Sensor Type
        print("Ok, adding new sensor.")

        # Can't pass None to prompt function below, so pass empty string instead
        if sensor_name is None:
            sensor_name = ""

        sensor_name = prompt("Please enter a name: ", default=sensor_name).strip()

        if sensor_name == "":
            print("You must provide a sensor name. Restarting sensor data entry")
            return self.add_to_sensors(
                data_store, sensor_name, sensor_type, host_id, privacy, change_id
            )
        if len(sensor_name) > 150:
            print(
                "Sensor name too long, maximum length 150 characters. Restarting sensor data entry."
            )
            return self.add_to_sensors(
                data_store, sensor_name, sensor_type, host_id, privacy, change_id
            )

        if sensor_type:
            sensor_type = data_store.add_to_sensor_types(sensor_type, change_id)
        else:
            sensor_type = self.resolve_reference(
                data_store,
                change_id,
                data_type="Sensor",
                db_class=data_store.db_classes.SensorType,
                field_name="sensor_type",
            )

        if sensor_type is None:
            print("Sensor Type couldn't resolved. Returning to the previous menu!")
            return self.resolve_sensor(data_store, sensor_name, None, host_id, None, change_id)

        if privacy:
            chosen_privacy = data_store.search_privacy(privacy)
            if chosen_privacy is None:
                level = prompt(
                    f"Please type level of new classification ({privacy}): ",
                    validator=numeric_validator,
                )
                chosen_privacy = data_store.add_to_privacies(privacy, level, change_id)
        else:
            chosen_privacy = self.resolve_reference(
                data_store,
                change_id,
                data_type="Sensor",
                text_name="classification",
                db_class=data_store.db_classes.Privacy,
                field_name="privacy",
            )

        if chosen_privacy is None:
            print("Classification couldn't resolved. Returning to the previous menu!")
            return self.resolve_sensor(data_store, sensor_name, None, host_id, None, change_id)

        print("-" * 61)
        print("Input complete. About to create this sensor:")
        print(f"Name: {sensor_name}")
        print(f"Type: {sensor_type.name}")
        print(f"Classification: {chosen_privacy.name}")

        choice = create_menu(
            "Create this sensor?: ",
            ["Yes", "No, make further edits"],
            validate_method=is_valid,
        )

        if choice == str(1):
            return sensor_name, sensor_type, chosen_privacy
        elif choice == str(2):
            return self.add_to_sensors(data_store, sensor_name, None, host_id, None, change_id)
        elif choice == ".":
            print("-" * 61, "\nReturning to the previous menu\n")
            return self.resolve_sensor(data_store, sensor_name, None, host_id, None, change_id)
