import sys
from .data_resolver import DataResolver
from .command_line_input import get_choice_input


class CommandLineResolver(DataResolver):
    def __init__(self):
        self.table_privacies = {}

    def synonym_search(self, data_store, platform_name):
        input_ = input("Please type word stem to search for: ")
        result = data_store.searchPlatform(input_)
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

    # TODO: be sure it works with new method names
    #  (addToTable and addToTableFromREPL)
    # TODO: privacy_id added to Platform. Resolver must be modified for that
    def add_to_platforms(self, data_store, platform_name):
        print("Ok, adding new platform.")

        # Choose Nationality
        nationalities = data_store.getNationalities()
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
                nationality_check_ok = data_store.checkNationality(new_input)
            chosen_nationality = data_store.addToNationalities(new_input)
        else:
            chosen_nationality = nationalities[choice - 2]

        # Choose Platform Type
        platform_types = data_store.getPlatformTypes()
        platform_type_names = [c.name for c in platform_types]
        platform_type_names.append("Add a new class")
        platform_type_names.append("Cancel import")
        choice = get_choice_input("Ok, please provide class: ", platform_type_names)
        if choice == len(platform_type_names):
            print("Quitting")
            sys.exit(1)
        elif choice == len(platform_type_names) - 1:
            platform_type_ok = False
            while not platform_type_ok:
                new_input = input("Please type name of new class: ")
                platform_type_ok = data_store.checkPlatformType(new_input)
            chosen_platform_type = data_store.addToPlatformTypes(new_input)
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
        privacies = data_store.getPrivacies()
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
                privacy_check_ok = data_store.checkPrivacy(new_input)
            chosen_privacy = data_store.addToPrivacies(new_input)
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
            return platform_name, chosen_platform_type, chosen_nationality
        elif choice == 2:
            return self.addToPlatformsFromREPL(data_store, platform_name)
        elif choice == 3:
            print("Quitting")
            sys.exit(1)

    def resolve_platform(self, data_store, platform_name):
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
            return self.addToPlatforms(data_store, platform_name)
        else:
            print("Quitting")
            sys.exit(1)

    def add_to_sensors(self, data_store, sensorName):
        # Choose Sensor Type
        print("Ok, adding new sensor.")
        sensor_types = data_store.getSensorTypes()
        sensor_type_names = [st.name for st in sensor_types]
        sensor_type_names.append("Add a new sensor type")
        sensor_type_names.append("Cancel import")
        choice = get_choice_input("Please provide sensor type: ", sensor_type_names)
        if choice == len(sensor_type_names):
            print("Quitting")
            sys.exit(1)
        elif choice == len(sensor_type_names) - 1:
            sensor_type_check_ok = False
            while not sensor_type_check_ok:
                new_input = input("Please type name of new sensor type: ")
                sensor_type_check_ok = data_store.checkSensorType(new_input)
            chosen_sensor_type = data_store.addToSensorTypes(new_input)
        else:
            chosen_sensor_type = sensor_types[choice - 2]

        return sensorName, chosen_sensor_type

    def resolve_sensor(self, data_store, sensorName):
        choice = get_choice_input(
            f"Sensor '{sensorName}' not found. Do you wish to: ",
            [f"Add a new sensor, titled '{sensorName}'", "Cancel import"],
        )

        if choice == 1:
            return self.addToSensors(data_store, sensorName)
        elif choice == 2:
            print("Quitting")
            sys.exit(1)

    def resolve_privacy(self, data_store, tabletypeId, tablename):
        if tabletypeId in self.table_privacies:
            return tabletypeId, self.table_privacies[tabletypeId]

        # Choose Privacy
        privacies = data_store.getPrivacies()
        privacy_names = [c.name for c in privacies]
        privacy_names.append("Add a new classification")
        privacy_names.append("Cancel import")
        choice = get_choice_input(
            f"Ok, please provide classification for table '{tablename}': ",
            privacy_names,
        )

        if choice == len(privacy_names):
            print("Quitting")
            sys.exit(1)
        elif choice == len(privacy_names) - 1:
            privacy_check_ok = False
            while not privacy_check_ok:
                new_input = input("Please type name of new classification: ")
                privacy_check_ok = data_store.checkPrivacy(new_input)
            chosen_privacy = data_store.addToPrivacies(new_input)
        else:
            chosen_privacy = privacies[choice - 2]

        self.table_privacies[tabletypeId] = chosen_privacy

        return tabletypeId, chosen_privacy
