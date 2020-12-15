import sys
from collections import OrderedDict

from prompt_toolkit import prompt
from prompt_toolkit.validation import Validator
from tabulate import tabulate

from pepys_import.core.store.constants import NATIONALITY, PLATFORM, PRIVACY
from pepys_import.resolvers import constants
from pepys_import.resolvers.command_line_input import create_menu, get_fuzzy_completer, is_valid
from pepys_import.resolvers.data_resolver import DataResolver
from pepys_import.utils.text_formatting_utils import (
    format_command,
    print_help_text,
    print_new_section_title,
)

TQDM_BAR_FORMAT = "{l_bar}{bar} | {n_fmt}/{total_fmt}"


def is_number(text):
    return text.isdigit()


numeric_validator = Validator.from_callable(
    is_number, error_message="This input contains non-numeric characters", move_cursor_to_end=True
)


class CommandLineResolver(DataResolver):
    def __init__(self):
        self.platform_questions_responses = OrderedDict()
        self.platform_questions_order = list()
        self.sensor_questions_responses = OrderedDict()
        self.sensor_questions_order = list()
        self.validation_dict = dict()

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
        if datafile_name is None:
            raise ValueError("You must specify a datafile name when calling resolve_datafile")

        print_new_section_title("Resolve Datafile")
        print(f"Ok, adding new datafile {datafile_name}.")

        # Choose Datafile Type
        if datafile_type:
            chosen_datafile_type = data_store.add_to_datafile_types(datafile_type, change_id)
        else:
            chosen_datafile_type = self.resolve_reference(
                data_store,
                change_id,
                data_type=f"Datafile named '{datafile_name}'",
                db_class=data_store.db_classes.DatafileType,
                field_name="datafile_type",
                help_id=constants.RESOLVE_DATAFILE_TYPE,
                search_help_id=constants.FUZZY_SEARCH_DATAFILE_TYPE,
            )

        if chosen_datafile_type is None:
            print("Quitting")
            sys.exit(1)

        # Choose Privacy
        if privacy:
            chosen_privacy = data_store.search_privacy(privacy)
            if chosen_privacy is None:
                level = prompt(
                    format_command(f"Please type level of new classification ({privacy}): "),
                    validator=numeric_validator,
                )
                chosen_privacy = data_store.add_to_privacies(privacy, level, change_id)
        else:
            chosen_privacy = self.resolve_reference(
                data_store,
                change_id,
                data_type=f"Datafile named '{datafile_name}'",
                db_class=data_store.db_classes.Privacy,
                field_name="privacy",
                text_name="classification",
                help_id=constants.RESOLVE_PRIVACY,
                search_help_id=constants.FUZZY_SEARCH_PRIVACY,
            )

        if chosen_privacy is None:
            print("Quitting")
            sys.exit(1)

        while True:
            print("-" * 60)
            print("Input complete. About to create this datafile:")
            print(f"Name: {datafile_name}")
            print(f"Type: {chosen_datafile_type.name}")
            print(f"Classification: {chosen_privacy.name}")

            choice = create_menu(
                "Create this datafile?: ",
                ["Yes", "No, make further edits"],
                validate_method=is_valid,
            )

            if choice in ["?", "HELP"]:
                print_help_text(data_store, constants.RESOLVE_DATAFILE)
            else:
                break
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
        print_new_section_title("Resolve Platform")
        platform_details = []
        final_options = ["Add a new platform", "Search for existing platform"]
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
                    f"Select: {platform.name} / {platform.identifier} / {platform.nationality_name}"
                )
        choices = final_options + platform_details

        def is_valid_dynamic(option):  # pragma: no cover
            return option in [str(i) for i in range(1, len(choices) + 1)] + [".", "?", "HELP"]

        choice = create_menu(
            f"Select a platform entry for {platform_name}:",
            choices,
            validate_method=is_valid_dynamic,
        )
        if choice == ".":
            print("Quitting")
            sys.exit(1)
        elif choice in ["?", "HELP"]:
            print_help_text(data_store, constants.RESOLVE_PLATFORM)
            return self.resolve_platform(
                data_store, platform_name, platform_type, nationality, privacy, change_id
            )
        elif choice == str(1):
            return self.add_to_platforms(
                data_store,
                platform_name,
                platform_type,
                nationality,
                privacy,
                change_id,
            )
        elif choice == str(2):
            return self.fuzzy_search_platform(
                data_store,
                platform_name,
                platform_type,
                nationality,
                privacy,
                change_id,
            )
        elif 3 <= int(choice) <= len(choices):
            # One of the pre-existing platforms was chosen
            platform_index = int(choice) - 3
            return platforms[platform_index]

    def resolve_sensor(self, data_store, sensor_name, sensor_type, host_id, privacy, change_id):
        print_new_section_title("Resolve Sensor")
        Platform = data_store.db_classes.Platform
        host_platform = (
            data_store.session.query(Platform).filter(Platform.platform_id == host_id).first()
        )
        if not host_platform:
            print("Invalid platform id specified")
            print("Quitting")
            sys.exit(1)

        objects = (
            data_store.session.query(data_store.db_classes.Sensor)
            .filter(data_store.db_classes.Sensor.host == host_id)
            .all()
        )
        if len(objects) == 0:
            # No sensors for this platform, so no point asking to search
            options = ["Add a new sensor"]
            search_option = 0  # Invalid option number, as search not available in this situation
            add_option = 1
            other_options_base = 2
        else:
            add_option = 1
            search_option = 2
            other_options_base = 3
            options = [
                "Add a new sensor",
                f"Search for existing sensor on platform '{host_platform.name}'",
            ]

            objects_dict = {f"Select: {obj.name}": obj for obj in objects}
            if len(objects_dict) <= 7:
                options.extend(objects_dict)

        if sensor_name:
            prompt = f"Sensor '{sensor_name}' on platform '{host_platform.name}' not found. Do you wish to: "
        else:
            prompt = f"Sensor on platform '{host_platform.name}' not found. Do you wish to: "

        def is_valid_dynamic(option):  # pragma: no cover
            return option in [str(i) for i in range(1, len(options) + 1)] + [".", "?", "HELP"]

        choice = create_menu(prompt, options, validate_method=is_valid_dynamic)
        if choice == ".":
            print("Quitting")
            sys.exit(1)
        elif choice in ["?", "HELP"]:
            print_help_text(data_store, constants.RESOLVE_SENSOR)
            return self.resolve_sensor(
                data_store, sensor_name, sensor_type, host_id, privacy, change_id
            )
        elif choice == str(search_option):
            return self.fuzzy_search_sensor(
                data_store, sensor_name, sensor_type, host_platform.platform_id, privacy, change_id
            )
        elif choice == str(add_option):
            return self.add_to_sensors(
                data_store, sensor_name, sensor_type, host_id, privacy, change_id
            )
        elif other_options_base <= int(choice) <= len(options):
            selected_object = objects_dict[options[int(choice) - 1]]
            if selected_object:
                # add sensor name and the selected sensor to sensor cache
                data_store._sensor_cache[(sensor_name, host_platform.platform_id)] = selected_object
                return selected_object

    def resolve_reference(
        self,
        data_store,
        change_id,
        data_type,
        db_class,
        field_name,
        help_id,
        search_help_id,
        text_name=None,
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
        :param help_id: Integer ID of the help text for resolve reference
        :type help_id: Integer
        :param search_help_id: Integer ID of the help text for fuzzy search reference
        :type search_help_id: Integer
        :return:
        """
        if text_name is None:
            text_name = field_name.replace("_", "-")
        options = [f"Search an existing {text_name}"]
        title = f"Ok, please provide {text_name} for new {data_type}: "
        current_values = ""
        if db_class.__tablename__ == NATIONALITY:
            objects = (
                data_store.session.query(db_class)
                .filter(db_class.priority.in_([1, 2]))
                .order_by(db_class.priority, db_class.name)
                .all()
            )
        elif db_class.__tablename__ == PRIVACY:
            all_values = data_store.session.query(db_class).order_by(db_class.level).all()
            objects = all_values[:8]
            current_values = "\nCurrent Privacies in the Database\n"
            headers = ["name", "level"]
            current_values += tabulate(
                [[str(getattr(row, column)) for column in headers] for row in all_values],
                headers=headers,
                tablefmt="grid",
                floatfmt=".3f",
            )
            current_values += "\n"
        else:
            objects = data_store.session.query(db_class).limit(8).all()
        objects_dict = {f"Select: {obj.name}": obj for obj in objects}
        options.extend(objects_dict)

        def is_valid_dynamic(option):  # pragma: no cover
            return option in [str(i) for i in range(1, len(options) + 1)] + [".", "?", "HELP"]

        choice = create_menu(
            title,
            options,
            validate_method=is_valid_dynamic,
            cancel=f"import (Please contact an expert user if you need a new {text_name} to be added)",
        )
        if choice == ".":
            print("-" * 60, "\nReturning to the previous menu\n")
            return None
        elif choice in ["?", "HELP"]:
            print_help_text(data_store, help_id)
            return self.resolve_reference(
                data_store=data_store,
                change_id=change_id,
                data_type=data_type,
                db_class=db_class,
                field_name=field_name,
                help_id=help_id,
                search_help_id=search_help_id,
                text_name=text_name,
            )
        # elif choice == ",":
        #     return constants.ASK_PREVIOUS
        elif choice == str(1):
            result = self.fuzzy_search_reference(
                data_store=data_store,
                change_id=change_id,
                data_type=data_type,
                db_class=db_class,
                field_name=field_name,
                help_id=help_id,
                search_help_id=search_help_id,
                text_name=text_name,
            )
            if result is None:
                return self.resolve_reference(
                    data_store=data_store,
                    change_id=change_id,
                    data_type=data_type,
                    db_class=db_class,
                    field_name=field_name,
                    help_id=help_id,
                    search_help_id=search_help_id,
                    text_name=text_name,
                )
            else:
                return result
        elif 2 <= int(choice) <= len(options):
            selected_object = objects_dict[options[int(choice) - 1]]
            if selected_object:
                return selected_object

    def fuzzy_search_reference(
        self,
        data_store,
        change_id,
        data_type,
        db_class,
        field_name,
        help_id,
        search_help_id,
        text_name=None,
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
        :param help_id: Integer ID of the help text for resolve reference
        :type help_id: Integer
        :param search_help_id: Integer ID of the help text for fuzzy search reference
        :type search_help_id: Integer
        :return:
        """
        objects = data_store.session.query(db_class).all()
        completer = [p.name for p in objects]

        def is_valid_reference(option):  # pragma: no cover
            return option in completer + ["."]

        choice = create_menu(
            "Please start typing to show suggested values",
            cancel=f"{text_name} search",
            choices=[],
            completer=get_fuzzy_completer(completer),
            validate_method=is_valid_reference,
        )
        if choice == ".":
            print("-" * 60, "\nReturning to the previous menu\n")
            return None
        elif choice in ["?", "HELP"]:
            print_help_text(data_store, search_help_id)
            return self.fuzzy_search_reference(
                data_store=data_store,
                change_id=change_id,
                data_type=data_type,
                db_class=db_class,
                field_name=field_name,
                help_id=help_id,
                search_help_id=search_help_id,
                text_name=text_name,
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
            values = list()
            values.append(platform.name)
            if platform.trigraph:
                values.append(platform.trigraph)
            if platform.quadgraph:
                values.append(platform.quadgraph)
            synonym = (
                data_store.session.query(data_store.db_classes.Synonym)
                .filter(
                    data_store.db_classes.Synonym.table == PLATFORM,
                    data_store.db_classes.Synonym.entity == platform.platform_id,
                )
                .all()
            )
            if synonym:
                synonym_names = [s.synonym for s in synonym]
                values.append(",".join(synonym_names))

            values.append(platform.identifier)
            values.append(platform.nationality_name)
            line = " / ".join(values)
            completer.append(line)
        choice = create_menu(
            "Please start typing to show suggested values",
            cancel="platform search",
            choices=[],
            completer=get_fuzzy_completer(completer),
        )
        if choice in ["?", "HELP"]:
            print_help_text(data_store, constants.FUZZY_SEARCH_PLATFORM)
            return self.fuzzy_search_platform(
                data_store,
                platform_name,
                platform_type,
                nationality,
                privacy,
                change_id,
            )
        elif choice in completer:
            # Extract the platform details from the string
            platform_details = choice.split(" / ")
            name, identifier, nationality = (
                platform_details[0],
                platform_details[-2],
                platform_details[-1],
            )
            # Get the platform from the database
            platform = (
                data_store.session.query(data_store.db_classes.Platform)
                .filter(data_store.db_classes.Platform.name == name)
                .filter(data_store.db_classes.Platform.identifier == identifier)
                .filter(data_store.db_classes.Platform.nationality_name == nationality)
                .first()
            )
            # If we've been given a platform name, then we might want to link
            # that platform name to the one we've picked, as a synonym
            if platform_name:
                while True:
                    new_choice = create_menu(
                        f"Do you wish to keep {platform_name} as synonym for {choice}?\n",
                        ["Yes", "No"],
                        validate_method=is_valid,
                    )
                    if new_choice in ["?", "HELP"]:
                        print_help_text(data_store, constants.KEEP_PLATFORM_AS_SYNONYM)
                    else:
                        break
                if new_choice == str(1):
                    # Add it to synonyms and return existing platform
                    data_store.add_to_synonyms(
                        PLATFORM, platform_name, platform.platform_id, change_id
                    )
                    print(f"'{platform_name}' added to Synonyms!")
                    return platform
                elif new_choice == str(2):
                    return platform
                elif new_choice == ".":
                    print("-" * 60, "\nReturning to the previous menu\n")
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
            print("-" * 60, "\nReturning to the previous menu\n")
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
        if choice in ["?", "HELP"]:
            print_help_text(data_store, constants.FUZZY_SEARCH_SENSOR)
            return self.fuzzy_search_sensor(
                data_store, sensor_name, sensor_type, host_id, privacy, change_id
            )
        elif choice == ".":
            print("-" * 60, "\nReturning to the previous menu\n")
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

    def ask_platform_question(self, index, default=None):
        func, params, _ = self.platform_questions_responses[index]
        if default:
            params.update({"default": default})
            self.platform_questions_responses[index][2] = default
        new_response = func(**params)
        if isinstance(new_response, str):
            new_response = new_response.strip()

        if new_response in ["?", "HELP"]:
            return new_response
        elif self.validate_response(new_response, index):
            self.platform_questions_responses[index][2] = new_response
            return new_response
        else:
            _, return_func, return_params = self.validation_dict[index]
            return_func(*return_params)

    def create_platform_questions_dict(
        self, data_store, platform_name, platform_type, nationality, privacy, change_id
    ):
        self.platform_questions_responses = dict()
        if platform_name is None:
            platform_name = ""
        self.platform_questions_responses[constants.PLATFORM_NAME] = [
            prompt,
            {"message": format_command("Please enter a name: "), "default": platform_name},
            platform_name,
        ]
        self.platform_questions_responses[constants.PLATFORM_IDENTIFIER] = [
            prompt,
            {"message": format_command("Please enter identifier (pennant or tail number): ")},
            None,
        ]
        if platform_name and len(platform_name) >= 3:
            trigraph = platform_name[:3]
        else:
            trigraph = ""
        self.platform_questions_responses[constants.PLATFORM_TRIGRAPH] = [
            prompt,
            {"message": format_command("Please enter trigraph (optional): "), "default": trigraph},
            trigraph,
        ]
        if platform_name and len(platform_name) >= 4:
            quadgraph = platform_name[:4]
        else:
            quadgraph = ""
        self.platform_questions_responses[constants.PLATFORM_QUADGRAPH] = [
            prompt,
            {
                "message": format_command("Please enter quadgraph (optional): "),
                "default": quadgraph,
            },
            quadgraph,
        ]
        if not nationality:
            self.platform_questions_responses[constants.RESOLVE_NATIONALITY] = [
                self.resolve_reference,
                {
                    "data_store": data_store,
                    "change_id": change_id,
                    "data_type": "Platform",
                    "db_class": data_store.db_classes.Nationality,
                    "field_name": "nationality",
                    "help_id": constants.RESOLVE_NATIONALITY,
                    "search_help_id": constants.FUZZY_SEARCH_NATIONALITY,
                },
                None,
            ]
        if not platform_type:
            self.platform_questions_responses[constants.RESOLVE_PLATFORM_TYPE] = [
                self.resolve_reference,
                {
                    "data_store": data_store,
                    "change_id": change_id,
                    "data_type": "Platform",
                    "db_class": data_store.db_classes.PlatformType,
                    "field_name": "platform_type",
                    "help_id": constants.RESOLVE_PLATFORM_TYPE,
                    "search_help_id": constants.FUZZY_SEARCH_PLATFORM_TYPE,
                },
                None,
            ]
        if not privacy:
            self.platform_questions_responses[constants.RESOLVE_PRIVACY] = [
                self.resolve_reference,
                {
                    "data_store": data_store,
                    "change_id": change_id,
                    "data_type": "Platform",
                    "text_name": "classification",
                    "db_class": data_store.db_classes.Privacy,
                    "field_name": "privacy",
                    "help_id": constants.RESOLVE_PRIVACY,
                    "search_help_id": constants.FUZZY_SEARCH_PRIVACY,
                },
                None,
            ]
        self.platform_questions_order = list(self.platform_questions_responses.keys())

    def create_platform_validation_dict(
        self, data_store, platform_name, platform_type, nationality, privacy, change_id
    ):
        self.validation_dict = dict()
        self.validation_dict[constants.PLATFORM_NAME] = (
            self.validate_platform_name,
            self.add_to_platforms,
            [data_store, platform_name, platform_type, nationality, privacy, change_id],
        )
        self.validation_dict[constants.PLATFORM_IDENTIFIER] = (
            self.validate_platform_identifier,
            self.add_to_platforms,
            [data_store, platform_name, platform_type, nationality, privacy, change_id],
        )
        self.validation_dict[constants.PLATFORM_TRIGRAPH] = (
            self.validate_platform_trigraph,
            self.add_to_platforms,
            [data_store, platform_name, platform_type, nationality, privacy, change_id],
        )
        self.validation_dict[constants.PLATFORM_QUADGRAPH] = (
            self.validate_platform_quadgraph,
            self.add_to_platforms,
            [data_store, platform_name, platform_type, nationality, privacy, change_id],
        )
        self.validation_dict[constants.RESOLVE_NATIONALITY] = (
            self.validate_nationality,
            self.resolve_platform,
            [data_store, platform_name, None, None, None, change_id],
        )
        self.validation_dict[constants.RESOLVE_PLATFORM_TYPE] = (
            self.validate_platform_type,
            self.resolve_platform,
            [data_store, platform_name, None, None, None, change_id],
        )
        self.validation_dict[constants.RESOLVE_PRIVACY] = (
            self.validate_privacy,
            self.resolve_platform,
            [data_store, platform_name, None, None, None, change_id],
        )

    def validate_response(self, new_response, index):
        func, _, _ = self.validation_dict[index]
        return func(new_response)

    @staticmethod
    def validate_platform_name(platform_name):
        if not platform_name or platform_name == "":
            return False
        if len(platform_name) > 150:
            print(
                "Platform name too long, maximum length 150 characters. Restarting platform data entry."
            )
            return False
        return True

    @staticmethod
    def validate_platform_identifier(identifier):
        if len(identifier) > 10:
            print(
                "Identifier too long, maximum length 10 characters. Restarting platform data entry."
            )
            return False
        if not identifier or identifier == "":
            return False
        return True

    @staticmethod
    def validate_platform_trigraph(trigraph):
        if len(trigraph) > 3:
            print("Trigraph too long, maximum length 3 characters. Restarting platform data entry.")
            return False
        return True

    @staticmethod
    def validate_platform_quadgraph(quadgraph):
        if len(quadgraph) > 4:
            print(
                "Quadgraph too long, maximum length 4 characters. Restarting platform data entry."
            )
            return False
        return True

    @staticmethod
    def validate_nationality(nationality):
        if not nationality:
            print("Nationality couldn't resolved. Returning to the previous menu!")
            return False
        return True

    @staticmethod
    def validate_platform_type(platform_type):
        if not platform_type:
            print("Platform Type couldn't resolved. Returning to the previous menu!")
            return False
        return True

    @staticmethod
    def validate_privacy(privacy):
        if not privacy:
            print("Classification couldn't resolved. Returning to the previous menu!")
            return False
        return True

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
        self.create_platform_questions_dict(
            data_store, platform_name, platform_type, nationality, privacy, change_id
        )
        self.create_platform_validation_dict(
            data_store, platform_name, platform_type, nationality, privacy, change_id
        )
        print("Ok, adding new platform.")
        platform_name = self.ask_platform_question(constants.PLATFORM_NAME)
        while True:
            response = self.ask_platform_question(constants.PLATFORM_IDENTIFIER)
            if not response:
                _, return_func, return_params = self.validation_dict[constants.PLATFORM_IDENTIFIER]
                return return_func(*return_params)
            else:
                identifier = response
            if identifier in ["?", "HELP"]:
                print_help_text(data_store, constants.PLATFORM_IDENTIFIER)
            # elif identifier == ",":
            #     self.ask_platform_question(constants.PLATFORM_NAME)
            else:
                break
        while True:
            trigraph = self.ask_platform_question(
                constants.PLATFORM_TRIGRAPH, default=platform_name[:3]
            )
            if trigraph in ["?", "HELP"]:
                print_help_text(data_store, constants.PLATFORM_TRIGRAPH)
            # elif trigraph == ",":
            #     self.ask_platform_question(constants.PLATFORM_IDENTIFIER)
            else:
                break
        while True:
            quadgraph = self.ask_platform_question(
                constants.PLATFORM_QUADGRAPH, default=platform_name[:4]
            )
            if quadgraph in ["?", "HELP"]:
                print_help_text(data_store, constants.PLATFORM_QUADGRAPH)
            # elif quadgraph == ",":
            #     self.ask_platform_question(constants.PLATFORM_TRIGRAPH)
            else:
                break

        # Choose Nationality
        if nationality:
            chosen_nationality = data_store.add_to_nationalities(nationality, change_id)
        else:
            chosen_nationality = self.ask_platform_question(constants.RESOLVE_NATIONALITY)
            # if isinstance(chosen_nationality, str) and chosen_nationality == constants.ASK_PREVIOUS:
            #     self.ask_platform_question(constants.PLATFORM_QUADGRAPH)
        # Choose Platform Type
        if platform_type:
            chosen_platform_type = data_store.add_to_platform_types(platform_type, change_id)
        else:
            chosen_platform_type = self.ask_platform_question(constants.RESOLVE_PLATFORM_TYPE)
            # if (
            #     isinstance(chosen_platform_type, str)
            #     and chosen_platform_type == constants.ASK_PREVIOUS
            # ):
            #     self.ask_platform_question(constants.RESOLVE_NATIONALITY)
        # Choose Privacy
        if privacy:
            chosen_privacy = data_store.search_privacy(privacy)
            if chosen_privacy is None:
                level = prompt(
                    format_command(f"Please type level of new classification ({privacy}): "),
                    validator=numeric_validator,
                )
                chosen_privacy = data_store.add_to_privacies(privacy, level, change_id)
        else:
            chosen_privacy = self.ask_platform_question(constants.RESOLVE_PRIVACY)
            # if isinstance(chosen_privacy, str) and chosen_privacy == constants.ASK_PREVIOUS:
            #     self.ask_platform_question(constants.RESOLVE_PLATFORM_TYPE)

        def is_valid_choice(option):  # pragma: no cover
            return option in [str(1), str(2), str(3), ".", "?", "HELP"]

        while True:
            print("-" * 60)
            print("Input complete. About to create this platform:")
            print(f"Name: {platform_name}")
            print(f"Trigraph: {trigraph}")
            print(f"Quadgraph: {quadgraph}")
            print(f"Identifier: {identifier}")
            print(f"Nationality: {chosen_nationality.name}")
            print(f"Platform type: {chosen_platform_type.name}")
            print(f"Classification: {chosen_privacy.name}")

            choice = create_menu(
                "Create this platform?: ",
                ["Yes", "No, make further edits", "No, restart platform selection process"],
                validate_method=is_valid_choice,
            )
            if choice in ["?", "HELP"]:
                print_help_text(data_store, constants.ADD_TO_PLATFORMS)
            else:
                break

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
        elif choice == str(3):
            return self.resolve_platform(data_store, platform_name, None, None, None, change_id)
        elif choice == ".":
            print("-" * 60, "\nReturning to the previous menu\n")
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

        sensor_name = prompt(format_command("Please enter a name: "), default=sensor_name).strip()

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
                help_id=constants.RESOLVE_SENSOR_TYPE,
                search_help_id=constants.FUZZY_SEARCH_SENSOR_TYPE,
            )

        if sensor_type is None:
            print("Sensor Type couldn't resolved. Returning to the previous menu!")
            return self.resolve_sensor(data_store, sensor_name, None, host_id, None, change_id)

        if privacy:
            chosen_privacy = data_store.search_privacy(privacy)
            if chosen_privacy is None:
                level = prompt(
                    format_command(f"Please type level of new classification ({privacy}): "),
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
                help_id=constants.RESOLVE_PRIVACY,
                search_help_id=constants.FUZZY_SEARCH_PRIVACY,
            )

        if chosen_privacy is None:
            print("Classification couldn't resolved. Returning to the previous menu!")
            return self.resolve_sensor(data_store, sensor_name, None, host_id, None, change_id)

        def is_valid_choice(option):  # pragma: no cover
            return option in [str(1), str(2), str(3), ".", "?", "HELP"]

        while True:
            print("-" * 60)
            print("Input complete. About to create this sensor:")
            print(f"Name: {sensor_name}")
            print(f"Type: {sensor_type.name}")
            print(f"Classification: {chosen_privacy.name}")

            choice = create_menu(
                "Create this sensor?: ",
                ["Yes", "No, make further edits", "No, restart sensor selection process"],
                validate_method=is_valid_choice,
            )
            if choice in ["?", "HELP"]:
                print_help_text(data_store, constants.ADD_TO_SENSORS)
            else:
                break

        if choice == str(1):
            return sensor_name, sensor_type, chosen_privacy
        elif choice == str(2):
            return self.add_to_sensors(data_store, sensor_name, None, host_id, None, change_id)
        elif choice == str(3):
            return self.resolve_sensor(data_store, sensor_name, None, host_id, None, change_id)
        elif choice == ".":
            print("-" * 60, "\nReturning to the previous menu\n")
            return self.resolve_sensor(data_store, sensor_name, None, host_id, None, change_id)
