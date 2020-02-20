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
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_resolver_privacy(self, resolver_prompt, menu_prompt):
        menu_prompt.return_value = "2"
        resolver_prompt.return_value = "PRIVACY-TEST"
        with self.store.session_scope():
            privacy = self.resolver.resolve_privacy(self.store)
            self.assertEqual(privacy.name, "PRIVACY-TEST")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_add_new_privacy(self, menu_prompt):
        menu_prompt.side_effect = ["1", "PRIVACY-TEST", "1"]
        with self.store.session_scope():
            privacy = self.resolver.resolve_privacy(self.store)
            self.assertEqual(privacy.name, "PRIVACY-TEST")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_select_existing_privacy(self, menu_prompt):
        menu_prompt.side_effect = ["1", "PRIVACY-TEST"]
        with self.store.session_scope():
            self.store.add_to_privacies("PRIVACY-TEST")
            privacy = self.resolver.resolve_privacy(self.store)
            self.assertEqual(privacy.name, "PRIVACY-TEST")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_recursive_privacy(self, menu_prompt):
        menu_prompt.side_effect = ["1", "PRIVACY-TEST", "2", "PRIVACY-1"]
        with self.store.session_scope():
            self.store.add_to_privacies("PRIVACY-1")
            self.store.add_to_privacies("PRIVACY-2")
            privacy = self.resolver.resolve_privacy(self.store)
            self.assertEqual(privacy.name, "PRIVACY-1")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_quit_works_for_resolver_privacy(self, menu_prompt):
        menu_prompt.side_effect = [".", "1", "TEST", "."]
        with self.store.session_scope():
            with self.assertRaises(SystemExit):
                self.resolver.resolve_privacy(self.store)
            with self.assertRaises(SystemExit):
                self.resolver.resolve_privacy(self.store)

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_resolve_sensor(self, resolver_prompt, menu_prompt):
        menu_prompt.side_effect = ["2", "2", "PRIVACY-1"]
        resolver_prompt.side_effect = ["SENSOR-TYPE-1"]
        with self.store.session_scope():
            self.store.add_to_sensor_types("SENSOR-TYPE-1")
            self.store.add_to_privacies("PRIVACY-1")
            sensor_type, privacy = self.resolver.resolve_sensor(
                self.store, "TEST", sensor_type=None, privacy=None
            )

            self.assertEqual(sensor_type.name, "SENSOR-TYPE-1")
            self.assertEqual(privacy.name, "PRIVACY-1")

    def test_resolve_sensor_with_existing_sensor(self):
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
            sensors = self.store.session.query(self.store.db_classes.Sensor).all()
            sensor = platform.get_sensor(
                self.store, sensors, "TEST", sensor_type, privacy
            )

            sensor_2 = self.resolver.resolve_sensor(
                self.store, "TEST", sensor_type, privacy
            )

            self.assertEqual(sensor.name, sensor_2.name)
            self.assertEqual(sensor_2.name, "TEST")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_select_existing_sensor(self, menu_prompt):
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
            sensors = self.store.session.query(self.store.db_classes.Sensor).all()
            platform.get_sensor(self.store, sensors, "TEST", sensor_type, privacy)
            sensor = self.resolver.resolve_sensor(
                self.store, "TEST", sensor_type, privacy
            )
            self.assertEqual(sensor.name, "TEST")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_recursive_sensor(self, menu_prompt):
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
            sensors = self.store.session.query(self.store.db_classes.Sensor).all()
            platform.get_sensor(self.store, sensors, "SENSOR-1", sensor_type, privacy)
            platform.get_sensor(self.store, sensors, "SENSOR-2", sensor_type, privacy)

            sensor = self.resolver.resolve_sensor(
                self.store, "SENSOR-TEST", sensor_type, privacy
            )
            self.assertEqual(sensor.name, "SENSOR-1")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_add_sensor(self, menu_prompt):
        menu_prompt.side_effect = [
            "1",
            "SENSOR-TEST",
            "1",
            "1",
            "SENSOR-TYPE-1",
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
            sensors = self.store.session.query(self.store.db_classes.Sensor).all()
            platform.get_sensor(self.store, sensors, "SENSOR-1", sensor_type, privacy)
            platform.get_sensor(self.store, sensors, "SENSOR-2", sensor_type, privacy)

            sensor_type, privacy = self.resolver.resolve_sensor(
                self.store, "SENSOR-TEST", sensor_type=None, privacy=None
            )

            self.assertEqual(sensor_type.name, "SENSOR-TYPE-1")
            self.assertEqual(privacy.name, "PRIVACY-1")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_quit_works_for_resolver_sensor(self, resolver_prompt, menu_prompt):
        menu_prompt.side_effect = [".", "2", ".", "2", ".", "1", "TEST", "."]
        resolver_prompt.side_effect = ["TEST"]
        with self.store.session_scope():
            with self.assertRaises(SystemExit):
                self.resolver.resolve_sensor(self.store, "", "", "")
            with self.assertRaises(SystemExit):
                self.resolver.resolve_sensor(self.store, "", "", "")
            with self.assertRaises(SystemExit):
                self.resolver.resolve_sensor(self.store, "", "", "")
            with self.assertRaises(SystemExit):
                self.resolver.resolve_sensor(self.store, "", "", "")

    def test_resolver_sensor_with_sensor_given(self):
        with self.store.session_scope():
            sensor_type = self.store.add_to_sensor_types("SENSOR-TYPE-1")
            privacy = self.store.add_to_privacies("PRIVACY-1")
            platform_type = self.store.add_to_platform_types("Warship")
            nationality = self.store.add_to_nationalities("UK")
            platform = self.store.get_platform(
                "PLATFORM-1",
                nationality=nationality.name,
                platform_type=platform_type.name,
                privacy=privacy.name,
            )
            all_sensors = self.store.session.query(self.store.db_classes.Sensor).all()
            platform.get_sensor(
                data_store=self.store,
                all_sensors=all_sensors,
                sensor_name="TEST",
                sensor_type=sensor_type,
                privacy=privacy,
            )
            sensor = self.resolver.resolve_sensor(
                data_store=self.store,
                sensor_name="TEST",
                sensor_type=sensor_type,
                privacy=privacy,
            )
            self.assertEqual(sensor.name, "TEST")
            self.assertEqual(sensor.sensor_type_id, sensor_type.sensor_type_id)

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_sensor_type_add_sensor_type(self, menu_prompt):
        menu_prompt.side_effect = ["TEST", "1"]
        with self.store.session_scope():
            sensor_type = self.resolver.fuzzy_search_sensor_type(self.store)
            self.assertEqual(sensor_type.name, "TEST")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_sensor_type_recursive(self, menu_prompt):
        menu_prompt.side_effect = ["TEST", "2", "SENSOR-TYPE-1"]
        with self.store.session_scope():
            self.store.add_to_sensor_types("SENSOR-TYPE-1")
            self.store.add_to_sensor_types("SENSOR-TYPE-2")
            sensor_type = self.resolver.fuzzy_search_sensor_type(self.store)
            self.assertEqual(sensor_type.name, "SENSOR-TYPE-1")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_quit_works_for_fuzzy_search_sensor_type(self, menu_prompt):
        menu_prompt.side_effect = ["TEST", "."]
        with self.store.session_scope():
            with self.assertRaises(SystemExit):
                self.resolver.fuzzy_search_sensor_type(self.store)

    # @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    # @patch("pepys_import.resolvers.command_line_resolver.prompt")
    # def test_resolver_platform(self, resolver_prompt, menu_prompt):
    #     menu_prompt.side_effect = ["2", "2", "2", "2", "1"]
    #     resolver_prompt.side_effect = ["UK", "Warship", "PRIVACY-1"]
    #     with self.store.session_scope():
    #         self.store.add_to_privacies("PRIVACY-1")
    #         self.store.add_to_platform_types("Warship")
    #         self.store.add_to_nationalities("UK")
    #         (
    #             platform_name,
    #             platform_type,
    #             nationality,
    #             privacy,
    #         ) = self.resolver.resolve_platform(
    #             data_store=self.store,
    #             platform_name="TEST",
    #             platform_type=None,
    #             nationality=None,
    #             privacy=None,
    #         )
    #         self.assertEqual(platform_name, "TEST")
    #         self.assertEqual(platform_type.name, "Warship")
    #         self.assertEqual(nationality.name, "UK")
    #         self.assertEqual(privacy.name, "PRIVACY-1")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_quit_works_for_resolver_platform(self, resolver_prompt, menu_prompt):
        menu_prompt.side_effect = [
            ".",
            "2",
            ".",
            "2",
            "2",
            ".",
            "2",
            "2",
            "2",
            ".",
            "2",
            "2",
            "2",
            "2",
            ".",
            "1",
            "TEST",
            ".",
        ]
        resolver_prompt.side_effect = [
            "UK",
            "UK",
            "Warship",
            "UK",
            "Warship",
            "PRIVACY-1",
        ]
        with self.store.session_scope():
            self.store.add_to_privacies("PRIVACY-1")
            self.store.add_to_platform_types("Warship")
            self.store.add_to_nationalities("UK")

            with self.assertRaises(SystemExit):
                self.resolver.resolve_platform(self.store, "", "", "", "")
            with self.assertRaises(SystemExit):
                self.resolver.resolve_platform(self.store, "", "", "", "")
            with self.assertRaises(SystemExit):
                self.resolver.resolve_platform(self.store, "", "", "", "")
            with self.assertRaises(SystemExit):
                self.resolver.resolve_platform(self.store, "", "", "", "")
            with self.assertRaises(SystemExit):
                self.resolver.resolve_platform(self.store, "", "", "", "")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_resolver_platform_with_values(self, menu_prompt):
        menu_prompt.side_effect = ["2", "1"]
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

    def test_resolver_platform_with_platform_given(self):
        with self.store.session_scope():
            privacy = self.store.add_to_privacies("PRIVACY-1")
            platform_type = self.store.add_to_platform_types("Warship")
            nationality = self.store.add_to_nationalities("UK")
            self.store.get_platform(
                "TEST",
                nationality=nationality.name,
                platform_type=platform_type.name,
                privacy=privacy.name,
            )
            platform = self.resolver.resolve_platform(
                data_store=self.store,
                platform_name="TEST",
                platform_type=platform_type.name,
                nationality=nationality.name,
                privacy=privacy.name,
            )
            self.assertEqual(platform.name, "TEST")
            self.assertEqual(platform.platform_type_id, platform_type.platform_type_id)
            self.assertEqual(platform.nationality_id, nationality.nationality_id)
            self.assertEqual(platform.privacy_id, privacy.privacy_id)

    @patch("pepys_import.resolvers.command_line_input.prompt")
    def test_resolver_platform_add_to_synonym_table(self, menu_prompt):
        menu_prompt.side_effect = ["1", "TEST", "1"]
        with self.store.session_scope():
            synonym = self.resolver.resolve_platform(
                data_store=self.store,
                platform_name="TEST",
                platform_type=None,
                nationality=None,
                privacy=None,
            )
            self.assertEqual(synonym.synonym, "TEST")
            self.assertEqual(synonym.table, "Platforms")

    def test_resolver_platform_find_platform_from_synonym(self):
        # TODO: hit the lines between 66-87 in command line resolver
        pass


if __name__ == "__main__":
    unittest.main()
