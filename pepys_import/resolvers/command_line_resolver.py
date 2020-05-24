import re
import sys

from prompt_toolkit import prompt
from prompt_toolkit.completion import FuzzyWordCompleter
from sqlalchemy import or_

from pepys_import.core.store import constants
from pepys_import.resolvers.command_line_input import create_menu, is_valid
from pepys_import.resolvers.data_resolver import DataResolver


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
        :type change_id: Integer or UUID
        :return:
        """
        print("Ok, adding new datafile.")

        datafile_name = prompt("Please enter a name: ", default=datafile_name)
        # Choose Datafile Type
        if datafile_type:
            chosen_datafile_type = data_store.add_to_datafile_types(datafile_type, change_id)
        else:
            chosen_datafile_type = self.resolve_reference(
                data_store,
                change_id,
                data_type="Datafile",
                text_name="datafile-type",
                db_class=data_store.db_classes.DatafileType,
                field_name="datafile_type",
            )

        if chosen_datafile_type is None:
            print("Quitting")
            sys.exit(1)

        # Choose Privacy
        if privacy:
            chosen_privacy = data_store.add_to_privacies(privacy, change_id)
        else:
            chosen_privacy = self.resolve_reference(
                data_store,
                change_id,
                data_type="Datafile",
                text_name="classification",
                db_class=data_store.db_classes.Privacy,
                field_name="privacy",
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
            "Create this datafile?: ", ["Yes", "No, make further edits"], validate_method=is_valid,
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
        options = [f"Search for existing platform", f"Add a new platform"]
        if platform_name:
            options[1] += f", default name '{platform_name}'"
        choice = create_menu(
            f"Platform '{platform_name}' not found. Do you wish to: ",
            options,
            validate_method=is_valid,
        )

        if choice == str(1):
            return self.fuzzy_search_platform(
                data_store, platform_name, platform_type, nationality, privacy, change_id,
            )
        elif choice == str(2):
            return self.add_to_platforms(
                data_store, platform_name, platform_type, nationality, privacy, change_id,
            )
        elif choice == ".":
            print("Quitting")
            sys.exit(1)

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
            f"Add a new sensor",
        ]
        if sensor_name:
            options[1] += f", default name '{sensor_name}'"
            prompt = f"Sensor '{sensor_name}' on platform '{host_platform.name}' not found. Do you wish to: "
        else:
            prompt = f"Sensor on platform '{host_platform.name}' not found. Do you wish to: "
        choice = create_menu(prompt, options, validate_method=is_valid,)

        if choice == str(1):
            return self.fuzzy_search_sensor(
                data_store, sensor_name, sensor_type, host_platform.platform_id, privacy, change_id
            )
        elif choice == str(2):
            return self.add_to_sensors(
                data_store, sensor_name, sensor_type, host_id, privacy, change_id
            )
        elif choice == ".":
            print("Quitting")
            sys.exit(1)

    def resolve_reference(
        self, data_store, change_id, data_type, text_name, db_class, field_name,
    ):
        options = [f"Search an existing {text_name}", f"Add a new {text_name}"]
        objects = data_store.session.query(db_class).all()
        objects_dict = {obj.name: obj for obj in objects}
        data_store.session.expunge_all()
        plural_field = (
            re.sub("([A-Z][a-z]+)", r" \1", re.sub("([A-Z]+)", r"\1", db_class.__tablename__))
            .strip()
            .lower()
            .replace(" ", "_")
        )
        if len(objects_dict) <= 7:
            options.extend(objects_dict)
        choice = create_menu(f"Ok, please provide {text_name} for new {data_type}: ", options,)

        if choice == ".":
            print("-" * 61, "\nReturning to the previous menu\n")
            return None
        elif choice == str(1):
            result = self.fuzzy_search_reference(
                data_store, change_id, data_type, text_name, db_class, field_name
            )
            if result is None:
                return self.resolve_reference(
                    data_store, change_id, data_type, text_name, db_class, field_name
                )
            else:
                return result
        elif choice == str(2):
            new_object = prompt(f"Please type name of new {text_name}: ")
            search_method = getattr(data_store, f"search_{field_name}")
            obj = search_method(new_object)
            if obj:
                return obj
            elif new_object:
                add_method = getattr(data_store, f"add_to_{plural_field}")
                return add_method(new_object, change_id)
            else:
                print("You haven't entered an input!")
                return self.resolve_reference(
                    data_store, change_id, data_type, text_name, db_class, field_name
                )
        elif 3 <= int(choice) <= len(options):
            selected_object = objects_dict[options[int(choice) - 1]]
            if selected_object:
                return selected_object

    def fuzzy_search_reference(
        self, data_store, change_id, data_type, text_name, db_class, field_name
    ):

        objects = data_store.session.query(db_class).all()
        completer = [p.name for p in objects]
        choice = create_menu(
            "Please start typing to show suggested values",
            cancel=f"{text_name} search",
            choices=[],
            completer=FuzzyWordCompleter(completer),
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
                return data_store.add_to_privacies(choice, change_id)
            elif new_choice == str(2):
                return self.fuzzy_search_reference(
                    data_store, change_id, data_type, text_name, db_class, field_name
                )
            elif new_choice == ".":
                print("-" * 61, "\nReturning to the previous menu\n")
                return self.resolve_reference(
                    data_store, change_id, data_type, text_name, db_class, field_name,
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
        :type change_id: Integer or UUID
        :return:
        """
        completer = list()
        platforms = data_store.session.query(data_store.db_classes.Platform).all()
        for platform in platforms:
            completer.append(platform.name)
            if platform.trigraph:
                completer.append(platform.trigraph)
            if platform.quadgraph:
                completer.append(platform.quadgraph)
        choice = create_menu(
            "Please start typing to show suggested values",
            cancel="platform search",
            choices=[],
            completer=FuzzyWordCompleter(completer),
        )
        if platform_name and choice in completer:
            new_choice = create_menu(
                f"Do you wish to keep {platform_name} as synonym for {choice}?",
                ["Yes", "No"],
                validate_method=is_valid,
            )
            if new_choice == str(1):
                platform = (
                    data_store.session.query(data_store.db_classes.Platform)
                    .filter(
                        or_(
                            data_store.db_classes.Platform.name == choice,
                            data_store.db_classes.Platform.trigraph == choice,
                            data_store.db_classes.Platform.quadgraph == choice,
                        )
                    )
                    .first()
                )
                # Add it to synonyms and return existing platform
                data_store.add_to_synonyms(
                    constants.PLATFORM, platform_name, platform.platform_id, change_id
                )
                print(f"'{platform_name}' added to Synonyms!")
                return platform
            elif new_choice == str(2):
                return self.add_to_platforms(
                    data_store, platform_name, platform_type, nationality, privacy, change_id,
                )
            elif new_choice == ".":
                print("-" * 61, "\nReturning to the previous menu\n")
                return self.fuzzy_search_platform(
                    data_store, platform_name, platform_type, nationality, privacy, change_id,
                )
        elif choice == ".":
            print("-" * 61, "\nReturning to the previous menu\n")
            return self.resolve_platform(
                data_store, platform_name, nationality, platform_type, privacy, change_id,
            )
        elif choice not in completer:
            print(f"'{choice}' could not found! Redirecting to adding a new platform..")
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
        :type change_id: Integer or UUID
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
            completer=FuzzyWordCompleter(completer),
        )
        if sensor_name and choice in completer:
            new_choice = create_menu(
                f"Do you wish to keep {sensor_name} as synonym for {choice}?",
                ["Yes", "No"],
                validate_method=is_valid,
            )
            if new_choice == str(1):
                sensor = (
                    data_store.session.query(data_store.db_classes.Sensor)
                    .filter(data_store.db_classes.Sensor.name == choice)
                    .first()
                )
                # Add it to synonyms and return existing sensor
                data_store.add_to_synonyms(
                    constants.SENSOR, sensor_name, sensor.sensor_id, change_id
                )
                print(f"'{sensor_name}' added to Synonyms!")
                return sensor
            elif new_choice == str(2):
                return self.add_to_sensors(
                    data_store, sensor_name, sensor_type, host_id, privacy, change_id
                )
            elif new_choice == ".":
                print("-" * 61, "\nReturning to the previous menu\n")
                return self.fuzzy_search_sensor(
                    data_store, sensor_name, sensor_type, host_id, privacy, change_id
                )
        elif choice == ".":
            print("-" * 61, "\nReturning to the previous menu\n")
            return self.resolve_sensor(
                data_store, sensor_name, sensor_type, host_id, privacy, change_id
            )
        elif choice not in completer:
            print(f"'{choice}' could not found! Redirecting to adding a new sensor..")
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
        :param platform_name: Name of :class:`Platform`
        :type platform_name: String
        :param nationality: Name of :class:`Nationality`
        :type nationality: Nationality
        :param platform_type: Name of :class:`PlatformType`
        :type platform_type: PlatformType
        :param privacy: Name of :class:`Privacy`
        :type privacy: Privacy
        :param change_id: ID of the :class:`Change` object
        :type change_id: Integer or UUID
        :return:
        """
        print("Ok, adding new platform.")
        if platform_name:
            platform_name = prompt("Please enter a name: ", default=platform_name)
            trigraph = None
            if len(platform_name) >= 3:
                trigraph = prompt("Please enter trigraph (optional): ", default=platform_name[:3])
            quadgraph = None
            if len(platform_name) >= 4:
                quadgraph = prompt("Please enter quadgraph (optional): ", default=platform_name[:4])
        else:
            platform_name = prompt("Please enter a name: ")
            trigraph = prompt("Please enter trigraph (optional): ")
            quadgraph = prompt("Please enter quadgraph (optional): ")
        pennant_number = prompt("Please enter pennant number (optional): ")

        # Choose Nationality
        if nationality:
            chosen_nationality = data_store.add_to_nationalities(nationality, change_id)
        else:
            chosen_nationality = self.resolve_reference(
                data_store,
                change_id,
                data_type="Platform",
                text_name="nationality",
                db_class=data_store.db_classes.Nationality,
                field_name="nationality",
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
                text_name="platform-type",
                db_class=data_store.db_classes.PlatformType,
                field_name="platform_type",
            )

        if chosen_platform_type is None:
            print("Platform Type couldn't resolved. Returning to the previous menu!")
            return self.resolve_platform(data_store, platform_name, None, None, None, change_id)

        # Choose Privacy
        if privacy:
            chosen_privacy = data_store.add_to_privacies(privacy, change_id)
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
        if trigraph:
            print(f"Trigraph: {trigraph}")
        if quadgraph:
            print(f"Quadgraph: {quadgraph}")
        print(f"Pennant Number: {pennant_number}")
        print(f"Nationality: {chosen_nationality.name}")
        print(f"Class: {chosen_platform_type.name}")
        print(f"Classification: {chosen_privacy.name}")

        choice = create_menu(
            "Create this platform?: ", ["Yes", "No, make further edits"], validate_method=is_valid,
        )

        if choice == str(1):
            return (
                platform_name,
                trigraph,
                quadgraph,
                pennant_number,
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
        :type change_id: Integer or UUID
        :return:
        """
        # Choose Sensor Type
        print("Ok, adding new sensor.")

        # Can't pass None to prompt function below, so pass empty string instead
        if sensor_name is None:
            sensor_name = ""

        sensor_name = prompt("Please enter a name: ", default=sensor_name)
        if sensor_type:
            sensor_type = data_store.add_to_sensor_types(sensor_type, change_id)
        else:
            sensor_type = self.resolve_reference(
                data_store,
                change_id,
                data_type="Sensor",
                text_name="sensor-type",
                db_class=data_store.db_classes.SensorType,
                field_name="sensor_type",
            )

        if sensor_type is None:
            print("Sensor Type couldn't resolved. Returning to the previous menu!")
            return self.resolve_sensor(data_store, sensor_name, None, host_id, None, change_id)

        if privacy:
            privacy = data_store.add_to_privacies(privacy, change_id)
        else:
            privacy = self.resolve_reference(
                data_store,
                change_id,
                data_type="Sensor",
                text_name="classification",
                db_class=data_store.db_classes.Privacy,
                field_name="privacy",
            )

        if privacy is None:
            print("Classification couldn't resolved. Returning to the previous menu!")
            return self.resolve_sensor(data_store, sensor_name, None, host_id, None, change_id)

        print("-" * 61)
        print("Input complete. About to create this sensor:")
        print(f"Name: {sensor_name}")
        print(f"Type: {sensor_type.name}")
        print(f"Classification: {privacy.name}")

        choice = create_menu(
            "Create this sensor?: ", ["Yes", "No, make further edits"], validate_method=is_valid,
        )

        if choice == str(1):
            return sensor_name, sensor_type, privacy
        elif choice == str(2):
            return self.add_to_sensors(data_store, sensor_name, None, host_id, None, change_id)
        elif choice == ".":
            print("-" * 61, "\nReturning to the previous menu\n")
            return self.resolve_sensor(data_store, sensor_name, None, host_id, None, change_id)

    def resolve_privacy(self, data_store, change_id, data_type):
        pass
