import os
import unittest
from contextlib import redirect_stdout
from datetime import datetime
from io import StringIO
from unittest.mock import patch
from uuid import uuid4

import pytest
from prompt_toolkit.document import Document
from prompt_toolkit.validation import ValidationError

from pepys_import.core.store.data_store import DataStore
from pepys_import.resolvers import constants
from pepys_import.resolvers.command_line_input import is_valid
from pepys_import.resolvers.command_line_resolver import (
    CommandLineResolver,
    MinMaxValidator,
    is_number,
)
from pepys_import.utils.text_formatting_utils import formatted_text_to_str

DIR_PATH = os.path.dirname(__file__)


class ReferenceDataTestCase(unittest.TestCase):
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
        with self.store.session_scope():
            self.change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_select_existing_privacy(self, menu_prompt):
        """Test whether an existing Privacy entity searched and returned or not"""

        # Select "Search an existing classification"->Search "PRIVACY-TEST"
        menu_prompt.side_effect = ["1", "PRIVACY-TEST"]
        with self.store.session_scope():
            self.store.add_to_privacies("PRIVACY-TEST", 0, self.change_id)
            privacy = self.resolver.resolve_reference(
                self.store,
                self.change_id,
                "",
                self.store.db_classes.Privacy,
                "privacy",
                "classification",
                "",
                "",
            )
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
            self.store.add_to_privacies("PRIVACY-TEST", 0, self.change_id)
            privacy = self.resolver.resolve_reference(
                self.store,
                self.change_id,
                "",
                self.store.db_classes.Privacy,
                "privacy",
                "classification",
                "",
                "",
            )
            self.assertEqual(privacy.name, "PRIVACY-TEST")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_recursive_privacy(self, menu_prompt):
        """Test whether recursive call works for privacy"""

        # Select "Search an existing classification"->Search "PRIVACY-TEST"->Select "No"
        # ->Search "Public"
        menu_prompt.side_effect = ["1", "PRIVACY-TEST", "2", "Public"]
        with self.store.session_scope():
            self.store.add_to_privacies("Public", 0, self.change_id)
            self.store.add_to_privacies("Public Sensitive", 0, self.change_id)
            privacy = self.resolver.resolve_reference(
                self.store,
                self.change_id,
                "",
                self.store.db_classes.Privacy,
                "privacy",
                "classification",
                "",
                "",
            )
            self.assertEqual(privacy.name, "Public")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_select_privacy_directly(self, menu_prompt):
        """Test whether recursive call works for privacy"""

        # Select "2-Public"
        menu_prompt.side_effect = ["2"]
        with self.store.session_scope():
            self.store.add_to_privacies("Public", 0, self.change_id)
            self.store.add_to_privacies("Public Sensitive", 0, self.change_id)
            privacy = self.resolver.resolve_reference(
                self.store,
                self.change_id,
                "",
                self.store.db_classes.Privacy,
                "privacy",
                "classification",
                "",
                "",
            )
            self.assertEqual(privacy.name, "Public")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_select_existing_platform_type(self, menu_prompt):
        """Test whether an existing PlatformType entity searched and returned or not"""

        # Select "Search an existing platform-type"->Search "TYPE-TEST"
        menu_prompt.side_effect = ["1", "TYPE-TEST"]
        with self.store.session_scope():
            self.store.add_to_platform_types("TYPE-TEST", self.change_id)
            platform_type = self.resolver.resolve_reference(
                self.store,
                self.change_id,
                "",
                self.store.db_classes.PlatformType,
                "platform_type",
                "",
                "",
            )
            assert platform_type.__tablename__ == "PlatformTypes"
            assert platform_type.name == "TYPE-TEST"

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_recursive_platform_type(self, menu_prompt):
        """Test whether recursive call works for platform_type"""

        # Select "Search an existing platform-type"->Search "TYPE-TEST"->Select "No"
        # ->Search "TYPE-1"
        menu_prompt.side_effect = ["1", "TYPE-TEST", "2", "TYPE-1"]
        with self.store.session_scope():
            self.store.add_to_platform_types("TYPE-1", self.change_id)
            self.store.add_to_platform_types("TYPE-2", self.change_id)
            platform_type = self.resolver.resolve_reference(
                self.store,
                self.change_id,
                "",
                self.store.db_classes.PlatformType,
                "platform_type",
                "",
                "",
            )
            self.assertEqual(platform_type.name, "TYPE-1")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_select_platform_type_directly(self, menu_prompt):
        """Test whether recursive call works for platform_type"""

        # Select "2-TYPE-1"
        menu_prompt.side_effect = ["2"]
        with self.store.session_scope():
            self.store.add_to_platform_types("TYPE-1", self.change_id)
            self.store.add_to_platform_types("TYPE-2", self.change_id)
            platform_type = self.resolver.resolve_reference(
                self.store,
                self.change_id,
                "",
                self.store.db_classes.PlatformType,
                "platform_type",
                "",
                "",
            )
            self.assertEqual(platform_type.name, "TYPE-1")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_resolver_reference_select_nationality_directly(self, menu_prompt):
        # Select "3-UK"
        menu_prompt.side_effect = ["2", "3", "4", "5"]
        with self.store.session_scope():
            self.store.add_to_nationalities("UK", self.change_id, priority=1)
            self.store.add_to_nationalities("FR", self.change_id, priority=2)
            self.store.add_to_nationalities("TR", self.change_id, priority=2)
            self.store.add_to_nationalities("AAA", self.change_id, priority=3)
            nationality = self.resolver.resolve_reference(
                self.store,
                self.change_id,
                "",
                self.store.db_classes.Nationality,
                "nationality",
                "",
                "",
            )
            assert nationality.name == "UK"

            nationality = self.resolver.resolve_reference(
                self.store,
                self.change_id,
                "",
                self.store.db_classes.Nationality,
                "nationality",
                "",
                "",
            )
            assert nationality.name == "FR"

            nationality = self.resolver.resolve_reference(
                self.store,
                self.change_id,
                "",
                self.store.db_classes.Nationality,
                "nationality",
                "",
                "",
            )
            assert nationality.name == "TR"

            nationality = self.resolver.resolve_reference(
                self.store,
                self.change_id,
                "",
                self.store.db_classes.Nationality,
                "nationality",
                "",
                "",
            )
            assert nationality is None

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_cancelling_fuzzy_search_reference(self, menu_prompt):
        """Test whether "." returns to the resolver privacy"""

        # Search "TEST"->Select "."->Select "."
        menu_prompt.side_effect = ["TEST", ".", "."]
        with self.store.session_scope():
            privacy = self.resolver.fuzzy_search_reference(
                self.store,
                self.change_id,
                "",
                self.store.db_classes.Privacy,
                "privacy",
                "classification",
                "",
                "",
            )
            self.assertIsNone(privacy)

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_cancelling_resolver_reference(self, menu_prompt):
        """Test whether "." cancels the resolve privacy and returns None"""
        menu_prompt.side_effect = [".", "1", ".", "."]
        temp_output = StringIO()
        with self.store.session_scope():
            # Select "."
            privacy = self.resolver.resolve_reference(
                self.store,
                self.change_id,
                "",
                self.store.db_classes.Privacy,
                "privacy",
                "classification",
                "",
                "",
            )
            self.assertIsNone(privacy)

            with redirect_stdout(temp_output):
                privacy = self.resolver.resolve_reference(
                    self.store,
                    self.change_id,
                    "",
                    self.store.db_classes.Privacy,
                    "privacy",
                    "classification",
                    "",
                    "",
                )
            assert privacy is None
        output = temp_output.getvalue()
        assert "Returning to the previous menu" in output

    @patch("pepys_import.utils.text_formatting_utils.input")
    @patch("pepys_import.utils.text_formatting_utils.custom_print_formatted_text")
    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_resolve_reference_print_help_text(self, menu_prompt, mock_print, mock_input):
        # Use normal print() to capture table reports
        def side_effect(text):
            print(formatted_text_to_str(text))

        mock_print.side_effect = side_effect
        mock_input.return_value = "Enter"
        with self.store.session_scope():  # necessary for importing help texts
            self.store.populate_reference()

        menu_prompt.side_effect = ["?", "HELP", "3"]
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.resolver.resolve_reference(
                data_store=self.store,
                change_id=self.change_id,
                data_type="Platform",
                db_class=self.store.db_classes.Nationality,
                field_name="nationality",
                help_id=constants.RESOLVE_NATIONALITY,
                search_help_id=constants.FUZZY_SEARCH_NATIONALITY,
            )
        output = temp_output.getvalue()
        assert constants.RESOLVE_NATIONALITY in output

    @patch("pepys_import.utils.text_formatting_utils.input")
    @patch("pepys_import.utils.text_formatting_utils.custom_print_formatted_text")
    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_reference_print_help_text(self, menu_prompt, mock_print, mock_input):
        # Use normal print() to capture table reports
        def side_effect(text):
            print(formatted_text_to_str(text))

        mock_print.side_effect = side_effect
        mock_input.return_value = "Enter"
        with self.store.session_scope():  # necessary for importing help texts
            self.store.populate_reference()

        menu_prompt.side_effect = ["?", "HELP", "United Kingdom"]
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.resolver.fuzzy_search_reference(
                data_store=self.store,
                change_id=self.change_id,
                data_type="Platform",
                db_class=self.store.db_classes.Nationality,
                field_name="nationality",
                help_id=constants.RESOLVE_NATIONALITY,
                search_help_id=constants.FUZZY_SEARCH_NATIONALITY,
            )
        output = temp_output.getvalue()
        assert constants.FUZZY_SEARCH_NATIONALITY in output


class PlatformTestCase(unittest.TestCase):
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
        with self.store.session_scope():
            self.store.populate_reference()
            self.change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_add_platform_to_synonym(self, menu_prompt):
        """Test whether entered platform name is added as a synonym or not"""

        # Search "PLATFORM-1"->Select "Yes"
        menu_prompt.side_effect = ["PLATFORM-1 / 123 / UK", "1"]
        with self.store.session_scope():
            privacy = self.store.add_to_privacies("Public", 0, self.change_id)
            platform_type = self.store.add_to_platform_types("Naval - frigate", self.change_id)
            nationality = self.store.add_to_nationalities("UK", self.change_id)

            platform = self.store.add_to_platforms(
                "PLATFORM-1",
                identifier="123",
                nationality=nationality.name,
                platform_type=platform_type.name,
                privacy=privacy.name,
                change_id=self.change_id,
            )

            synonym_platform = self.resolver.fuzzy_search_platform(
                self.store,
                "TEST",
                identifier=None,
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

        # Search "PLATFORM-1"->Select "No"->Type name/trigraph/quadgraph/idedntification->Select "Yes"
        menu_prompt.side_effect = ["TEST", "1"]
        resolver_prompt.side_effect = ["TEST", "123", "TST", "TEST"]
        with self.store.session_scope():
            privacy = self.store.add_to_privacies("Public", 0, self.change_id)
            platform_type = self.store.add_to_platform_types("Naval - frigate", self.change_id)
            nationality = self.store.add_to_nationalities("UK", self.change_id)
            self.store.add_to_platforms(
                "PLATFORM-1",
                trigraph="PL1",
                quadgraph="PLT1",
                identifier="123",
                nationality=nationality.name,
                platform_type=platform_type.name,
                privacy=privacy.name,
                change_id=self.change_id,
            )

            (
                platform_name,
                trigraph,
                quadgraph,
                identifier,
                platform_type,
                nationality,
                privacy,
            ) = self.resolver.fuzzy_search_platform(
                self.store,
                "TEST",
                identifier=None,
                nationality=nationality.name,
                platform_type=platform_type.name,
                privacy=privacy.name,
                change_id=self.change_id,
            )

            self.assertEqual(platform_name, "TEST")
            self.assertEqual(trigraph, "TST")
            self.assertEqual(quadgraph, "TEST")
            self.assertEqual(identifier, "123")

    @patch("pepys_import.resolvers.command_line_input.prompt")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_resolve_platform_select_existing_platform(self, resolver_prompt, menu_prompt):
        """Test whether a new platform entity is created or not"""

        menu_prompt.side_effect = ["5"]
        with self.store.session_scope():
            privacy = self.store.add_to_privacies("Public", 0, self.change_id)
            platform_type = self.store.add_to_platform_types("Naval - frigate", self.change_id)
            uk_nat = self.store.add_to_nationalities("UK", priority=1, change_id=self.change_id)
            fr_nat = self.store.add_to_nationalities("France", priority=2, change_id=self.change_id)
            self.store.add_to_platforms(
                "PLATFORM-1",
                trigraph="PL1",
                quadgraph="PLT1",
                identifier="123",
                nationality=uk_nat.name,
                platform_type=platform_type.name,
                privacy=privacy.name,
                change_id=self.change_id,
            )

            self.store.add_to_platforms(
                "PLATFORM-1",
                trigraph="PL1",
                quadgraph="PLT1",
                identifier="123",
                nationality=fr_nat.name,
                platform_type=platform_type.name,
                privacy=privacy.name,
                change_id=self.change_id,
            )

            resolved_platform = self.resolver.resolve_platform(
                self.store,
                "PLATFORM-1",
                "",
                "",
                "",
                "",
                change_id=self.change_id,
            )

            assert resolved_platform.name == "PLATFORM-1"
            assert resolved_platform.nationality_name == "UK"
            assert resolved_platform.identifier == "123"

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_resolver_platform_with_fuzzy_searches(self, resolver_platform, menu_prompt):
        """Test whether correct entities return when fuzzy search for platform type, nationality
        and privacy are called"""

        # Select "Search for existing platform"->Type "TEST"->Type name/trigraph/quadgraph/identifier
        # ->Select "Search for an existing nationality"->Select "UK"->Select "Search for an existing
        # platform type"->Select "Naval - frigate"->Select "Search for an existing classification"->Select
        # "Public"->Select "Yes"
        menu_prompt.side_effect = [
            "2",
            "TEST",
            "1",
            "UK",
            "1",
            "Naval - frigate",
            "1",
            "Public",
            "1",
        ]
        resolver_platform.side_effect = ["TEST", "123", "TST", "TEST"]
        with self.store.session_scope():
            self.store.add_to_privacies("Public", 0, self.change_id)
            self.store.add_to_platform_types("Naval - frigate", self.change_id)
            self.store.add_to_nationalities("UK", self.change_id)
            (
                platform_name,
                trigraph,
                quadgraph,
                identifier,
                platform_type,
                nationality,
                privacy,
            ) = self.resolver.resolve_platform(
                data_store=self.store,
                platform_name="TEST",
                identifier=None,
                platform_type=None,
                nationality=None,
                privacy=None,
                change_id=self.change_id,
            )
            self.assertEqual(platform_name, "TEST")
            self.assertEqual(trigraph, "TST")
            self.assertEqual(quadgraph, "TEST")
            self.assertEqual(identifier, "123")
            self.assertEqual(platform_type.name, "Naval - frigate")
            self.assertEqual(nationality.name, "UK")
            self.assertEqual(privacy.name, "Public")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_resolver_platform_edit_given_values(self, resolver_prompt, menu_prompt):
        """Test a new platform is created after make further edits option is selected"""

        # Select "Add a new platform"->Type name/trigraph/quadgraph/identifier->
        # Select "No, make further edits"->Type name/trigraph/quadgraph/identifier->
        # Select "Search for an existing nationality"->Select "UK"->
        # Select "Search for an existing platform type"->Select "Naval - frigate"->Select
        # "Search for an existing classification"->Select "Public"->Select "Yes"
        menu_prompt.side_effect = [
            "1",
            "2",
            "1",
            "UK",
            "1",
            "Naval - frigate",
            "1",
            "Public",
            "1",
        ]
        resolver_prompt.side_effect = [
            "TEST",
            "123",
            "TST",
            "TEST",
            "TEST",
            "123",
            "TST",
            "TEST",
        ]
        with self.store.session_scope():
            privacy = self.store.add_to_privacies("Public", 0, self.change_id).name
            platform_type = self.store.add_to_platform_types("Naval - frigate", self.change_id).name
            nationality = self.store.add_to_nationalities("UK", self.change_id).name
            (
                platform_name,
                trigraph,
                quadgraph,
                identifier,
                platform_type,
                nationality,
                privacy,
            ) = self.resolver.resolve_platform(
                data_store=self.store,
                platform_name=None,
                identifier=None,
                platform_type=platform_type,
                nationality=nationality,
                privacy=privacy,
                change_id=self.change_id,
            )
            self.assertEqual(platform_name, "TEST")
            self.assertEqual(trigraph, "TST")
            self.assertEqual(quadgraph, "TEST")
            self.assertEqual(identifier, "123")
            self.assertEqual(platform_type.name, "Naval - frigate")
            self.assertEqual(nationality.name, "UK")
            self.assertEqual(privacy.name, "Public")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_resolver_platform_edit_given_values_2(self, resolver_prompt, menu_prompt):
        """Test a new platform is created after make further edits option is selected"""

        # Select "Add a new platform"->Type name/trigraph/quadgraph/identifier->Select "No"->
        # Select "Add a new platform"->Type name/trigraph/quadgraph/identifier->
        # Select "Search for an existing nationality"->Select "UK"->
        # Select "Search for an existing platform type"->Select "Naval - frigate"->Select
        # "Search for an existing classification"->Select "Public"->Select "Yes"
        menu_prompt.side_effect = [
            "1",
            "3",
            "1",
            "1",
            "UK",
            "1",
            "Naval - frigate",
            "1",
            "Public",
            "1",
        ]
        resolver_prompt.side_effect = [
            "TEST",
            "123",
            "TST",
            "TEST",
            "TEST",
            "123",
            "TST",
            "TEST",
        ]
        with self.store.session_scope():
            privacy = self.store.add_to_privacies("Public", 0, self.change_id).name
            platform_type = self.store.add_to_platform_types("Naval - frigate", self.change_id).name
            nationality = self.store.add_to_nationalities("UK", self.change_id).name
            (
                platform_name,
                trigraph,
                quadgraph,
                identifier,
                platform_type,
                nationality,
                privacy,
            ) = self.resolver.resolve_platform(
                data_store=self.store,
                platform_name=None,
                identifier=None,
                platform_type=platform_type,
                nationality=nationality,
                privacy=privacy,
                change_id=self.change_id,
            )
            self.assertEqual(platform_name, "TEST")
            self.assertEqual(trigraph, "TST")
            self.assertEqual(quadgraph, "TEST")
            self.assertEqual(identifier, "123")
            self.assertEqual(platform_type.name, "Naval - frigate")
            self.assertEqual(nationality.name, "UK")
            self.assertEqual(privacy.name, "Public")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_resolver_platform_new_privacy_given(self, resolver_prompt, menu_prompt):
        menu_prompt.side_effect = ["1", "1"]
        resolver_prompt.side_effect = [
            "TEST",
            "123",
            "TST",
            "TEST",
            "10",
        ]
        with self.store.session_scope():
            platform_type = self.store.add_to_platform_types("Naval - frigate", self.change_id).name
            nationality = self.store.add_to_nationalities("UK", self.change_id).name
            (
                platform_name,
                trigraph,
                quadgraph,
                identifier,
                platform_type,
                nationality,
                privacy,
            ) = self.resolver.resolve_platform(
                data_store=self.store,
                platform_name="TEST",
                identifier=None,
                platform_type=platform_type,
                nationality=nationality,
                privacy="PRIVACY-TEST",
                change_id=self.change_id,
            )
            self.assertEqual(platform_name, "TEST")
            self.assertEqual(privacy.name, "PRIVACY-TEST")

    @patch("pepys_import.utils.text_formatting_utils.input")
    @patch("pepys_import.utils.text_formatting_utils.custom_print_formatted_text")
    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_fuzzy_search_platform_print_help_text(
        self, resolver_prompt, menu_prompt, mock_print, mock_input
    ):
        # Use normal print() to capture table reports
        def side_effect(text):
            print(formatted_text_to_str(text))

        mock_print.side_effect = side_effect
        mock_input.return_value = "Enter"
        menu_prompt.side_effect = ["?", "HELP", "TEST", "1"]
        resolver_prompt.side_effect = ["TEST", "123", "TST", "TEST"]
        with self.store.session_scope():
            privacy = self.store.add_to_privacies("Public", 0, self.change_id)
            platform_type = self.store.add_to_platform_types("Naval - frigate", self.change_id)
            nationality = self.store.add_to_nationalities("UK", self.change_id)
            self.store.add_to_platforms(
                "PLATFORM-1",
                trigraph="PL1",
                quadgraph="PLT1",
                identifier="123",
                nationality=nationality.name,
                platform_type=platform_type.name,
                privacy=privacy.name,
                change_id=self.change_id,
            )
            temp_output = StringIO()
            with redirect_stdout(temp_output):
                self.resolver.fuzzy_search_platform(
                    self.store,
                    "TEST",
                    identifier=None,
                    nationality=nationality.name,
                    platform_type=platform_type.name,
                    privacy=privacy.name,
                    change_id=self.change_id,
                )
            output = temp_output.getvalue()
            assert constants.FUZZY_SEARCH_PLATFORM in output

    @patch("pepys_import.utils.text_formatting_utils.input")
    @patch("pepys_import.utils.text_formatting_utils.custom_print_formatted_text")
    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_resolver_platform_print_help_text(
        self, resolver_prompt, menu_prompt, mock_print, mock_input
    ):
        # Use normal print() to capture table reports
        def side_effect(text):
            print(formatted_text_to_str(text))

        mock_print.side_effect = side_effect
        mock_input.return_value = "Enter"
        menu_prompt.side_effect = [
            "?",
            "HELP",
            "2",
            "2",
            "1",
            "UK",
            "1",
            "Naval - frigate",
            "1",
            "Public",
            "1",
        ]
        resolver_prompt.side_effect = [
            "TEST",
            "123",
            "TST",
            "TEST",
            "TEST",
            "123",
            "TST",
            "TEST",
        ]
        with self.store.session_scope():
            privacy = self.store.add_to_privacies("Public", 0, self.change_id).name
            platform_type = self.store.add_to_platform_types("Naval - frigate", self.change_id).name
            nationality = self.store.add_to_nationalities("UK", self.change_id).name
            temp_output = StringIO()
            with redirect_stdout(temp_output):
                self.resolver.resolve_platform(
                    data_store=self.store,
                    platform_name=None,
                    identifier=None,
                    platform_type=platform_type,
                    nationality=nationality,
                    privacy=privacy,
                    change_id=self.change_id,
                )
            output = temp_output.getvalue()
            assert constants.RESOLVE_PLATFORM in output

    @patch("pepys_import.utils.text_formatting_utils.input")
    @patch("pepys_import.utils.text_formatting_utils.custom_print_formatted_text")
    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_add_to_platforms_print_help_text(
        self, resolver_prompt, menu_prompt, mock_print, mock_input
    ):
        # Use normal print() to capture table reports
        def side_effect(text):
            print(formatted_text_to_str(text))

        mock_print.side_effect = side_effect
        mock_input.return_value = "Enter"
        menu_prompt.side_effect = [
            "?",
            "HELP",
            "1",
        ]
        resolver_prompt.side_effect = [
            "TEST",
            "?",
            "123",
            "?",
            "TST",
            "?",
            "TEST",
        ]
        with self.store.session_scope():
            privacy = self.store.add_to_privacies("Public", 0, self.change_id).name
            platform_type = self.store.add_to_platform_types("Naval - frigate", self.change_id).name
            nationality = self.store.add_to_nationalities("UK", self.change_id).name
            temp_output = StringIO()
            with redirect_stdout(temp_output):
                self.resolver.add_to_platforms(
                    data_store=self.store,
                    platform_name=None,
                    identifier=None,
                    platform_type=platform_type,
                    nationality=nationality,
                    privacy=privacy,
                    change_id=self.change_id,
                )
            output = temp_output.getvalue()
            assert constants.ADD_TO_PLATFORMS in output
            assert constants.PLATFORM_IDENTIFIER in output
            assert constants.PLATFORM_TRIGRAPH in output
            assert constants.PLATFORM_QUADGRAPH in output


class DatafileTestCase(unittest.TestCase):
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
        with self.store.session_scope():
            self.store.populate_reference()
            self.change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_resolver_datafile_edit_given_values(self, resolver_prompt, menu_prompt):
        """Test whether correct datafile type and privacy returns after resolver is further edited"""

        # Type "TEST"->Select "No"->Type "TEST"->Select "Search for an existing datafile-type"->
        # Search "DATAFILE-TYPE-2"->Select "Search for an existing classification"->Search
        # "Public Sensitive"->Select "Yes"
        menu_prompt.side_effect = [
            "2",
            "1",
            "DATAFILE-TYPE-2",
            "1",
            "Public Sensitive",
            "1",
        ]
        resolver_prompt.side_effect = ["TEST", "TEST"]
        with self.store.session_scope():
            privacy = self.store.add_to_privacies("Public", 0, self.change_id).name
            self.store.add_to_privacies("Public Sensitive", 0, self.change_id)
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
            self.assertEqual(privacy.name, "Public Sensitive")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_resolver_datafile_add_new_datafile(self, resolver_prompt, menu_prompt):
        """Test whether the correct datafile type and privacy entities are returned after searched
        and not found in Datafile Table."""

        # Type "TEST"->Select "Search for an existing datafile type"->Search "DATAFILE-TYPE-1"->
        # Select "Search for an existing classification"->Search "Public->Select "Yes"
        menu_prompt.side_effect = [
            "1",
            "DATAFILE-TYPE-1",
            "1",
            "Public",
            "1",
        ]
        with self.store.session_scope():
            self.store.add_to_privacies("Public", 0, self.change_id)
            self.store.add_to_datafile_types("DATAFILE-TYPE-1", self.change_id)
            datafile_name, datafile_type, privacy = self.resolver.resolve_datafile(
                data_store=self.store,
                datafile_name="TEST",
                datafile_type=None,
                privacy=None,
                change_id=self.change_id,
            )
            self.assertEqual(datafile_name, "TEST")
            self.assertEqual(datafile_type.name, "DATAFILE-TYPE-1")
            self.assertEqual(privacy.name, "Public")

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
            privacy = self.store.add_to_privacies("Public", 0, self.change_id).name
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

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_resolver_datafile_new_privacy_given(self, resolver_prompt, menu_prompt):
        menu_prompt.side_effect = ["1"]
        resolver_prompt.side_effect = [
            "TEST",
            "10",
        ]
        with self.store.session_scope():
            datafile_type = self.store.add_to_datafile_types("DATAFILE-TYPE-1", self.change_id).name
            (datafile_name, datafile_type, privacy,) = self.resolver.resolve_datafile(
                data_store=self.store,
                datafile_name="TEST",
                datafile_type=datafile_type,
                privacy="PRIVACY-TEST",
                change_id=self.change_id,
            )
            self.assertEqual(datafile_name, "TEST")
            self.assertEqual(privacy.name, "PRIVACY-TEST")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_resolver_datafile_datafile_name_is_none(self, resolver_prompt, menu_prompt):
        menu_prompt.side_effect = ["1"]
        resolver_prompt.side_effect = [
            "TEST",
            "10",
        ]
        with self.store.session_scope():
            datafile_type = self.store.add_to_datafile_types("DATAFILE-TYPE-1", self.change_id).name
            with pytest.raises(ValueError):
                self.resolver.resolve_datafile(
                    data_store=self.store,
                    datafile_name=None,
                    datafile_type=datafile_type,
                    privacy="PRIVACY-TEST",
                    change_id=self.change_id,
                )

    @patch("pepys_import.utils.text_formatting_utils.input")
    @patch("pepys_import.utils.text_formatting_utils.custom_print_formatted_text")
    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_resolver_datafile_print_help_text(
        self, resolver_prompt, menu_prompt, mock_print, mock_input
    ):
        # Use normal print() to capture table reports
        def side_effect(text):
            print(formatted_text_to_str(text))

        mock_print.side_effect = side_effect
        mock_input.return_value = "Enter"
        menu_prompt.side_effect = [
            "?",
            "HELP",
            "1",
        ]
        resolver_prompt.side_effect = ["TEST", "TEST"]
        with self.store.session_scope():
            privacy = self.store.add_to_privacies("Public", 0, self.change_id).name
            datafile_type = self.store.add_to_datafile_types("DATAFILE-TYPE-1", self.change_id).name
            temp_output = StringIO()
            with redirect_stdout(temp_output):
                self.resolver.resolve_datafile(
                    data_store=self.store,
                    datafile_name="TEST",
                    datafile_type=datafile_type,
                    privacy=privacy,
                    change_id=self.change_id,
                )
            output = temp_output.getvalue()
            assert constants.RESOLVE_DATAFILE in output


class SensorTestCase(unittest.TestCase):
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
        with self.store.session_scope():
            self.change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_resolve_sensor(self, resolver_prompt, menu_prompt):
        """Test whether correct sensor type and privacy entities are resolved or not"""

        # Select "Add a new sensor"->Type "TEST"->Select "Add a new sensor-type"->
        # Type "SENSOR-TYPE-1"->Select "Add a new classification"->Type "Public"->Select "Yes"
        menu_prompt.side_effect = ["1", "2", "2", "1"]
        resolver_prompt.side_effect = ["TEST", "SENSOR-TYPE-1", "Public"]
        with self.store.session_scope():
            self.store.add_to_sensor_types("SENSOR-TYPE-1", self.change_id)

            privacy = self.store.add_to_privacies("Public", 0, self.change_id).name
            nationality = self.store.add_to_nationalities("UK", self.change_id).name
            platform_type = self.store.add_to_platform_types("PLATFORM-TYPE-1", self.change_id).name

            platform = self.store.get_platform(
                platform_name="Test Platform",
                identifier="123",
                nationality=nationality,
                platform_type=platform_type,
                privacy=privacy,
                change_id=self.change_id,
            )

            sensor_name, sensor_type, privacy = self.resolver.resolve_sensor(
                self.store,
                "TEST",
                sensor_type=None,
                host_id=platform.platform_id,
                privacy=None,
                change_id=self.change_id,
            )

            self.assertEqual(sensor_name, "TEST")
            self.assertEqual(sensor_type.name, "SENSOR-TYPE-1")
            self.assertEqual(privacy.name, "Public")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_resolver_sensor_make_further_edit(self, resolver_prompt, menu_prompt):
        """Test whether correct sensor type and privacy returns after resolver is further edited"""

        # Select "Add a new sensor"->Type "TEST"->Select "No"->Type "TEST"->
        # Select "Search for an existing sensor-type"->Search "SENSOR-TYPE-2"->
        # Select "Search for an existing classification"->Search "Public Sensitive"->Select "Yes"
        menu_prompt.side_effect = [
            "1",
            "2",
            "1",
            "SENSOR-TYPE-2",
            "1",
            "Public Sensitive",
            "1",
        ]
        resolver_prompt.side_effect = ["TEST", "TEST"]
        with self.store.session_scope():
            sensor_type = self.store.add_to_sensor_types("SENSOR-TYPE-1", self.change_id)
            sensor_type_2 = self.store.add_to_sensor_types("SENSOR-TYPE-2", self.change_id)
            privacy = self.store.add_to_privacies("Public", 0, self.change_id)
            privacy_2 = self.store.add_to_privacies("Public Sensitive", 0, self.change_id)
            nationality = self.store.add_to_nationalities("UK", self.change_id)
            platform_type = self.store.add_to_platform_types("PLATFORM-TYPE-1", self.change_id)

            platform = self.store.get_platform(
                platform_name="Test Platform",
                identifier="123",
                nationality=nationality.name,
                platform_type=platform_type.name,
                privacy=privacy.name,
                change_id=self.change_id,
            )

            (resolved_name, resolved_type, resolved_privacy,) = self.resolver.resolve_sensor(
                self.store,
                "TEST",
                sensor_type.name,
                platform.platform_id,
                privacy.name,
                self.change_id,
            )
            self.assertEqual(resolved_name, "TEST")
            self.assertEqual(resolved_type.sensor_type_id, sensor_type_2.sensor_type_id)
            self.assertEqual(resolved_privacy.privacy_id, privacy_2.privacy_id)

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_resolver_sensor_return_sensor_selection_process(self, resolver_prompt, menu_prompt):
        # Select "Add a new sensor"->Type "TEST"->Select "No, restart sensor selection process"->
        # Select "Add a new sensor" ->Type "TEST"->Select "Search for an existing sensor-type"->
        # Search "SENSOR-TYPE-2"->Select "Search for an existing classification"->
        # Search "Public Sensitive"->Select "Yes"
        menu_prompt.side_effect = [
            "1",
            "3",
            "1",
            "1",
            "SENSOR-TYPE-2",
            "1",
            "Public Sensitive",
            "1",
        ]
        resolver_prompt.side_effect = ["TEST", "TEST"]
        with self.store.session_scope():
            sensor_type = self.store.add_to_sensor_types("SENSOR-TYPE-1", self.change_id)
            sensor_type_2 = self.store.add_to_sensor_types("SENSOR-TYPE-2", self.change_id)
            privacy = self.store.add_to_privacies("Public", 0, self.change_id)
            privacy_2 = self.store.add_to_privacies("Public Sensitive", 0, self.change_id)
            nationality = self.store.add_to_nationalities("UK", self.change_id)
            platform_type = self.store.add_to_platform_types("PLATFORM-TYPE-1", self.change_id)

            platform = self.store.get_platform(
                platform_name="Test Platform",
                identifier="123",
                nationality=nationality.name,
                platform_type=platform_type.name,
                privacy=privacy.name,
                change_id=self.change_id,
            )

            (resolved_name, resolved_type, resolved_privacy,) = self.resolver.resolve_sensor(
                self.store,
                "TEST",
                sensor_type.name,
                platform.platform_id,
                privacy.name,
                self.change_id,
            )
            self.assertEqual(resolved_name, "TEST")
            self.assertEqual(resolved_type.sensor_type_id, sensor_type_2.sensor_type_id)
            self.assertEqual(resolved_privacy.privacy_id, privacy_2.privacy_id)

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_fuzzy_search_add_sensor(self, resolver_prompt, menu_prompt):
        """Test whether a new Sensor entity created or not after searched
        and not founded in the Sensor Table."""

        # Select "Search an existing sensor"->Search "Blah"->Type "SENSOR-TEST"->
        # Select "Search for an existing sensor-type"->Search "SENSOR-TYPE-1"->
        # Select "Search an existing classification"->Search "Public"->Select "Yes"
        menu_prompt.side_effect = [
            "2",
            "Blah",
            "1",
            "SENSOR-TYPE-1",
            "1",
            "Public",
            "1",
        ]
        resolver_prompt.side_effect = ["SENSOR-TEST"]
        with self.store.session_scope():
            # Create platform first, then create a Sensor object
            sensor_type = self.store.add_to_sensor_types("SENSOR-TYPE-1", self.change_id).name
            privacy = self.store.add_to_privacies("Public", 0, self.change_id).name
            nationality = self.store.add_to_nationalities("UK", self.change_id).name
            platform_type = self.store.add_to_platform_types("PLATFORM-TYPE-1", self.change_id).name
            platform = self.store.get_platform(
                platform_name="Test Platform",
                identifier="123",
                nationality=nationality,
                platform_type=platform_type,
                privacy=privacy,
                change_id=self.change_id,
            )
            platform.get_sensor(self.store, "SENSOR-1", sensor_type, privacy, self.change_id)
            platform.get_sensor(self.store, "SENSOR-2", sensor_type, privacy, self.change_id)

            sensor_name, sensor_type, privacy = self.resolver.resolve_sensor(
                self.store,
                "SENSOR-TEST",
                host_id=platform.platform_id,
                sensor_type=None,
                privacy=None,
                change_id=self.change_id,
            )

            self.assertEqual(sensor_name, "SENSOR-TEST")
            self.assertEqual(sensor_type.name, "SENSOR-TYPE-1")
            self.assertEqual(privacy.name, "Public")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_resolve_sensor_select_sensor_directly(self, menu_prompt):
        """Test whether correct sensor is selected directly or not"""

        # Select "3-SENSOR-1"
        menu_prompt.side_effect = ["3"]
        with self.store.session_scope():
            sensor_type = self.store.add_to_sensor_types("SENSOR-TYPE-1", self.change_id).name
            privacy = self.store.add_to_privacies("Public", 0, self.change_id).name
            nationality = self.store.add_to_nationalities("UK", self.change_id).name
            platform_type = self.store.add_to_platform_types("PLATFORM-TYPE-1", self.change_id).name

            platform = self.store.get_platform(
                platform_name="Test Platform",
                identifier="123",
                nationality=nationality,
                platform_type=platform_type,
                privacy=privacy,
                change_id=self.change_id,
            )
            platform.get_sensor(
                self.store,
                sensor_name="TEST",
                sensor_type=sensor_type,
                privacy=privacy,
                change_id=self.change_id,
            )
            platform_2 = self.store.get_platform(
                platform_name="Test Platform 2",
                identifier="234",
                nationality=nationality,
                platform_type=platform_type,
                privacy=privacy,
                change_id=self.change_id,
            )
            platform_2.get_sensor(
                self.store,
                sensor_name="TEST-SENSOR",
                sensor_type=sensor_type,
                privacy=privacy,
                change_id=self.change_id,
            )

            sensor = self.resolver.resolve_sensor(
                self.store,
                "TEST-2",
                sensor_type=None,
                host_id=platform.platform_id,
                privacy=None,
                change_id=self.change_id,
            )

            self.assertEqual(sensor.name, "TEST")

    def test_resolve_sensor_wrong_platform(self):
        with pytest.raises(SystemExit):
            uuid = uuid4()
            self.resolver.resolve_sensor(
                self.store,
                "TEST",
                sensor_type=None,
                host_id=uuid,
                privacy=None,
                change_id=self.change_id,
            )

    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_resolve_missing_info(self, resolver_prompt):
        resolver_prompt.side_effect = ["TEST_VALUE"]
        info = self.resolver.resolve_missing_info("What do you need?", "HELLO")
        self.assertEqual(info, "TEST_VALUE")

    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_resolve_missing_info_default_fallback(self, resolver_prompt):
        resolver_prompt.side_effect = [None]
        info_none = self.resolver.resolve_missing_info("A question", "DEFAULT")
        self.assertEqual(info_none, "DEFAULT")

        resolver_prompt.side_effect = [""]
        info_empty = self.resolver.resolve_missing_info("A question", "DEFAULT")
        self.assertEqual(info_empty, "DEFAULT")

        resolver_prompt.side_effect = [20]
        info_value = self.resolver.resolve_missing_info("A question", 0)
        self.assertEqual(info_value, 20)

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_fuzzy_search_sensor_empty_name_and_choice_in_sensor(self, menu_prompt):
        menu_prompt.side_effect = [
            "SENSOR-1",
        ]
        with self.store.session_scope():
            # Create platform first, then create a Sensor object
            sensor_type = self.store.add_to_sensor_types("SENSOR-TYPE-1", self.change_id).name
            privacy = self.store.add_to_privacies("Public", 0, self.change_id).name
            nationality = self.store.add_to_nationalities("UK", self.change_id).name
            platform_type = self.store.add_to_platform_types("PLATFORM-TYPE-1", self.change_id).name
            platform = self.store.get_platform(
                platform_name="Test Platform",
                identifier="123",
                nationality=nationality,
                platform_type=platform_type,
                privacy=privacy,
                change_id=self.change_id,
            )
            platform.get_sensor(self.store, "SENSOR-1", sensor_type, privacy, self.change_id)
            platform.get_sensor(self.store, "SENSOR-2", sensor_type, privacy, self.change_id)

            sensor = self.resolver.fuzzy_search_sensor(
                self.store,
                sensor_name=None,
                host_id=platform.platform_id,
                sensor_type=None,
                privacy=None,
                change_id=self.change_id,
            )

            self.assertEqual(sensor.name, "SENSOR-1")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_resolver_sensor_new_privacy_given(self, resolver_prompt, menu_prompt):
        menu_prompt.side_effect = [
            "1",
            "1",
        ]
        resolver_prompt.side_effect = ["TEST", "10"]
        with self.store.session_scope():
            sensor_type = self.store.add_to_sensor_types("SENSOR-TYPE-1", self.change_id)
            privacy = self.store.add_to_privacies("Public", 0, self.change_id)
            nationality = self.store.add_to_nationalities("UK", self.change_id)
            platform_type = self.store.add_to_platform_types("PLATFORM-TYPE-1", self.change_id)

            platform = self.store.get_platform(
                platform_name="Test Platform",
                identifier="123",
                nationality=nationality.name,
                platform_type=platform_type.name,
                privacy=privacy.name,
                change_id=self.change_id,
            )

            (resolved_name, resolved_type, resolved_privacy,) = self.resolver.resolve_sensor(
                self.store,
                "TEST",
                sensor_type.name,
                platform.platform_id,
                "PRIVACY-TEST",
                self.change_id,
            )
            self.assertEqual(resolved_name, "TEST")
            self.assertEqual(resolved_privacy.name, "PRIVACY-TEST")

    @patch("pepys_import.utils.text_formatting_utils.input")
    @patch("pepys_import.utils.text_formatting_utils.custom_print_formatted_text")
    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_fuzzy_search_sensor_print_help_text(
        self, resolver_prompt, menu_prompt, mock_print, mock_input
    ):
        with self.store.session_scope():
            self.store.populate_reference()

        # Use normal print() to capture table reports
        def side_effect(text):
            print(formatted_text_to_str(text))

        mock_print.side_effect = side_effect
        mock_input.return_value = "Enter"
        menu_prompt.side_effect = [
            "?",
            "HELP",
            "SENSOR-1",
        ]
        resolver_prompt.side_effect = ["SENSOR-1"]
        with self.store.session_scope():
            sensor_type = self.store.add_to_sensor_types("SENSOR-TYPE-1", self.change_id).name
            privacy = self.store.add_to_privacies("Public", 0, self.change_id).name
            nationality = self.store.add_to_nationalities("UK", self.change_id).name
            platform_type = self.store.add_to_platform_types("PLATFORM-TYPE-1", self.change_id).name
            platform = self.store.get_platform(
                platform_name="Test Platform",
                identifier="123",
                nationality=nationality,
                platform_type=platform_type,
                privacy=privacy,
                change_id=self.change_id,
            )
            platform.get_sensor(self.store, "SENSOR-1", sensor_type, privacy, self.change_id)

            temp_output = StringIO()
            with redirect_stdout(temp_output):
                self.resolver.fuzzy_search_sensor(
                    self.store,
                    "SENSOR-TEST",
                    host_id=platform.platform_id,
                    sensor_type=sensor_type,
                    privacy=privacy,
                    change_id=self.change_id,
                )
            output = temp_output.getvalue()
            assert constants.FUZZY_SEARCH_SENSOR in output

    @patch("pepys_import.utils.text_formatting_utils.input")
    @patch("pepys_import.utils.text_formatting_utils.custom_print_formatted_text")
    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_resolver_sensor_print_help_text(
        self, resolver_prompt, menu_prompt, mock_print, mock_input
    ):
        with self.store.session_scope():
            self.store.populate_reference()

        # Use normal print() to capture table reports
        def side_effect(text):
            print(formatted_text_to_str(text))

        mock_print.side_effect = side_effect
        mock_input.return_value = "Enter"
        menu_prompt.side_effect = [
            "?",
            "HELP",
            "1",
            "SENSOR-1",
        ]
        resolver_prompt.side_effect = ["SENSOR-1"]
        with self.store.session_scope():
            sensor_type = self.store.add_to_sensor_types("SENSOR-TYPE-1", self.change_id).name
            privacy = self.store.add_to_privacies("Public", 0, self.change_id).name
            nationality = self.store.add_to_nationalities("UK", self.change_id).name
            platform_type = self.store.add_to_platform_types("PLATFORM-TYPE-1", self.change_id).name
            platform = self.store.get_platform(
                platform_name="Test Platform",
                identifier="123",
                nationality=nationality,
                platform_type=platform_type,
                privacy=privacy,
                change_id=self.change_id,
            )
            platform.get_sensor(self.store, "SENSOR-1", sensor_type, privacy, self.change_id)

            temp_output = StringIO()
            with redirect_stdout(temp_output):
                self.resolver.resolve_sensor(
                    self.store,
                    "SENSOR-TEST",
                    host_id=platform.platform_id,
                    sensor_type=sensor_type,
                    privacy=privacy,
                    change_id=self.change_id,
                )
            output = temp_output.getvalue()
            assert constants.RESOLVE_SENSOR in output

    @patch("pepys_import.utils.text_formatting_utils.input")
    @patch("pepys_import.utils.text_formatting_utils.custom_print_formatted_text")
    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_add_to_sensors_print_help_text(
        self, resolver_prompt, menu_prompt, mock_print, mock_input
    ):
        with self.store.session_scope():
            self.store.populate_reference()

        # Use normal print() to capture table reports
        def side_effect(text):
            print(formatted_text_to_str(text))

        mock_print.side_effect = side_effect
        mock_input.return_value = "Enter"
        menu_prompt.side_effect = ["?", "HELP", "1"]
        resolver_prompt.side_effect = ["SENSOR-TEST"]
        with self.store.session_scope():
            # Create platform first, then create a Sensor object
            sensor_type = self.store.add_to_sensor_types("SENSOR-TYPE-1", self.change_id).name
            privacy = self.store.add_to_privacies("Public", 0, self.change_id).name
            nationality = self.store.add_to_nationalities("UK", self.change_id).name
            platform_type = self.store.add_to_platform_types("PLATFORM-TYPE-1", self.change_id).name
            platform = self.store.get_platform(
                platform_name="Test Platform",
                identifier="123",
                nationality=nationality,
                platform_type=platform_type,
                privacy=privacy,
                change_id=self.change_id,
            )
            platform.get_sensor(self.store, "SENSOR-1", sensor_type, privacy, self.change_id)
            platform.get_sensor(self.store, "SENSOR-2", sensor_type, privacy, self.change_id)

            temp_output = StringIO()
            with redirect_stdout(temp_output):
                self.resolver.add_to_sensors(
                    self.store,
                    "SENSOR-TEST",
                    host_id=platform.platform_id,
                    sensor_type=sensor_type,
                    privacy=privacy,
                    change_id=self.change_id,
                )
            output = temp_output.getvalue()
            assert constants.ADD_TO_SENSORS in output


class CancellingAndReturnPreviousMenuTestCase(unittest.TestCase):
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
        with self.store.session_scope():
            self.change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_top_level_quitting(self, menu_prompt):
        """Test whether "." quits from the resolve platform/sensor"""
        menu_prompt.side_effect = [".", ".", "."]
        with self.store.session_scope():
            privacy = self.store.add_to_privacies("Public", 0, self.change_id).name
            nationality = self.store.add_to_nationalities("UK", self.change_id).name
            platform_type = self.store.add_to_platform_types("PLATFORM-TYPE-1", self.change_id).name
            platform = self.store.get_platform(
                platform_name="Test Platform",
                identifier="123",
                nationality=nationality,
                platform_type=platform_type,
                privacy=privacy,
                change_id=self.change_id,
            )
            with self.assertRaises(SystemExit):
                self.resolver.resolve_platform(self.store, "", "", "", "", "", self.change_id)
            with self.assertRaises(SystemExit):
                self.resolver.resolve_sensor(
                    self.store, "", "", platform.platform_id, "", self.change_id
                )

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_cancelling_fuzzy_search_platform(self, menu_prompt):
        """Test whether "." returns to resolve platform"""

        # Search "PLATFORM-1"->Select "."->Select "."->Select "."
        menu_prompt.side_effect = [".", ".", "."]
        with self.store.session_scope():
            privacy = self.store.add_to_privacies("Public", 0, self.change_id)
            platform_type = self.store.add_to_platform_types("Naval - frigate", self.change_id)
            nationality = self.store.add_to_nationalities("UK", self.change_id)
            self.store.add_to_platforms(
                "PLATFORM-1",
                "123",
                nationality.name,
                platform_type.name,
                privacy.name,
                change_id=self.change_id,
            )
            with self.assertRaises(SystemExit):
                self.resolver.fuzzy_search_platform(
                    self.store, "TEST", "", "", "", "", self.change_id
                )

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_cancelling_fuzzy_search_platform_when_given_platform_name(self, menu_prompt):
        """Test whether "." returns to resolve platform if we've given a platform name, and
        therefore are asked whether we want to create a synonym"""

        # Search "PLATFORM-1"->Select "."->Select "."->Select "."
        menu_prompt.side_effect = ["PLATFORM-1 / 123 / UK", ".", ".", "."]
        with self.store.session_scope():
            privacy = self.store.add_to_privacies("Public", 0, self.change_id)
            platform_type = self.store.add_to_platform_types("Naval - frigate", self.change_id)
            nationality = self.store.add_to_nationalities("UK", self.change_id)
            self.store.add_to_platforms(
                "PLATFORM-1",
                "123",
                nationality.name,
                platform_type.name,
                privacy.name,
                change_id=self.change_id,
            )
            with self.assertRaises(SystemExit):
                self.resolver.fuzzy_search_platform(
                    self.store, "TEST", "", "", "", "", self.change_id
                )

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    def test_cancelling_fuzzy_search_sensor(self, menu_prompt):
        """Test whether "." returns to resolve sensor"""

        # Type Select "."->Select "."->Select "."->Select "."
        menu_prompt.side_effect = [".", ".", ".", "."]
        with self.store.session_scope():
            sensor_type = self.store.add_to_sensor_types("SENSOR-TYPE-1", self.change_id).name
            privacy = self.store.add_to_privacies("Public", 0, self.change_id).name
            nationality = self.store.add_to_nationalities("UK", self.change_id).name
            platform_type = self.store.add_to_platform_types("PLATFORM-TYPE-1", self.change_id).name
            platform = self.store.get_platform(
                platform_name="Test Platform",
                identifier="123",
                nationality=nationality,
                platform_type=platform_type,
                privacy=privacy,
                change_id=self.change_id,
            )
            platform.get_sensor(self.store, "SENSOR-1", sensor_type, privacy, self.change_id)

            with self.assertRaises(SystemExit):
                self.resolver.fuzzy_search_sensor(
                    self.store, "TEST", "", platform.platform_id, "", self.change_id
                )

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_cancelling_during_add_to_platforms(self, resolver_prompt, menu_prompt):
        menu_prompt.side_effect = [
            ".",
            ".",
        ]
        resolver_prompt.side_effect = [
            "TEST",
            "123",
            "TST",
            "TEST",
        ]
        with self.store.session_scope():
            # Type name/trigraph/quadgraph/identifier->Select "Cancel nationality search"->
            # Select "Cancel import"
            with self.assertRaises(SystemExit):
                self.resolver.add_to_platforms(
                    self.store, "PLATFORM-1", "", "", "", "", self.change_id
                )

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
            "Public",
        ]
        with self.store.session_scope():
            privacy = self.store.add_to_privacies("Public", 0, self.change_id).name
            nationality = self.store.add_to_nationalities("UK", self.change_id).name
            platform_type = self.store.add_to_platform_types("PLATFORM-TYPE-1", self.change_id).name
            self.store.add_to_sensor_types("SENSOR-TYPE-1", self.change_id).name
            platform = self.store.get_platform(
                platform_name="Test Platform",
                identifier="123",
                nationality=nationality,
                platform_type=platform_type,
                privacy=privacy,
                change_id=self.change_id,
            )
            # Type "TEST"->Select "Cancel sensor type search"->Select "Cancel import"
            with self.assertRaises(SystemExit):
                self.resolver.add_to_sensors(
                    self.store, "SENSOR-1", "", platform.platform_id, "", self.change_id
                )
            # Type "TEST"->Select "Add a new sensor type"->Type "SENSOR-TYPE-1->
            # Select "Cancel classification search" ->Select "Cancel import"
            with self.assertRaises(SystemExit):
                self.resolver.add_to_sensors(
                    self.store, "SENSOR-1", "", platform.platform_id, "", self.change_id
                )
            # Type "TEST"->Select "Add a new sensor type"->Type "SENSOR-TYPE-1->
            # Select "Add a new classification"->Type "Public"->Select "Cancel import"->
            # Select "Cancel import"
            with self.assertRaises(SystemExit):
                self.resolver.add_to_sensors(
                    self.store, "SENSOR-1", "", platform.platform_id, "", self.change_id
                )


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
            self.change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id

    def tearDown(self) -> None:
        if os.path.exists(self.file_path):
            os.remove(self.file_path)

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_get_platform_adds_resolved_platform_successfully(self, resolver_prompt, menu_prompt):
        menu_prompt.side_effect = [
            "1",
            "1",
            "United Kingdom",
            "1",
            "Fishing Vessel",
            "1",
            "Public",
            "1",
        ]
        resolver_prompt.side_effect = ["Test Platform", "123", "Tst", "Test"]
        with self.store.session_scope():
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            # there must be 4 entities at the beginning (the default ones)
            self.assertEqual(len(platforms), 4)

            self.store.get_platform("Test Platform", change_id=self.change_id)

            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            self.assertEqual(len(platforms), 5)
            self.assertEqual(platforms[-1].name, "Test Platform")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_get_datafile_adds_resolved_datafile_successfully(self, resolver_prompt, menu_prompt):
        menu_prompt.side_effect = [
            "1",
            "Replay",
            "1",
            "Public",
            "1",
        ]
        with self.store.session_scope():
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            # there must be zero entities at the beginning
            self.assertEqual(len(datafiles), 0)

            self.store.get_datafile("test", None, 0, "HASHED", change_id=self.change_id)

            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 1)
            self.assertEqual(datafiles[0].reference, "test")

    @patch("pepys_import.resolvers.command_line_resolver.create_menu")
    @patch("pepys_import.resolvers.command_line_resolver.prompt")
    def test_get_sensor_adds_resolved_sensor_successfully(self, resolver_prompt, menu_prompt):
        menu_prompt.side_effect = [
            "1",
            "1",
            "Location-Satellite",
            "1",
            "Public",
            "1",
        ]
        resolver_prompt.side_effect = ["SENSOR-TEST"]
        with self.store.session_scope():
            sensors = self.store.session.query(self.store.db_classes.Sensor).all()
            # there must be 5 entities at the beginning (the default ones)
            self.assertEqual(len(sensors), 6)

            platform = self.store.get_platform(
                platform_name="ADRI",
                identifier="A643",
                nationality="United Kingdom",
                change_id=self.change_id,
            )
            platform.get_sensor(self.store, "SENSOR-TEST", change_id=self.change_id)

            # there must be 3 entities now
            sensors = self.store.session.query(self.store.db_classes.Sensor).all()
            self.assertEqual(len(sensors), 7)
            self.assertEqual(sensors[-1].name, "SENSOR-TEST")


class MinMaxValidatorTests(unittest.TestCase):
    def test_min_max_validator_none(self):
        validator = MinMaxValidator(None, None)
        with pytest.raises(ValidationError):
            validator.validate(Document("ABC"))

        validator.validate(Document("20"))

    def test_min_max_validator_min_only(self):
        validator = MinMaxValidator(15, None)
        with pytest.raises(ValidationError):
            validator.validate(Document("14"))
        with pytest.raises(ValidationError):
            validator.validate(Document("0"))
        validator.validate(Document("15"))
        validator.validate(Document("16"))
        validator.validate(Document("122001"))

    def test_min_max_validator_max_only(self):
        validator = MinMaxValidator(None, 15)
        with pytest.raises(ValidationError):
            validator.validate(Document("16"))
        with pytest.raises(ValidationError):
            validator.validate(Document("122001"))
        validator.validate(Document("15"))
        validator.validate(Document("14"))
        validator.validate(Document("0"))

    def test_min_max_validator_same_value(self):
        validator = MinMaxValidator(15, 15)
        with pytest.raises(ValidationError):
            validator.validate(Document("16"))
        with pytest.raises(ValidationError):
            validator.validate(Document("14"))
        validator.validate(Document("15"))

    def test_min_max_validator_min_and_max(self):
        validator = MinMaxValidator(10, 15)
        with pytest.raises(ValidationError):
            validator.validate(Document("16"))
        with pytest.raises(ValidationError):
            validator.validate(Document("9"))
        validator.validate(Document("15"))
        validator.validate(Document("10"))
        validator.validate(Document("13"))

    def test_min_max_validator_allow_empty(self):
        validator = MinMaxValidator(10, 15, True)
        with pytest.raises(ValidationError):
            validator.validate(Document("16"))
        with pytest.raises(ValidationError):
            validator.validate(Document("9"))
        with pytest.raises(ValidationError):
            validator.validate(Document("TEXT"))
        validator.validate(Document(""))

    def test_min_max_validator__do_not_allow_empty(self):
        validator = MinMaxValidator(10, 15, False)
        with pytest.raises(ValidationError):
            validator.validate(Document("16"))
        with pytest.raises(ValidationError):
            validator.validate(Document("9"))
        with pytest.raises(ValidationError):
            validator.validate(Document("TEXT"))
        with pytest.raises(ValidationError):
            validator.validate(Document(""))


@pytest.mark.parametrize(
    "number,expected_result",
    [
        pytest.param("123", True, id="valid number1"),
        pytest.param("9", True, id="valid number2"),
        pytest.param("ABC", False, id="invalid number1"),
        pytest.param("12#", False, id="invalid number2"),
    ],
)
def test_is_number(number, expected_result):
    assert is_number(number) == expected_result


@pytest.mark.parametrize(
    "s,expected_result",
    [
        pytest.param(".", True, id="valid_dot"),
        pytest.param("1", True, id="valid_1"),
        pytest.param("2", True, id="valid_2"),
        pytest.param("3", False, id="invalid_3"),
        pytest.param("9", False, id="invalid_9"),
        pytest.param("#", False, id="invalid_#"),
    ],
)
def test_is_valid(s, expected_result):
    assert is_valid(s) == expected_result


if __name__ == "__main__":
    unittest.main()
