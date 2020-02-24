import unittest
from unittest.mock import patch


from pepys_import.resolvers.command_line_resolver import CommandLineResolver
from pepys_import.core.store.data_store import DataStore


class CommandLineResolverTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.resolver = CommandLineResolver()
        self.store = DataStore(
            "",
            "",
            "",
            0,
            ":memory:",
            db_type="sqlite",
            missing_data_resolver=self.resolver,
        )
        self.store.initialise()

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_add_new_privacy(self, menu_prompt):
        """Test whether a new Privacy entity created or not
        after searched and not founded in the Privacy Table."""

        # Select "Search an existing classification"->Search "PRIVACY-TEST"->
        # Select "Yes"
        menu_prompt.side_effect = ["1", "PRIVACY-TEST", "1"]
        with self.store.session_scope():
            privacy = self.resolver.resolve_privacy(self.store)
            self.assertEqual(privacy.name, "PRIVACY-TEST")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_select_existing_privacy(self, menu_prompt):
        """Test whether an existing Privacy entity searched and returned or not"""

        # Select "Search an existing classification"->Search "PRIVACY-TEST"
        menu_prompt.side_effect = ["1", "PRIVACY-TEST"]
        with self.store.session_scope():
            self.store.add_to_privacies("PRIVACY-TEST")
            privacy = self.resolver.resolve_privacy(self.store)
            self.assertEqual(privacy.name, "PRIVACY-TEST")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_fuzzy_search_select_existing_privacy_without_search(
        self, resolver_prompt, menu_prompt
    ):
        """Test whether a new Privacy entity created or not"""

        # Select "Add a new classification"->Type "PRIVACY-TEST"
        menu_prompt.side_effect = ["2"]
        resolver_prompt.side_effect = ["PRIVACY-TEST"]
        with self.store.session_scope():
            self.store.add_to_privacies("PRIVACY-TEST")
            privacy = self.resolver.resolve_privacy(self.store)
            self.assertEqual(privacy.name, "PRIVACY-TEST")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_recursive_privacy(self, menu_prompt):
        """Test whether recursive call works for privacy"""

        # Select "Search an existing classification"->Search "PRIVACY-TEST"->Select "No"
        # ->Search "PRIVACY-1"
        menu_prompt.side_effect = ["1", "PRIVACY-TEST", "2", "PRIVACY-1"]
        with self.store.session_scope():
            self.store.add_to_privacies("PRIVACY-1")
            self.store.add_to_privacies("PRIVACY-2")
            privacy = self.resolver.resolve_privacy(self.store)
            self.assertEqual(privacy.name, "PRIVACY-1")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_quit_works_for_resolver_privacy(self, menu_prompt):
        """Test whether "." quits from the resolve privacy"""
        menu_prompt.side_effect = [".", "1", "TEST", "."]
        with self.store.session_scope():
            # Select "."
            with self.assertRaises(SystemExit):
                self.resolver.resolve_privacy(self.store)
            # Select "Search an existing classification"->Search "TEST"->Select "."
            with self.assertRaises(SystemExit):
                self.resolver.resolve_privacy(self.store)

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_resolve_sensor(self, resolver_prompt, menu_prompt):
        """Test whether correct sensor type and privacy entities are resolved or not"""

        # Select "Add a new sensor"->Select "Add a new sensor-type"->
        # Type "SENSOR-TYPE-1"->Select "Add a new classification"->Type "PRIVACY-1"
        menu_prompt.side_effect = ["2", "2", "2"]
        resolver_prompt.side_effect = ["SENSOR-TYPE-1", "PRIVACY-1"]
        with self.store.session_scope():
            self.store.add_to_sensor_types("SENSOR-TYPE-1")
            self.store.add_to_privacies("PRIVACY-1")
            sensor_type, privacy = self.resolver.resolve_sensor(
                self.store, "TEST", sensor_type=None, privacy=None
            )

            self.assertEqual(sensor_type.name, "SENSOR-TYPE-1")
            self.assertEqual(privacy.name, "PRIVACY-1")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_resolve_sensor_with_new_sensor_type(self, resolver_prompt, menu_prompt):
        """Test whether correct sensor type and privacy entities are resolved or not"""

        # Select "Add a new sensor"->Select "Add a new sensor-type"->
        # Type "SENSOR-TYPE-1"->Select "Add a new classification"->Type "PRIVACY-1"
        menu_prompt.side_effect = ["2", "2", "2"]
        resolver_prompt.side_effect = ["SENSOR-TYPE-1", "PRIVACY-1"]
        with self.store.session_scope():
            self.store.add_to_privacies("PRIVACY-1")
            sensor_type, privacy = self.resolver.resolve_sensor(
                self.store, "TEST", sensor_type=None, privacy=None
            )

            self.assertEqual(sensor_type.name, "SENSOR-TYPE-1")
            self.assertEqual(privacy.name, "PRIVACY-1")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_select_existing_sensor(self, menu_prompt):
        """Test whether an existing Sensor entity returned after fuzzy search"""

        # Select "Search for existing sensor"->Search "TEST"
        menu_prompt.side_effect = ["1", "TEST"]
        with self.store.session_scope():
            # Create platform first, then create a Sensor object
            sensor_type = self.store.add_to_sensor_types("SENSOR-TYPE-1")
            privacy = self.store.add_to_privacies("PRIVACY-1").name
            nationality = self.store.add_to_nationalities("UK").name
            platform_type = self.store.add_to_platform_types("PLATFORM-TYPE-1").name
            platform = self.store.get_platform(
                platform_name="Test Platform",
                nationality=nationality,
                platform_type=platform_type,
                privacy=privacy,
            )
            platform.get_sensor(self.store, "TEST", sensor_type, privacy)

            # it will return existing Sensor entity
            sensor = self.resolver.resolve_sensor(
                self.store, "TEST", sensor_type, privacy
            )
            self.assertEqual(sensor.name, "TEST")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_recursive_sensor(self, menu_prompt):
        """Test whether recursive call works for sensor"""

        # Select "Search an existing sensor"->Search "SENSOR-TEST"->Select "No"
        # ->Search "SENSOR-1"
        menu_prompt.side_effect = ["1", "SENSOR-TEST", "2", "SENSOR-1"]
        with self.store.session_scope():
            # Create platform first, then create a Sensor object
            sensor_type = self.store.add_to_sensor_types("SENSOR-TYPE-1")
            privacy = self.store.add_to_privacies("PRIVACY-1").name
            nationality = self.store.add_to_nationalities("UK").name
            platform_type = self.store.add_to_platform_types("PLATFORM-TYPE-1").name
            platform = self.store.get_platform(
                platform_name="Test Platform",
                nationality=nationality,
                platform_type=platform_type,
                privacy=privacy,
            )
            platform.get_sensor(self.store, "SENSOR-1", sensor_type, privacy)
            platform.get_sensor(self.store, "SENSOR-2", sensor_type, privacy)

            sensor = self.resolver.resolve_sensor(
                self.store, "SENSOR-TEST", sensor_type, privacy
            )
            self.assertEqual(sensor.name, "SENSOR-1")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_add_sensor(self, menu_prompt):
        """Test whether a new Sensor entity created or not after searched
        and not founded in the Sensor Table."""

        # Select "Search an existing sensor"->Search "SENSOR-TEST"->Select "Yes"->
        # Select "Search for an existing sensor-type"->Search "SENSOR-TYPE-1"->
        # Select "Search an existing classification"->Search "PRIVACY-1"
        menu_prompt.side_effect = [
            "1",
            "SENSOR-TEST",
            "1",
            "1",
            "SENSOR-TYPE-1",
            "1",
            "PRIVACY-1",
        ]
        with self.store.session_scope():
            # Create platform first, then create a Sensor object
            sensor_type = self.store.add_to_sensor_types("SENSOR-TYPE-1")
            privacy = self.store.add_to_privacies("PRIVACY-1").name
            nationality = self.store.add_to_nationalities("UK").name
            platform_type = self.store.add_to_platform_types("PLATFORM-TYPE-1").name
            platform = self.store.get_platform(
                platform_name="Test Platform",
                nationality=nationality,
                platform_type=platform_type,
                privacy=privacy,
            )
            platform.get_sensor(self.store, "SENSOR-1", sensor_type, privacy)
            platform.get_sensor(self.store, "SENSOR-2", sensor_type, privacy)

            sensor_type, privacy = self.resolver.resolve_sensor(
                self.store, "SENSOR-TEST", sensor_type=None, privacy=None
            )

            self.assertEqual(sensor_type.name, "SENSOR-TYPE-1")
            self.assertEqual(privacy.name, "PRIVACY-1")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_quit_works_for_resolver_sensor(self, resolver_prompt, menu_prompt):
        """Test whether "." quits from the resolve sensor"""
        # TODO: selects not correct
        menu_prompt.side_effect = [".", "2", ".", "2", ".", "1", "TEST", "."]
        resolver_prompt.side_effect = ["TEST"]
        with self.store.session_scope():
            # Select "."
            with self.assertRaises(SystemExit):
                self.resolver.resolve_sensor(self.store, "", "", "")
            # Select "Add a new sensor"->Select "."
            with self.assertRaises(SystemExit):
                self.resolver.resolve_sensor(self.store, "", "", "")
            # Select "Add a new sensor"->Search "TEST"->Select "."
            with self.assertRaises(SystemExit):
                self.resolver.resolve_sensor(self.store, "", "", "")
            # Select "Search an existing sensor"->Search "TEST"->Select "."
            with self.assertRaises(SystemExit):
                self.resolver.resolve_sensor(self.store, "", "", "")

    # def test_resolver_sensor_with_sensor_given(self):
    #     """Test whether an existing Sensor entity returned or not"""
    #     with self.store.session_scope():
    #         sensor_type = self.store.add_to_sensor_types("SENSOR-TYPE-1")
    #         privacy = self.store.add_to_privacies("PRIVACY-1")
    #         platform_type = self.store.add_to_platform_types("Warship")
    #         nationality = self.store.add_to_nationalities("UK")
    #         platform = self.store.get_platform(
    #             "PLATFORM-1",
    #             nationality=nationality.name,
    #             platform_type=platform_type.name,
    #             privacy=privacy.name,
    #         )
    #         all_sensors = self.store.session.query(self.store.db_classes.Sensor).all()
    #         platform.get_sensor(
    #             data_store=self.store,
    #             all_sensors=all_sensors,
    #             sensor_name="TEST",
    #             sensor_type=sensor_type,
    #             privacy=privacy,
    #         )
    #
    #         # it will return existing Sensor entity
    #         sensor = self.resolver.resolve_sensor(
    #             data_store=self.store,
    #             sensor_name="TEST",
    #             sensor_type=sensor_type,
    #             privacy=privacy,
    #         )
    #         self.assertEqual(sensor.name, "TEST")
    #         self.assertEqual(sensor.sensor_type_id, sensor_type.sensor_type_id)

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_resolver_sensor_with_values_given(self, menu_prompt):
        """Test whether correct sensor type and privacy returns from add_to_sensors method or not"""

        # Select "Add a new sensor"
        menu_prompt.side_effect = ["2"]
        with self.store.session_scope():
            sensor_type = self.store.add_to_sensor_types("SENSOR-TYPE-1")
            privacy = self.store.add_to_privacies("PRIVACY-1")
            resolved_type, resolved_privacy = self.resolver.resolve_sensor(
                self.store, "TEST", sensor_type.name, privacy.name
            )
            self.assertEqual(resolved_type.sensor_type_id, sensor_type.sensor_type_id)
            self.assertEqual(resolved_privacy.privacy_id, privacy.privacy_id)

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_sensor_type_add_sensor_type(self, menu_prompt):
        """Test whether a new sensor type is added or not"""

        # Type "TEST"->Select "Yes"
        menu_prompt.side_effect = ["TEST", "1"]
        with self.store.session_scope():
            sensor_type = self.resolver.fuzzy_search_sensor_type(self.store)
            self.assertEqual(sensor_type.name, "TEST")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_sensor_type_recursive(self, menu_prompt):
        """Test whether recursive call works for sensor type"""

        # Type "TEST"->Select "No, I'd like to select a sensor type"->Type "SENSOR-TYPE-1"
        menu_prompt.side_effect = ["TEST", "2", "SENSOR-TYPE-1"]
        with self.store.session_scope():
            self.store.add_to_sensor_types("SENSOR-TYPE-1")
            self.store.add_to_sensor_types("SENSOR-TYPE-2")
            sensor_type = self.resolver.fuzzy_search_sensor_type(self.store)
            self.assertEqual(sensor_type.name, "SENSOR-TYPE-1")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_quit_works_for_fuzzy_search_sensor_type(self, menu_prompt):
        """Test whether "." quits from the fuzzy search sensor type"""

        # Type "TEST"->Select "."
        menu_prompt.side_effect = ["TEST", "."]
        with self.store.session_scope():
            with self.assertRaises(SystemExit):
                self.resolver.fuzzy_search_sensor_type(self.store)

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_add_new_nationality(self, menu_prompt):
        """Test whether a new nationality is added or not"""

        # Type "TEST"->Select "Yes"
        menu_prompt.side_effect = ["TEST", "1"]
        with self.store.session_scope():
            nationality = self.resolver.fuzzy_search_nationality(self.store)
            self.assertEqual(nationality.name, "TEST")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_nationality_recursive(self, menu_prompt):
        """Test whether recursive call works for Nationality"""

        # Type "TEST"->Select "No, I'd like to select a nationality"->Type "UK"
        menu_prompt.side_effect = ["TEST", "2", "UK"]
        with self.store.session_scope():
            self.store.add_to_nationalities("UK")
            self.store.add_to_nationalities("USA")
            nationality = self.resolver.fuzzy_search_nationality(self.store)
            self.assertEqual(nationality.name, "UK")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_quit_works_for_fuzzy_search_nationality(self, menu_prompt):
        """Test whether "." quits from the fuzzy search nationality """
        menu_prompt.side_effect = ["TEST", "."]
        with self.store.session_scope():
            with self.assertRaises(SystemExit):
                self.resolver.fuzzy_search_nationality(self.store)

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_quit_works_for_resolve_nationality(self, menu_prompt):
        """Test whether "." quits from the resolve nationality """
        menu_prompt.side_effect = ["."]
        with self.store.session_scope():
            with self.assertRaises(SystemExit):
                self.resolver.resolve_nationality(self.store)

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_add_new_platform_type(self, menu_prompt):
        """Test whether a new Platform Type is added or not"""

        # Type "TEST"->Select "Yes"
        menu_prompt.side_effect = ["TEST", "1"]
        with self.store.session_scope():
            platform_type = self.resolver.fuzzy_search_platform_type(self.store)
            self.assertEqual(platform_type.name, "TEST")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_platform_type_recursive(self, menu_prompt):
        """Test whether recursive call works for Platform Type"""

        # Type "TEST"->Select "No, I'd like to select a platform type"->Type "PLATFORM-TYPE-1"
        menu_prompt.side_effect = ["TEST", "2", "PLATFORM-TYPE-1"]
        with self.store.session_scope():
            self.store.add_to_platform_types("PLATFORM-TYPE-1")
            self.store.add_to_platform_types("PLATFORM-TYPE-2")
            platform_type = self.resolver.fuzzy_search_platform_type(self.store)
            self.assertEqual(platform_type.name, "PLATFORM-TYPE-1")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_quit_works_for_fuzzy_search_platform_type(self, menu_prompt):
        """Test whether "." quits from platform type"""

        # Type "TEST"->Select "."
        menu_prompt.side_effect = ["TEST", "."]
        with self.store.session_scope():
            with self.assertRaises(SystemExit):
                self.resolver.fuzzy_search_platform_type(self.store)

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_quit_works_for_resolve_platform_type(self, menu_prompt):
        """Test whether "." quits from the resolve platform type """
        menu_prompt.side_effect = ["."]
        with self.store.session_scope():
            with self.assertRaises(SystemExit):
                self.resolver.resolve_platform_type(self.store)

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_add_platform_to_synonym(self, menu_prompt):
        """Test whether entered platform name is added as a synonym or not"""

        # Search "PLATFORM-1"->Select "Yes"
        menu_prompt.side_effect = ["PLATFORM-1", "1"]
        with self.store.session_scope():
            privacy = self.store.add_to_privacies("PRIVACY-1")
            platform_type = self.store.add_to_platform_types("Warship")
            nationality = self.store.add_to_nationalities("UK")
            platform = self.store.get_platform(
                "PLATFORM-1",
                nationality=nationality.name,
                platform_type=platform_type.name,
                privacy=privacy.name,
            )

            synonym = self.resolver.fuzzy_search_platform(
                self.store,
                "TEST",
                nationality=nationality.name,
                platform_type=platform_type.name,
                privacy=privacy.name,
            )

            self.assertEqual(platform.platform_id, synonym.entity)

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_fuzzy_search_add_new_platform(self, resolver_prompt, menu_prompt):
        """Test whether a new platform entity is created or not"""

        # Search "PLATFORM-1"->Select "No"->Type name/trigraph/quadgraph/pennat number->Select "Yes"
        menu_prompt.side_effect = ["PLATFORM-1", "2", "1"]
        resolver_prompt.side_effect = ["TEST", "TST", "TEST", "123"]
        with self.store.session_scope():
            privacy = self.store.add_to_privacies("PRIVACY-1")
            platform_type = self.store.add_to_platform_types("Warship")
            nationality = self.store.add_to_nationalities("UK")
            self.store.get_platform(
                "PLATFORM-1",
                nationality=nationality.name,
                platform_type=platform_type.name,
                privacy=privacy.name,
            )

            (
                platform_name,
                platform_type,
                nationality,
                privacy,
            ) = self.resolver.fuzzy_search_platform(
                self.store,
                "TEST",
                nationality=nationality.name,
                platform_type=platform_type.name,
                privacy=privacy.name,
            )

            self.assertEqual(platform_name, "TEST")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_quit_works_for_fuzzy_search_platform(self, menu_prompt):
        """Test whether "." quits from platform"""

        # Type "TEST"->Select "."
        menu_prompt.side_effect = ["PLATFORM-1", "."]
        with self.store.session_scope():
            privacy = self.store.add_to_privacies("PRIVACY-1")
            platform_type = self.store.add_to_platform_types("Warship")
            nationality = self.store.add_to_nationalities("UK")
            self.store.get_platform(
                "PLATFORM-1",
                nationality=nationality.name,
                platform_type=platform_type.name,
                privacy=privacy.name,
            )
            with self.assertRaises(SystemExit):
                self.resolver.fuzzy_search_platform(self.store, "TEST", "", "", "")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_resolver_platform_with_fuzzy_searches(
        self, resolver_platform, menu_prompt
    ):
        """Test whether correct entities return when fuzzy search for platform type, nationality and privacy are
        called"""

        # Select "Search for existing platform"->Type "TEST"->Type name/trigraph/quadgraph/pennat number->Select
        # "Search for an existing nationality"->Select "UK"->Select "Search for an existing platform type"->Select
        # "Warship"->Select "Search for an existing classification"->Select "PRIVACY-1"->Select "Yes"
        menu_prompt.side_effect = [
            "1",
            "TEST",
            "1",
            "UK",
            "1",
            "Warship",
            "1",
            "PRIVACY-1",
            "1",
        ]
        resolver_platform.side_effect = ["TEST", "TST", "TEST", "123"]
        with self.store.session_scope():
            self.store.add_to_privacies("PRIVACY-1")
            self.store.add_to_platform_types("Warship")
            self.store.add_to_nationalities("UK")
            (
                platform_name,
                platform_type,
                nationality,
                privacy,
            ) = self.resolver.resolve_platform(
                data_store=self.store,
                platform_name="TEST",
                platform_type=None,
                nationality=None,
                privacy=None,
            )
            self.assertEqual(platform_name, "TEST")
            self.assertEqual(platform_type.name, "Warship")
            self.assertEqual(nationality.name, "UK")
            self.assertEqual(privacy.name, "PRIVACY-1")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_resolver_platform_with_new_values(self, resolver_prompt, menu_prompt):
        """Test whether new platform type, nationality and privacy entities are created for Platform or not"""

        # Select "Add a new platform"->Type name/trigraph/quadgraph/pennat number->Select "Add a new nationality"->
        # Select "UK"->Select "Add a new platform type"->Select "Warship"->Select "Add a new classification"->Select
        # "PRIVACY-1"->Select "Yes"
        menu_prompt.side_effect = ["2", "2", "2", "2", "1"]
        resolver_prompt.side_effect = [
            "TEST",
            "TST",
            "TEST",
            "123",
            "UK",
            "Warship",
            "PRIVACY-1",
        ]
        with self.store.session_scope():
            (
                platform_name,
                platform_type,
                nationality,
                privacy,
            ) = self.resolver.resolve_platform(
                data_store=self.store,
                platform_name="TEST",
                platform_type=None,
                nationality=None,
                privacy=None,
            )
            self.assertEqual(platform_name, "TEST")
            self.assertEqual(platform_type.name, "Warship")
            self.assertEqual(nationality.name, "UK")
            self.assertEqual(privacy.name, "PRIVACY-1")

    # TODO: use it for find method in data store or delete it
    # def test_resolver_platform_with_platform_given(self):
    #     with self.store.session_scope():
    #         privacy = self.store.add_to_privacies("PRIVACY-1")
    #         platform_type = self.store.add_to_platform_types("Warship")
    #         nationality = self.store.add_to_nationalities("UK")
    #         self.store.get_platform(
    #             "TEST",
    #             nationality=nationality.name,
    #             platform_type=platform_type.name,
    #             privacy=privacy.name,
    #         )
    #         platform = self.resolver.resolve_platform(
    #             data_store=self.store,
    #             platform_name="TEST",
    #             platform_type=platform_type.name,
    #             nationality=nationality.name,
    #             privacy=privacy.name,
    #         )
    #         self.assertEqual(platform.name, "TEST")
    #         self.assertEqual(platform.platform_type_id, platform_type.platform_type_id)
    #         self.assertEqual(platform.nationality_id, nationality.nationality_id)
    #         self.assertEqual(platform.privacy_id, privacy.privacy_id)

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_resolver_platform_edit_given_values(self, resolver_prompt, menu_prompt):
        """Test a new platform is created after make further edits option is selected"""

        # Select "Add a new platform"->Type name/trigraph/quadgraph/pennat number->Select "No"->
        # Type name/trigraph/quadgraph/pennat number->Select "Search for an existing nationality"->Select
        # "UK"->Select "Search for an existing platform type"->Select "Warship"->Select "Search for an existing
        # classification"->Select "PRIVACY-1"->Select "Yes"
        menu_prompt.side_effect = [
            "2",
            "2",
            "1",
            "UK",
            "1",
            "Warship",
            "1",
            "PRIVACY-1",
            "1",
        ]
        resolver_prompt.side_effect = [
            "TEST",
            "TST",
            "TEST",
            "123",
            "TEST",
            "TST",
            "TEST",
            "123",
        ]
        with self.store.session_scope():
            privacy = self.store.add_to_privacies("PRIVACY-1").name
            platform_type = self.store.add_to_platform_types("Warship").name
            nationality = self.store.add_to_nationalities("UK").name
            (
                platform_name,
                platform_type,
                nationality,
                privacy,
            ) = self.resolver.resolve_platform(
                data_store=self.store,
                platform_name="TEST",
                platform_type=platform_type,
                nationality=nationality,
                privacy=privacy,
            )
            self.assertEqual(platform_name, "TEST")
            self.assertEqual(platform_type.name, "Warship")
            self.assertEqual(nationality.name, "UK")
            self.assertEqual(privacy.name, "PRIVACY-1")

    @patch("pepys_import.resolvers.command_line_input.prompt")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_quit_works_for_resolver_platform(self, resolver_prompt, menu_prompt):
        """Test whether "." quits works for resolver platform """
        menu_prompt.side_effect = [
            ".",
            "2",
            ".",
        ]
        resolver_prompt.side_effect = [
            "TEST",
            "TST",
            "TEST",
            "123",
            "TEST",
            "TST",
            "TEST",
            "123",
        ]
        with self.store.session_scope():
            privacy = self.store.add_to_privacies("PRIVACY-1").name
            platform_type = self.store.add_to_platform_types("Warship").name
            nationality = self.store.add_to_nationalities("UK").name

            # Select "."
            with self.assertRaises(SystemExit):
                self.resolver.resolve_platform(
                    self.store, "TEST", platform_type, nationality, privacy
                )
            # Select "Add a new platform"->Type name/trigraph/quadgraph/pennat->Select "."
            with self.assertRaises(SystemExit):
                self.resolver.resolve_platform(
                    self.store, "TEST", platform_type, nationality, privacy
                )

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_add_new_datafile_type(self, menu_prompt):
        menu_prompt.side_effect = ["TEST", "1"]
        with self.store.session_scope():
            datafile_type = self.resolver.fuzzy_search_datafile_type(self.store)
            self.assertEqual(datafile_type.name, "TEST")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_datafile_type_recursive(self, menu_prompt):
        menu_prompt.side_effect = ["TEST", "2", "DATAFILE-TYPE-1"]
        with self.store.session_scope():
            self.store.add_to_datafile_types("DATAFILE-TYPE-1")
            self.store.add_to_datafile_types("DATAFILE-TYPE-2")
            datafile_type = self.resolver.fuzzy_search_datafile_type(self.store)
            self.assertEqual(datafile_type.name, "DATAFILE-TYPE-1")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_quit_works_for_fuzzy_search_datafile_type(self, menu_prompt):
        menu_prompt.side_effect = ["TEST", "."]
        with self.store.session_scope():
            with self.assertRaises(SystemExit):
                self.resolver.fuzzy_search_datafile_type(self.store)

    # TODO: use it for find method in data store or delete it
    # def test_resolver_datafile_with_datafile_given(self):
    #     with self.store.session_scope():
    #         privacy = self.store.add_to_privacies("PRIVACY-1")
    #         datafile_type = self.store.add_to_datafile_types("DATAFILE-TYPE-1")
    #         self.store.add_to_datafiles(
    #             file_type=datafile_type.name, privacy=privacy.name, reference="TEST",
    #         )
    #         datafile = self.resolver.resolve_datafile(
    #             data_store=self.store,
    #             datafile_name="TEST",
    #             datafile_type=datafile_type.name,
    #             privacy=privacy.name,
    #         )
    #         self.assertEqual(datafile.reference, "TEST")
    #         self.assertEqual(datafile.datafile_type_id, datafile_type.datafile_type_id)
    #         self.assertEqual(datafile.privacy_id, privacy.privacy_id)

    # TODO: modify it when resolve_datafile is refactored
    # @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    # def test_resolver_datafile_add_to_synonym(self, menu_prompt):
    #     menu_prompt.side_effect = ["1", "TEST", "1"]
    #     with self.store.session_scope():
    #         synonym = self.resolver.resolve_datafile(
    #             data_store=self.store,
    #             datafile_name="TEST",
    #             datafile_type=None,
    #             privacy=None,
    #         )
    #         self.assertEqual(synonym.synonym, "TEST")
    #         self.assertEqual(synonym.table, "Datafiles")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_resolver_datafile_edit_given_values(self, menu_prompt):
        menu_prompt.side_effect = [
            "2",
            "2",
            "DATAFILE-TYPE-1",
            "1",
            "PRIVACY-1",
            "1",
        ]
        with self.store.session_scope():
            privacy = self.store.add_to_privacies("PRIVACY-1").name
            datafile_type = self.store.add_to_datafile_types("DATAFILE-TYPE-1").name
            (datafile_name, datafile_type, privacy,) = self.resolver.resolve_datafile(
                data_store=self.store,
                datafile_name="TEST",
                datafile_type=datafile_type,
                privacy=privacy,
            )
            self.assertEqual(datafile_name, "TEST")
            self.assertEqual(datafile_type.name, "DATAFILE-TYPE-1")
            self.assertEqual(privacy.name, "PRIVACY-1")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_resolver_datafile_add_new_datafile(self, menu_prompt):
        menu_prompt.side_effect = [
            "1",
            "TEST",
            "2",
            "DATAFILE-TYPE-1",
            "1",
            "PRIVACY-1",
            "1",
        ]
        with self.store.session_scope():
            self.store.add_to_privacies("PRIVACY-1")
            self.store.add_to_datafile_types("DATAFILE-TYPE-1")
            datafile_name, datafile_type, privacy = self.resolver.resolve_datafile(
                data_store=self.store,
                datafile_name="TEST",
                datafile_type=None,
                privacy=None,
            )
            self.assertEqual(datafile_name, "TEST")
            self.assertEqual(datafile_type.name, "DATAFILE-TYPE-1")
            self.assertEqual(privacy.name, "PRIVACY-1")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_datafile_returns_existing_datafile(self, menu_prompt):
        menu_prompt.side_effect = ["TEST"]
        with self.store.session_scope():
            privacy = self.store.add_to_privacies("PRIVACY-1")
            datafile_type = self.store.add_to_datafile_types("DATAFILE-TYPE-1")
            self.store.add_to_datafiles(
                file_type=datafile_type.name, privacy=privacy.name, reference="TEST",
            )
            datafile = self.resolver.fuzzy_search_datafile(
                data_store=self.store,
                datafile_name="TEST",
                datafile_type=datafile_type.name,
                privacy=privacy.name,
            )
            self.assertEqual(datafile.reference, "TEST")
            self.assertEqual(datafile.datafile_type_id, datafile_type.datafile_type_id)
            self.assertEqual(datafile.privacy_id, privacy.privacy_id)

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_quit_works_for_resolver_datafile(self, menu_prompt):
        menu_prompt.side_effect = [
            ".",
            "2",
            "DATAFILE-TYPE-1",
            ".",
            "2",
            ".",
            "1",
            "TEST",
            ".",
        ]
        with self.store.session_scope():
            self.store.add_to_privacies("PRIVACY-1")
            self.store.add_to_datafile_types("DATAFILE-TYPE-1")

            with self.assertRaises(SystemExit):
                self.resolver.resolve_datafile(self.store, "TEST", "", "")
            with self.assertRaises(SystemExit):
                self.resolver.resolve_datafile(self.store, "TEST", "", "")
            with self.assertRaises(SystemExit):
                self.resolver.resolve_datafile(
                    self.store, "TEST", "DATAFILE-TYPE-1", "PRIVACY-1"
                )
            with self.assertRaises(SystemExit):
                self.resolver.resolve_datafile(self.store, "TEST", "", "")


if __name__ == "__main__":
    unittest.main()
