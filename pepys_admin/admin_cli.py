import os
import sys
import webbrowser

from alembic import command
from alembic.config import Config
from prompt_toolkit import prompt

import config
from paths import ROOT_DIRECTORY
from pepys_admin.base_cli import BaseShell
from pepys_admin.export_cli import ExportShell
from pepys_admin.initialise_cli import InitialiseShell
from pepys_admin.snapshot_cli import SnapshotShell
from pepys_admin.view_data_cli import ViewDataShell
from pepys_import.core.store import constants
from pepys_import.core.store.db_status import TableTypes
from pepys_import.utils.data_store_utils import is_schema_created
from pepys_import.utils.error_handling import handle_status_errors
from pepys_import.utils.text_formatting_utils import (
    custom_print_formatted_text,
    format_command,
    format_table,
)

DIR_PATH = os.path.dirname(os.path.abspath(__file__))


class AdminShell(BaseShell):
    """Main Shell of Pepys Admin."""

    choices = """(1) Initialise/Clear
(2) Status
(3) Export
(4) Snapshot
(5) Migrate
(6) View Data
(7) View Docs
(.) Exit
"""
    prompt = "(pepys-admin) "

    def __init__(self, data_store, csv_path=DIR_PATH):
        super(AdminShell, self).__init__()
        self.data_store = data_store
        self.csv_path = csv_path
        self.aliases = {
            ".": self.do_exit,
            "1": self.do_initialise,
            "2": self.do_status,
            "3": self.do_export,
            "4": self.do_snapshot,
            "5": self.do_migrate,
            "6": self.do_view_data,
            "7": self.do_view_docs,
        }

        self.cfg = Config(os.path.join(ROOT_DIRECTORY, "alembic.ini"))
        script_location = os.path.join(ROOT_DIRECTORY, "migrations")
        self.cfg.set_main_option("script_location", script_location)
        self.cfg.attributes["db_type"] = data_store.db_type
        self.cfg.attributes["connection"] = data_store.engine

    def do_export(self):
        """Runs the :code:`ExportShell` which offers to export datafiles."""
        print("-" * 60)
        export_shell = ExportShell(self.data_store)
        export_shell.cmdloop()

    def do_view_docs(self):  # pragma: no cover
        print("Loading docs in default web browser")
        path = os.path.abspath(os.path.join(ROOT_DIRECTORY, "docs", "_build", "html", "index.html"))
        webbrowser.open("file://" + path)

    def do_snapshot(self):
        """Runs the :code:`SnapshotShell` to take a snapshot of reference or/and metadata tables."""
        print("-" * 60)
        snapshot_shell = SnapshotShell(self.data_store)
        snapshot_shell.cmdloop()

    def do_initialise(self):
        """Runs the :code:`InitialiseShell` which offers to clear contents, import sample data,
        create/delete schema."""
        print("-" * 60)
        initialise = InitialiseShell(self.data_store, self, self.csv_path)
        initialise.cmdloop()

    def do_status(self):
        """Prints table summaries and database version."""

        if is_schema_created(self.data_store.engine, self.data_store.db_type):
            with self.data_store.session_scope(), handle_status_errors():
                measurement_summary = self.data_store.get_status(TableTypes.MEASUREMENT)
                report = measurement_summary.report()
                formatted_text = format_table("## Measurements", table_string=report)
                custom_print_formatted_text(formatted_text)

                metadata_summary = self.data_store.get_status(TableTypes.METADATA)
                report = metadata_summary.report()
                formatted_text = format_table("## Metadata", table_string=report)
                custom_print_formatted_text(formatted_text)

                reference_summary = self.data_store.get_status(
                    TableTypes.REFERENCE, exclude=[constants.HELP_TEXT]
                )
                report = reference_summary.report()
                formatted_text = format_table("## Reference", table_string=report)
                custom_print_formatted_text(formatted_text)

            print("## Database Version")
            command.current(self.cfg, verbose=True)

        print("## Config file")
        print(f"Location: {config.CONFIG_FILE_PATH}")
        try:
            print("Contents:")
            with open(config.CONFIG_FILE_PATH) as f:
                print(f.read())
        except Exception as e:
            print(f"Error reading config file: {str(e)}")

    def do_migrate(self):
        """Runs Alembic's :code:`upgrade` command to migrate the database to the latest version."""
        confirmation = prompt(
            format_command(
                "Your database schema is going to be updated. Are you sure to continue? (y/N) "
            )
        )
        if confirmation.lower() == "y":
            print("Alembic migration command running, see output below.")
            try:
                command.upgrade(self.cfg, "head")
            except Exception as e:
                print(
                    f"Exception details: {e}\n\nERROR: Alembic error when migrating the database!"
                )

    def do_view_data(self):
        """Runs the :code:`ViewDataShell` which offers to view a table and run SQL."""
        if is_schema_created(self.data_store.engine, self.data_store.db_type) is False:
            return
        print("-" * 60)
        shell = ViewDataShell(self.data_store)
        shell.cmdloop()

    @staticmethod
    def do_exit():
        """Exit the application"""
        print("Thank you for using Pepys Admin")
        sys.exit()
