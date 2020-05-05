import os
import unittest
from contextlib import redirect_stdout
from datetime import datetime
from io import StringIO
from unittest.mock import patch

from pepys_import.core.store.data_store import DataStore
from pepys_import.resolvers.command_line_resolver import CommandLineResolver

DIR_PATH = os.path.dirname(__file__)


class PrivacyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.resolver = CommandLineResolver()
        self.store = DataStore(
            "", "", "", 0, ":memory:", db_type="sqlite", missing_data_resolver=self.resolver,
        )
        self.store.initialise()
        with self.store.session_scope():
            self.change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_add_new_privacy(self, menu_prompt):
        """Test whether a new Privacy entity created or not
        after searched and not founded in the Privacy Table."""

        # Select "Search an existing classification"->Search "PRIVACY-TEST"->
        # Select "Yes"
        menu_prompt.side_effect = ["1", "PRIVACY-TEST", "1"]
        with self.store.session_scope():
            privacy = self.resolver.resolve_privacy(self.store, self.change_id, "")
            self.assertEqual(privacy.name, "PRIVACY-TEST")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_select_existing_privacy(self, menu_prompt):
        """Test whether an existing Privacy entity searched and returned or not"""

        # Select "Search an existing classification"->Search "PRIVACY-TEST"
        menu_prompt.side_effect = ["1", "PRIVACY-TEST"]
        with self.store.session_scope():
            self.store.add_to_privacies("PRIVACY-TEST", self.change_id)
            privacy = self.resolver.resolve_privacy(self.store, self.change_id, "")
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
            self.store.add_to_privacies("PRIVACY-TEST", self.change_id)
            privacy = self.resolver.resolve_privacy(self.store, self.change_id, "")
            self.assertEqual(privacy.name, "PRIVACY-TEST")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_recursive_privacy(self, menu_prompt):
        """Test whether recursive call works for privacy"""

        # Select "Search an existing classification"->Search "PRIVACY-TEST"->Select "No"
        # ->Search "PRIVACY-1"
        menu_prompt.side_effect = ["1", "PRIVACY-TEST", "2", "PRIVACY-1"]
        with self.store.session_scope():
            self.store.add_to_privacies("PRIVACY-1", self.change_id)
            self.store.add_to_privacies("PRIVACY-2", self.change_id)
            privacy = self.resolver.resolve_privacy(self.store, self.change_id, "")
            self.assertEqual(privacy.name, "PRIVACY-1")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_cancelling_fuzzy_search_privacy(self, menu_prompt):
        """Test whether "." returns to the resolver privacy"""

        # Search "TEST"->Select "."->Select "."
        menu_prompt.side_effect = ["TEST", ".", "."]
        with self.store.session_scope():
            privacy = self.resolver.fuzzy_search_privacy(self.store, self.change_id, "")
            self.assertIsNone(privacy)

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_cancelling_resolver_privacy(self, menu_prompt):
        """Test whether "." cancels the resolve privacy and returns None"""
        menu_prompt.side_effect = [".", "1", ".", "."]
        temp_output = StringIO()
        with self.store.session_scope():
            # Select "."
            privacy = self.resolver.resolve_privacy(self.store, self.change_id, "")
            self.assertIsNone(privacy)

            with redirect_stdout(temp_output):
                privacy = self.resolver.resolve_privacy(self.store, self.change_id, "")
            assert privacy is None
        output = temp_output.getvalue()
        assert "Returning to the previous menu" in output

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_resolve_privacy_empty_input(self, resolver_prompt, menu_prompt):
        resolver_prompt.side_effect = [""]
        menu_prompt.side_effect = ["2", "."]
        temp_output = StringIO()
        with self.store.session_scope(), redirect_stdout(temp_output):
            self.resolver.resolve_privacy(self.store, self.change_id, "")
        output = temp_output.getvalue()
        assert "You haven't entered an input!" in output


class NationalityTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.resolver = CommandLineResolver()
        self.store = DataStore(
            "", "", "", 0, ":memory:", db_type="sqlite", missing_data_resolver=self.resolver,
        )
        self.store.initialise()
        with self.store.session_scope():
            self.change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_add_new_nationality(self, menu_prompt):
        """Test whether a new nationality is added or not"""

        # Type "TEST"->Select "Yes"
        menu_prompt.side_effect = ["TEST", "1"]
        with self.store.session_scope():
            nationality = self.resolver.fuzzy_search_nationality(
                self.store, "PLATFORM-1", self.change_id
            )
            self.assertEqual(nationality.name, "TEST")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_nationality_recursive(self, menu_prompt):
        """Test whether recursive call works for Nationality"""

        # Type "TEST"->Select "No, I'd like to select a nationality"->Type "UK"
        menu_prompt.side_effect = ["TEST", "2", "UK"]
        with self.store.session_scope():
            self.store.add_to_nationalities("UK", self.change_id)
            self.store.add_to_nationalities("USA", self.change_id)
            nationality = self.resolver.fuzzy_search_nationality(
                self.store, "PLATFORM-1", self.change_id
            )
            self.assertEqual(nationality.name, "UK")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_cancelling_fuzzy_search_nationality(self, menu_prompt):
        """Test whether "." returns to the resolve nationality """
        menu_prompt.side_effect = [".", ".", "TEST", ".", "."]
        with self.store.session_scope():
            temp_output = StringIO()
            # Select "."->Select "."
            with redirect_stdout(temp_output):
                nationality = self.resolver.fuzzy_search_nationality(
                    self.store, "PLATFORM-1", self.change_id
                )
            output = temp_output.getvalue()
            self.assertIn("Returning to the previous menu", output)
            self.assertIsNone(nationality)

            # Search "TEST"->Select "."->Select "."
            with redirect_stdout(temp_output):
                nationality = self.resolver.fuzzy_search_nationality(
                    self.store, "PLATFORM-1", self.change_id
                )
            output = temp_output.getvalue()
            self.assertIn("Returning to the previous menu", output)
            self.assertIsNone(nationality)

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_cancelling_resolve_nationality(self, menu_prompt):
        """Test whether "." cancels the resolve nationality and returns None"""
        menu_prompt.side_effect = ["."]
        with self.store.session_scope():
            # Select "."
            nationality = self.resolver.resolve_nationality(self.store, "", self.change_id)
            self.assertIsNone(nationality)


class PlatformTypeTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.resolver = CommandLineResolver()
        self.store = DataStore(
            "", "", "", 0, ":memory:", db_type="sqlite", missing_data_resolver=self.resolver,
        )
        self.store.initialise()
        with self.store.session_scope():
            self.change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_add_new_platform_type(self, menu_prompt):
        """Test whether a new Platform Type is added or not"""

        # Type "TEST"->Select "Yes"
        menu_prompt.side_effect = ["TEST", "1"]
        with self.store.session_scope():
            platform_type = self.resolver.fuzzy_search_platform_type(
                self.store, "PLATFORM-1", self.change_id
            )
            self.assertEqual(platform_type.name, "TEST")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_platform_type_recursive(self, menu_prompt):
        """Test whether recursive call works for Platform Type"""

        # Type "TEST"->Select "No, I'd like to select a platform type"->Type "PLATFORM-TYPE-1"
        menu_prompt.side_effect = ["TEST", "2", "PLATFORM-TYPE-1"]
        with self.store.session_scope():
            self.store.add_to_platform_types("PLATFORM-TYPE-1", self.change_id)
            self.store.add_to_platform_types("PLATFORM-TYPE-2", self.change_id)
            platform_type = self.resolver.fuzzy_search_platform_type(
                self.store, "PLATFORM-1", self.change_id
            )
            self.assertEqual(platform_type.name, "PLATFORM-TYPE-1")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_cancelling_fuzzy_search_platform_type(self, menu_prompt):
        """Test whether "." returns to the resolve platform type"""
        menu_prompt.side_effect = [".", ".", "TEST", ".", "."]

        with self.store.session_scope():
            temp_output = StringIO()
            # Select "."->Select "."
            with redirect_stdout(temp_output):
                platform_type = self.resolver.fuzzy_search_platform_type(
                    self.store, "PLATFORM-1", self.change_id
                )
            output = temp_output.getvalue()
            self.assertIn("Returning to the previous menu", output)
            self.assertIsNone(platform_type)

            # Search "TEST"->Select "."->Select "."
            with redirect_stdout(temp_output):
                platform_type = self.resolver.fuzzy_search_platform_type(
                    self.store, "PLATFORM-1", self.change_id
                )
            output = temp_output.getvalue()
            self.assertIn("Returning to the previous menu", output)
            self.assertIsNone(platform_type)

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_cancelling_resolve_platform_type(self, menu_prompt):
        """Test whether "." cancels the resolve platform type and returns None"""
        menu_prompt.side_effect = ["."]
        with self.store.session_scope():
            platform_type = self.resolver.resolve_platform_type(
                self.store, "PLATFORM-1", self.change_id
            )
        self.assertIsNone(platform_type)


class DatafileTypeTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.resolver = CommandLineResolver()
        self.store = DataStore(
            "", "", "", 0, ":memory:", db_type="sqlite", missing_data_resolver=self.resolver,
        )
        self.store.initialise()
        with self.store.session_scope():
            self.change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_add_new_datafile_type(self, menu_prompt):
        """Test whether a new Datafile Type is added or not"""

        # Type "TEST"->Select "Yes"
        menu_prompt.side_effect = ["TEST", "1"]
        with self.store.session_scope():
            datafile_type = self.resolver.fuzzy_search_datafile_type(
                self.store, "DATAFILE-1", self.change_id
            )
            self.assertEqual(datafile_type.name, "TEST")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_datafile_type_recursive(self, menu_prompt):
        """Test whether recursive call works for Datafile Type"""

        # Type "TEST"->Select "No, I'd like to select a datafile type"->Type "DATAFILE-TYPE-1"
        menu_prompt.side_effect = ["TEST", "2", "DATAFILE-TYPE-1"]
        with self.store.session_scope():
            self.store.add_to_datafile_types("DATAFILE-TYPE-1", self.change_id)
            self.store.add_to_datafile_types("DATAFILE-TYPE-2", self.change_id)
            datafile_type = self.resolver.fuzzy_search_datafile_type(
                self.store, "DATAFILE-1", self.change_id
            )
            self.assertEqual(datafile_type.name, "DATAFILE-TYPE-1")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_cancelling_fuzzy_search_datafile_type(self, menu_prompt):
        """Test whether "." returns to the resolve datafile type"""

        menu_prompt.side_effect = [".", ".", "TEST", ".", "."]

        temp_output = StringIO()
        with self.store.session_scope():
            # Select "."->Select "."
            with redirect_stdout(temp_output):
                datafile_type = self.resolver.fuzzy_search_datafile_type(
                    self.store, "DATAFILE-1", self.change_id
                )
            output = temp_output.getvalue()
            self.assertIn("Returning to the previous menu", output)
            self.assertIsNone(datafile_type)

            # Type "TEST"->Select "."->Select "."
            with redirect_stdout(temp_output):
                datafile_type = self.resolver.fuzzy_search_datafile_type(
                    self.store, "DATAFILE-1", self.change_id
                )
            output = temp_output.getvalue()
            self.assertIn("Returning to the previous menu", output)
            self.assertIsNone(datafile_type)

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_resolve_datafile_type_add_new_datafile_type(self, resolver_prompt, menu_prompt):
        """Test whether a new Datafile Type is added or not"""

        # Select "Add a new datafile type" -> Type "TEST"
        menu_prompt.side_effect = ["2"]
        resolver_prompt.side_effect = ["TEST"]
        with self.store.session_scope():
            datafile_type = self.resolver.resolve_datafile_type(
                self.store, "DATAFILE-1", self.change_id
            )
            self.assertEqual(datafile_type.name, "TEST")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_cancelling_resolve_datafile_type(self, menu_prompt):
        """Test whether "." cancels the resolve datafile type and returns None"""
        menu_prompt.side_effect = ["."]
        with self.store.session_scope():
            datafile_type = self.resolver.resolve_datafile_type(
                self.store, "DATAFILE-1", self.change_id
            )
        self.assertIsNone(datafile_type)


class SensorTypeTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.resolver = CommandLineResolver()
        self.store = DataStore(
            "", "", "", 0, ":memory:", db_type="sqlite", missing_data_resolver=self.resolver,
        )
        self.store.initialise()
        with self.store.session_scope():
            self.change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_add_new_sensor_type(self, menu_prompt):
        """Test whether a new Sensor Type is added or not"""

        # Type "TEST"->Select "Yes"
        menu_prompt.side_effect = ["TEST", "1"]
        with self.store.session_scope():
            sensor_type = self.resolver.fuzzy_search_sensor_type(
                self.store, "SENSOR-1", self.change_id
            )
            self.assertEqual(sensor_type.name, "TEST")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_sensor_type_recursive(self, menu_prompt):
        """Test whether recursive call works for Sensor Type"""

        # Type "TEST"->Select "No, I'd like to select a sensor type"->Type "SENSOR-TYPE-1"
        menu_prompt.side_effect = ["TEST", "2", "SENSOR-TYPE-1"]
        with self.store.session_scope():
            self.store.add_to_sensor_types("SENSOR-TYPE-1", self.change_id)
            self.store.add_to_sensor_types("SENSOR-TYPE-2", self.change_id)
            sensor_type = self.resolver.fuzzy_search_sensor_type(
                self.store, "SENSOR-1", self.change_id
            )
            self.assertEqual(sensor_type.name, "SENSOR-TYPE-1")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_cancelling_fuzzy_search_sensor_type(self, menu_prompt):
        """Test whether "." returns to the resolver sensor type"""
        menu_prompt.side_effect = [".", ".", "TEST", ".", "."]

        with self.store.session_scope():
            temp_output = StringIO()
            # Select "."->Select "."
            with redirect_stdout(temp_output):
                sensor_type = self.resolver.fuzzy_search_sensor_type(
                    self.store, "SENSOR-1", self.change_id
                )
            output = temp_output.getvalue()
            self.assertIn("Returning to the previous menu", output)
            self.assertIsNone(sensor_type)

            # Type "TEST"->Select "."->Select "."
            with redirect_stdout(temp_output):
                sensor_type = self.resolver.fuzzy_search_sensor_type(
                    self.store, "SENSOR-1", self.change_id
                )
            output = temp_output.getvalue()
            self.assertIn("Returning to the previous menu", output)
            self.assertIsNone(sensor_type)

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_cancelling_resolve_sensor_type(self, menu_prompt):
        """Test whether "." cancels the resolve sensor type and returns None"""
        menu_prompt.side_effect = ["."]
        with self.store.session_scope():
            sensor_type = self.resolver.resolve_sensor_type(self.store, "SENSOR-1", self.change_id)
        self.assertIsNone(sensor_type)


class PlatformTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.resolver = CommandLineResolver()
        self.store = DataStore(
            "", "", "", 0, ":memory:", db_type="sqlite", missing_data_resolver=self.resolver,
        )
        self.store.initialise()
        with self.store.session_scope():
            self.change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_add_platform_to_synonym(self, menu_prompt):
        """Test whether entered platform name is added as a synonym or not"""

        # Search "PLATFORM-1"->Select "Yes"
        menu_prompt.side_effect = ["PLATFORM-1", "1"]
        with self.store.session_scope():
            privacy = self.store.add_to_privacies("PRIVACY-1", self.change_id)
            platform_type = self.store.add_to_platform_types("Warship", self.change_id)
            nationality = self.store.add_to_nationalities("UK", self.change_id)
            platform = self.store.get_platform(
                "PLATFORM-1",
                nationality=nationality.name,
                platform_type=platform_type.name,
                privacy=privacy.name,
                change_id=self.change_id,
            )

            synonym_platform = self.resolver.fuzzy_search_platform(
                self.store,
                "TEST",
                nationality=nationality.name,
                platform_type=platform_type.name,
                privacy=privacy.name,
                change_id=self.change_id,
            )

            self.assertEqual(platform.platform_id, synonym_platform.platform_id)

    @patch("pepys_import.resolvers.command_line_input.prompt")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_fuzzy_search_add_new_platform(self, resolver_prompt, menu_prompt):
        """Test whether a new platform entity is created or not"""

        # Search "PLATFORM-1"->Select "No"->Type name/trigraph/quadgraph/pennant number->Select "Yes"
        menu_prompt.side_effect = ["PLATFORM-1", "2", "1"]
        resolver_prompt.side_effect = ["TEST", "TST", "TEST", "123"]
        with self.store.session_scope():
            privacy = self.store.add_to_privacies("PRIVACY-1", self.change_id)
            platform_type = self.store.add_to_platform_types("Warship", self.change_id)
            nationality = self.store.add_to_nationalities("UK", self.change_id)
            self.store.get_platform(
                "PLATFORM-1",
                trigraph="PL1",
                quadgraph="PLT1",
                pennant_number="123",
                nationality=nationality.name,
                platform_type=platform_type.name,
                privacy=privacy.name,
                change_id=self.change_id,
            )

            (
                platform_name,
                trigraph,
                quadgraph,
                pennant_number,
                platform_type,
                nationality,
                privacy,
            ) = self.resolver.fuzzy_search_platform(
                self.store,
                "TEST",
                nationality=nationality.name,
                platform_type=platform_type.name,
                privacy=privacy.name,
                change_id=self.change_id,
            )

            self.assertEqual(platform_name, "TEST")
            self.assertEqual(trigraph, "TST")
            self.assertEqual(quadgraph, "TEST")
            self.assertEqual(pennant_number, "123")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_resolver_platform_with_fuzzy_searches(self, resolver_platform, menu_prompt):
        """Test whether correct entities return when fuzzy search for platform type, nationality
        and privacy are called"""

        # Select "Search for existing platform"->Type "TEST"->Type name/trigraph/quadgraph/pennant number
        # ->Select "Search for an existing nationality"->Select "UK"->Select "Search for an existing
        # platform type"->Select "Warship"->Select "Search for an existing classification"->Select
        # "PRIVACY-1"->Select "Yes"
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
            self.store.add_to_privacies("PRIVACY-1", self.change_id)
            self.store.add_to_platform_types("Warship", self.change_id)
            self.store.add_to_nationalities("UK", self.change_id)
            (
                platform_name,
                trigraph,
                quadgraph,
                pennant_number,
                platform_type,
                nationality,
                privacy,
            ) = self.resolver.resolve_platform(
                data_store=self.store,
                platform_name="TEST",
                platform_type=None,
                nationality=None,
                privacy=None,
                change_id=self.change_id,
            )
            self.assertEqual(platform_name, "TEST")
            self.assertEqual(trigraph, "TST")
            self.assertEqual(quadgraph, "TEST")
            self.assertEqual(pennant_number, "123")
            self.assertEqual(platform_type.name, "Warship")
            self.assertEqual(nationality.name, "UK")
            self.assertEqual(privacy.name, "PRIVACY-1")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_resolver_platform_with_new_values(self, resolver_prompt, menu_prompt):
        """Test whether new platform type, nationality and privacy entities are created for Platform
         or not"""

        # Select "Add a new platform"->Type name/trigraph/quadgraph/pennant number->Select
        # "Add a new nationality"->Select "UK"->Select "Add a new platform type"->Select "Warship
        # ->Select "Add a new classification"->Select "PRIVACY-1"->Select "Yes"
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
                trigraph,
                quadgraph,
                pennant_number,
                platform_type,
                nationality,
                privacy,
            ) = self.resolver.resolve_platform(
                data_store=self.store,
                platform_name="TEST",
                platform_type=None,
                nationality=None,
                privacy=None,
                change_id=self.change_id,
            )
            self.assertEqual(platform_name, "TEST")
            self.assertEqual(trigraph, "TST")
            self.assertEqual(quadgraph, "TEST")
            self.assertEqual(pennant_number, "123")
            self.assertEqual(platform_type.name, "Warship")
            self.assertEqual(nationality.name, "UK")
            self.assertEqual(privacy.name, "PRIVACY-1")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_resolver_platform_edit_given_values(self, resolver_prompt, menu_prompt):
        """Test a new platform is created after make further edits option is selected"""

        # Select "Add a new platform"->Type name/trigraph/quadgraph/pennant number->Select "No"->
        # Type name/trigraph/quadgraph/pennant number->Select "Search for an existing nationality"
        # ->Select "UK"->Select "Search for an existing platform type"->Select "Warship"->Select
        # "Search for an existing classification"->Select "PRIVACY-1"->Select "Yes"
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
            privacy = self.store.add_to_privacies("PRIVACY-1", self.change_id).name
            platform_type = self.store.add_to_platform_types("Warship", self.change_id).name
            nationality = self.store.add_to_nationalities("UK", self.change_id).name
            (
                platform_name,
                trigraph,
                quadgraph,
                pennant_number,
                platform_type,
                nationality,
                privacy,
            ) = self.resolver.resolve_platform(
                data_store=self.store,
                platform_name="TEST",
                platform_type=platform_type,
                nationality=nationality,
                privacy=privacy,
                change_id=self.change_id,
            )
            self.assertEqual(platform_name, "TEST")
            self.assertEqual(trigraph, "TST")
            self.assertEqual(quadgraph, "TEST")
            self.assertEqual(pennant_number, "123")
            self.assertEqual(platform_type.name, "Warship")
            self.assertEqual(nationality.name, "UK")
            self.assertEqual(privacy.name, "PRIVACY-1")


class DatafileTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.resolver = CommandLineResolver()
        self.store = DataStore(
            "", "", "", 0, ":memory:", db_type="sqlite", missing_data_resolver=self.resolver,
        )
        self.store.initialise()
        with self.store.session_scope():
            self.change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_resolver_datafile_edit_given_values(self, resolver_prompt, menu_prompt):
        """Test whether correct datafile type and privacy returns after resolver is further edited"""

        # Type "TEST"->Select "No"->Type "TEST"->Select "Search for an existing datafile-type"->
        # Search "DATAFILE-TYPE-2"->Select "Search for an existing classification"->Search
        # "PRIVACY-2"->Select "Yes"
        menu_prompt.side_effect = [
            "2",
            "1",
            "DATAFILE-TYPE-2",
            "1",
            "PRIVACY-2",
            "1",
        ]
        resolver_prompt.side_effect = ["TEST", "TEST"]
        with self.store.session_scope():
            privacy = self.store.add_to_privacies("PRIVACY-1", self.change_id).name
            self.store.add_to_privacies("PRIVACY-2", self.change_id)
            datafile_type = self.store.add_to_datafile_types("DATAFILE-TYPE-1", self.change_id).name
            self.store.add_to_datafile_types("DATAFILE-TYPE-2", self.change_id)
            (datafile_name, datafile_type, privacy,) = self.resolver.resolve_datafile(
                data_store=self.store,
                datafile_name="TEST",
                datafile_type=datafile_type,
                privacy=privacy,
                change_id=self.change_id,
            )
            self.assertEqual(datafile_name, "TEST")
            self.assertEqual(datafile_type.name, "DATAFILE-TYPE-2")
            self.assertEqual(privacy.name, "PRIVACY-2")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_resolver_datafile_add_new_datafile(self, resolver_prompt, menu_prompt):
        """Test whether the correct datafile type and privacy entities are returned after searched
        and not found in Datafile Table."""

        # Type "TEST"->Select "Search for an existing datafile type"->Search "DATAFILE-TYPE-1"->
        # Select "Search for an existing classification"->Search "PRIVACY-1->Select "Yes"
        menu_prompt.side_effect = [
            "1",
            "DATAFILE-TYPE-1",
            "1",
            "PRIVACY-1",
            "1",
        ]
        resolver_prompt.side_effect = ["TEST"]
        with self.store.session_scope():
            self.store.add_to_privacies("PRIVACY-1", self.change_id)
            self.store.add_to_datafile_types("DATAFILE-TYPE-1", self.change_id)
            datafile_name, datafile_type, privacy = self.resolver.resolve_datafile(
                data_store=self.store,
                datafile_name=None,
                datafile_type=None,
                privacy=None,
                change_id=self.change_id,
            )
            self.assertEqual(datafile_name, "TEST")
            self.assertEqual(datafile_type.name, "DATAFILE-TYPE-1")
            self.assertEqual(privacy.name, "PRIVACY-1")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_quitting(self, resolver_prompt, menu_prompt):
        menu_prompt.side_effect = [
            ".",
            ".",
            ".",
        ]
        resolver_prompt.side_effect = ["TEST", "TEST", "TEST"]
        with self.store.session_scope():
            privacy = self.store.add_to_privacies("PRIVACY-1", self.change_id).name
            datafile_type = self.store.add_to_datafile_types("DATAFILE-TYPE-1", self.change_id).name
            with self.assertRaises(SystemExit):
                self.resolver.resolve_datafile(
                    data_store=self.store,
                    datafile_name="TEST",
                    datafile_type=datafile_type,
                    privacy=privacy,
                    change_id=self.change_id,
                )
            with self.assertRaises(SystemExit):
                self.resolver.resolve_datafile(
                    data_store=self.store,
                    datafile_name="TEST",
                    datafile_type=None,
                    privacy=privacy,
                    change_id=self.change_id,
                )
            with self.assertRaises(SystemExit):
                self.resolver.resolve_datafile(
                    data_store=self.store,
                    datafile_name="TEST",
                    datafile_type=datafile_type,
                    privacy=None,
                    change_id=self.change_id,
                )


class SensorTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.resolver = CommandLineResolver()
        self.store = DataStore(
            "", "", "", 0, ":memory:", db_type="sqlite", missing_data_resolver=self.resolver,
        )
        self.store.initialise()
        with self.store.session_scope():
            self.change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_resolve_sensor(self, resolver_prompt, menu_prompt):
        """Test whether correct sensor type and privacy entities are resolved or not"""

        # Select "Add a new sensor"->Type "TEST"->Select "Add a new sensor-type"->
        # Type "SENSOR-TYPE-1"->Select "Add a new classification"->Type "PRIVACY-1"->Select "Yes"
        menu_prompt.side_effect = ["2", "2", "2", "1"]
        resolver_prompt.side_effect = ["TEST", "SENSOR-TYPE-1", "PRIVACY-1"]
        with self.store.session_scope():
            self.store.add_to_sensor_types("SENSOR-TYPE-1", self.change_id)
            self.store.add_to_privacies("PRIVACY-1", self.change_id)
            sensor_name, sensor_type, privacy = self.resolver.resolve_sensor(
                self.store, "TEST", sensor_type=None, privacy=None, change_id=self.change_id,
            )

            self.assertEqual(sensor_name, "TEST")
            self.assertEqual(sensor_type.name, "SENSOR-TYPE-1")
            self.assertEqual(privacy.name, "PRIVACY-1")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_resolve_sensor_add_to_synonyms(self, menu_prompt):
        """Test whether the given sensor name is correctly added to Synonyms table or not"""

        # Select "Search an existing sensor"->Search "SENSOR-1"->Select "Yes"
        menu_prompt.side_effect = ["1", "SENSOR-1", "1"]
        with self.store.session_scope():
            # Create platform first, then create a Sensor object
            sensor_type = self.store.add_to_sensor_types("SENSOR-TYPE-1", self.change_id).name
            privacy = self.store.add_to_privacies("PRIVACY-1", self.change_id).name
            nationality = self.store.add_to_nationalities("UK", self.change_id).name
            platform_type = self.store.add_to_platform_types("PLATFORM-TYPE-1", self.change_id).name
            platform = self.store.get_platform(
                platform_name="Test Platform",
                nationality=nationality,
                platform_type=platform_type,
                privacy=privacy,
                change_id=self.change_id,
            )
            sensor = platform.get_sensor(
                self.store, "SENSOR-1", sensor_type, privacy, change_id=self.change_id
            )

            synonym_sensor = self.resolver.resolve_sensor(
                self.store, "SENSOR-TEST", sensor_type, privacy, change_id=self.change_id,
            )
            self.assertEqual(synonym_sensor.sensor_id, sensor.sensor_id)

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_resolver_sensor_make_further_edit(self, resolver_prompt, menu_prompt):
        """Test whether correct sensor type and privacy returns after resolver is further edited"""

        # Select "Add a new sensor"->Type "TEST"->Select "No"->Type "TEST"->
        # Select "Search for an existing sensor-type"->Search "SENSOR-TYPE-2"->
        # Select "Search for an existing classification"->Search "PRIVACY-2"->Select "Yes"
        menu_prompt.side_effect = [
            "2",
            "2",
            "1",
            "SENSOR-TYPE-2",
            "1",
            "PRIVACY-2",
            "1",
        ]
        resolver_prompt.side_effect = ["TEST", "TEST"]
        with self.store.session_scope():
            sensor_type = self.store.add_to_sensor_types("SENSOR-TYPE-1", self.change_id)
            sensor_type_2 = self.store.add_to_sensor_types("SENSOR-TYPE-2", self.change_id)
            privacy = self.store.add_to_privacies("PRIVACY-1", self.change_id)
            privacy_2 = self.store.add_to_privacies("PRIVACY-2", self.change_id)
            (resolved_name, resolved_type, resolved_privacy,) = self.resolver.resolve_sensor(
                self.store, "TEST", sensor_type.name, privacy.name, self.change_id
            )
            self.assertEqual(resolved_name, "TEST")
            self.assertEqual(resolved_type.sensor_type_id, sensor_type_2.sensor_type_id)
            self.assertEqual(resolved_privacy.privacy_id, privacy_2.privacy_id)

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_fuzzy_search_add_sensor(self, resolver_prompt, menu_prompt):
        """Test whether a new Sensor entity created or not after searched
        and not founded in the Sensor Table."""

        # Select "Search an existing sensor"->Search "SENSOR-1"->Select "No"->Type "SENSOR-TEST"->
        # Select "Search for an existing sensor-type"->Search "SENSOR-TYPE-1"->
        # Select "Search an existing classification"->Search "PRIVACY-1"->Select "Yes"
        menu_prompt.side_effect = [
            "1",
            "SENSOR-1",
            "2",
            "1",
            "SENSOR-TYPE-1",
            "1",
            "PRIVACY-1",
            "1",
        ]
        resolver_prompt.side_effect = ["SENSOR-TEST"]
        with self.store.session_scope():
            # Create platform first, then create a Sensor object
            sensor_type = self.store.add_to_sensor_types("SENSOR-TYPE-1", self.change_id).name
            privacy = self.store.add_to_privacies("PRIVACY-1", self.change_id).name
            nationality = self.store.add_to_nationalities("UK", self.change_id).name
            platform_type = self.store.add_to_platform_types("PLATFORM-TYPE-1", self.change_id).name
            platform = self.store.get_platform(
                platform_name="Test Platform",
                nationality=nationality,
                platform_type=platform_type,
                privacy=privacy,
                change_id=self.change_id,
            )
            platform.get_sensor(self.store, "SENSOR-1", sensor_type, privacy, self.change_id)
            platform.get_sensor(self.store, "SENSOR-2", sensor_type, privacy, self.change_id)

            sensor_name, sensor_type, privacy = self.resolver.resolve_sensor(
                self.store, "SENSOR-TEST", sensor_type=None, privacy=None, change_id=self.change_id,
            )

            self.assertEqual(sensor_name, "SENSOR-TEST")
            self.assertEqual(sensor_type.name, "SENSOR-TYPE-1")
            self.assertEqual(privacy.name, "PRIVACY-1")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_fuzzy_search_add_sensor_alternative(self, resolver_prompt, menu_prompt):
        """Test whether a new Sensor entity created when the Sensor Table is empty."""

        # Select "Search an existing sensor"->Search "SENSOR-1"->Type "SENSOR-TEST"->Select "Yes"
        menu_prompt.side_effect = [
            "1",
            "SENSOR-1",
            "1",
        ]
        resolver_prompt.side_effect = ["SENSOR-TEST"]
        with self.store.session_scope():
            sensor_type = self.store.add_to_sensor_types("SENSOR-TYPE-1", self.change_id)
            privacy = self.store.add_to_privacies("PRIVACY-1", self.change_id).name

            sensor_name, sensor_type, privacy = self.resolver.resolve_sensor(
                self.store,
                "SENSOR-TEST",
                sensor_type=sensor_type.name,
                privacy=privacy,
                change_id=self.change_id,
            )

            self.assertEqual(sensor_name, "SENSOR-TEST")


class CancellingAndReturnPreviousMenuTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.resolver = CommandLineResolver()
        self.store = DataStore(
            "", "", "", 0, ":memory:", db_type="sqlite", missing_data_resolver=self.resolver,
        )
        self.store.initialise()
        with self.store.session_scope():
            self.change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_top_level_quitting(self, menu_prompt):
        """Test whether "." quits from the resolve platform/sensor"""
        menu_prompt.side_effect = [".", ".", "."]
        with self.store.session_scope():
            with self.assertRaises(SystemExit):
                self.resolver.resolve_platform(self.store, "", "", "", "", self.change_id)
            with self.assertRaises(SystemExit):
                self.resolver.resolve_sensor(self.store, "", "", "", self.change_id)

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_cancelling_fuzzy_search_platform(self, menu_prompt):
        """Test whether "." returns to resolve platform"""

        # Search "PLATFORM-1"->Select "."->Select "."->Select "."
        menu_prompt.side_effect = ["PLATFORM-1", ".", ".", "."]
        with self.store.session_scope():
            privacy = self.store.add_to_privacies("PRIVACY-1", self.change_id)
            platform_type = self.store.add_to_platform_types("Warship", self.change_id)
            nationality = self.store.add_to_nationalities("UK", self.change_id)
            self.store.get_platform(
                "PLATFORM-1",
                nationality=nationality.name,
                platform_type=platform_type.name,
                privacy=privacy.name,
                change_id=self.change_id,
            )
            with self.assertRaises(SystemExit):
                self.resolver.fuzzy_search_platform(self.store, "TEST", "", "", "", self.change_id)

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_cancelling_fuzzy_search_sensor(self, menu_prompt):
        """Test whether "." returns to resolve sensor"""

        # Type "SENSOR-1"->Select "."->Select "."->Select "."
        menu_prompt.side_effect = ["SENSOR-1", ".", ".", "."]
        with self.store.session_scope():
            sensor_type = self.store.add_to_sensor_types("SENSOR-TYPE-1", self.change_id).name
            privacy = self.store.add_to_privacies("PRIVACY-1", self.change_id).name
            nationality = self.store.add_to_nationalities("UK", self.change_id).name
            platform_type = self.store.add_to_platform_types("PLATFORM-TYPE-1", self.change_id).name
            platform = self.store.get_platform(
                platform_name="Test Platform",
                nationality=nationality,
                platform_type=platform_type,
                privacy=privacy,
                change_id=self.change_id,
            )
            platform.get_sensor(self.store, "SENSOR-1", sensor_type, privacy, self.change_id)

            with self.assertRaises(SystemExit):
                self.resolver.fuzzy_search_sensor(self.store, "TEST", "", "", self.change_id)

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_cancelling_during_add_to_platforms(self, resolver_prompt, menu_prompt):
        menu_prompt.side_effect = [
            ".",
            ".",
            "2",
            ".",
            ".",
            "2",
            "2",
            ".",
            ".",
            "2",
            "2",
            "2",
            ".",
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
            "UK",
            "TEST",
            "TST",
            "TEST",
            "123",
            "UK",
            "TYPE-1",
            "TEST",
            "TST",
            "TEST",
            "123",
            "UK",
            "TYPE-1",
            "PRIVACY-1",
        ]
        with self.store.session_scope():
            # Type name/trigraph/quadgraph/pennant number->Select "Cancel nationality search"->
            # Select "Cancel import"
            with self.assertRaises(SystemExit):
                self.resolver.add_to_platforms(self.store, "PLATFORM-1", "", "", "", self.change_id)
            # Type name/trigraph/quadgraph/pennant number->Select "Add new nationality"->Type "UK"->
            # Select "Cancel platform type search"->Select "Cancel import"
            with self.assertRaises(SystemExit):
                self.resolver.add_to_platforms(self.store, "PLATFORM-1", "", "", "", self.change_id)
            # Type name/trigraph/quadgraph/pennant number->Select "Add new nationality"->Type "UK"->
            # Select "Add a new platform type"->Type "TYPE-1"->Select "Cancel classification search"->
            # Select "Cancel import"
            with self.assertRaises(SystemExit):
                self.resolver.add_to_platforms(self.store, "PLATFORM-1", "", "", "", self.change_id)
            # Type name/trigraph/quadgraph/pennant number->Select "Add new nationality"->Type "UK"->
            # Select "Add a new platform type"->Select "Add new classification"->Type "PRIVACY-1"->Type
            # "TYPE-1"->Select "Cancel import"->Select "Cancel import"
            with self.assertRaises(SystemExit):
                self.resolver.add_to_platforms(self.store, "PLATFORM-1", "", "", "", self.change_id)

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_cancelling_during_add_to_sensors(self, resolver_prompt, menu_prompt):
        menu_prompt.side_effect = [".", ".", "2", ".", ".", "2", "2", ".", "."]
        resolver_prompt.side_effect = [
            "TEST",
            "TEST",
            "SENSOR-TYPE-1",
            "TEST",
            "SENSOR-TYPE-1",
            "PRIVACY-1",
        ]
        with self.store.session_scope():
            # Type "TEST"->Select "Cancel sensor type search"->Select "Cancel import"
            with self.assertRaises(SystemExit):
                self.resolver.add_to_sensors(self.store, "SENSOR-1", "", "", self.change_id)
            # Type "TEST"->Select "Add a new sensor type"->Type "SENSOR-TYPE-1->
            # Select "Cancel classification search" ->Select "Cancel import"
            with self.assertRaises(SystemExit):
                self.resolver.add_to_sensors(self.store, "SENSOR-1", "", "", self.change_id)
            # Type "TEST"->Select "Add a new sensor type"->Type "SENSOR-TYPE-1->
            # Select "Add a new classification"->Type "PRIVACY-1"->Select "Cancel import"->
            # Select "Cancel import"
            with self.assertRaises(SystemExit):
                self.resolver.add_to_sensors(self.store, "SENSOR-1", "", "", self.change_id)


class GetMethodsTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.file_path = os.path.join(DIR_PATH, "test.db")
        self.store = DataStore(
            "",
            "",
            "",
            0,
            self.file_path,
            db_type="sqlite",
            missing_data_resolver=CommandLineResolver(),
        )
        self.store.initialise()
        with self.store.session_scope():
            self.store.populate_reference()
            self.store.populate_metadata()
            self.store.populate_measurement()
            self.change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id

    def tearDown(self) -> None:
        if os.path.exists(self.file_path):
            os.remove(self.file_path)

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_get_platform_adds_resolved_platform_successfully(self, resolver_prompt, menu_prompt):
        menu_prompt.side_effect = [
            "2",
            "1",
            "UK",
            "1",
            "Fisher",
            "1",
            "PRIVACY-1",
            "1",
        ]
        resolver_prompt.side_effect = ["Test Platform", "Tst", "Test", "123"]
        with self.store.session_scope():
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            # there must be 2 entities at the beginning
            self.assertEqual(len(platforms), 2)

            self.store.get_platform("Test Platform", change_id=self.change_id)

            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            self.assertEqual(len(platforms), 3)
            self.assertEqual(platforms[2].name, "Test Platform")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_get_datafile_adds_resolved_datafile_successfully(self, resolver_prompt, menu_prompt):
        menu_prompt.side_effect = [
            "1",
            "DATAFILE-TYPE-1",
            "1",
            "PRIVACY-1",
            "1",
        ]
        resolver_prompt.side_effect = ["DATAFILE-TEST"]
        with self.store.session_scope():
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            # there must be 2 entities at the beginning
            self.assertEqual(len(datafiles), 2)

            self.store.get_datafile("test", None, 0, "HASHED", change_id=self.change_id)

            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 3)
            self.assertEqual(datafiles[2].reference, "DATAFILE-TEST")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_get_sensor_adds_resolved_sensor_successfully(self, resolver_prompt, menu_prompt):
        menu_prompt.side_effect = [
            "2",
            "1",
            "SENSOR-TYPE-1",
            "1",
            "PRIVACY-1",
            "1",
        ]
        resolver_prompt.side_effect = ["SENSOR-TEST"]
        with self.store.session_scope():
            sensors = self.store.session.query(self.store.db_classes.Sensor).all()
            # there must be 2 entities at the beginning
            self.assertEqual(len(sensors), 2)

            platform = self.store.get_platform("PLATFORM-1", change_id=self.change_id)
            platform.get_sensor(self.store, "SENSOR-TEST", change_id=self.change_id)

            # there must be 3 entities now
            sensors = self.store.session.query(self.store.db_classes.Sensor).all()
            self.assertEqual(len(sensors), 3)
            self.assertEqual(sensors[2].name, "SENSOR-TEST")


if __name__ == "__main__":
    unittest.main()
