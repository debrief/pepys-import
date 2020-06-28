import cmd
import os
import sys
import webbrowser

from alembic import command
from alembic.config import Config

from paths import ROOT_DIRECTORY
from pepys_admin.export_cli import ExportShell
from pepys_admin.initialise_cli import InitialiseShell
from pepys_admin.snapshot_cli import SnapshotShell
from pepys_admin.view_data_cli import ViewDataShell
from pepys_import.utils.data_store_utils import is_schema_created
from pepys_import.utils.error_handling import handle_status_errors

DIR_PATH = os.path.dirname(os.path.abspath(__file__))


class AdminShell(cmd.Cmd):
    """Main Shell of Pepys Admin."""

    intro = """--- Menu ---
(1) Initialise/Clear
(2) Status
(3) Export
(4) Snapshot
(5) Migrate
(6) View Data
(7) View Docs
(0) Exit
"""
    prompt = "(pepys-admin) "

    def __init__(self, data_store, csv_path=DIR_PATH):
        super(AdminShell, self).__init__()
        self.data_store = data_store
        self.csv_path = csv_path
        self.aliases = {
            "0": self.do_exit,
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
        print("-" * 61)
        export_shell = ExportShell(self.data_store)
        export_shell.cmdloop()

    def do_view_docs(self):
        print("Loading docs in default web browser")
        path = os.path.abspath(os.path.join(ROOT_DIRECTORY, "docs", "_build", "html", "index.html"))
        webbrowser.open("file://" + path)

    def do_snapshot(self):
        """Runs the :code:`SnapshotShell` to take a snapshot of reference or/and metadata tables."""
        print("-" * 61)
        snapshot_shell = SnapshotShell(self.data_store)
        snapshot_shell.cmdloop()

    def do_initialise(self):
        """Runs the :code:`InitialiseShell` which offers to clear contents, import sample data,
         create/delete schema."""
        print("-" * 61)
        initialise = InitialiseShell(self.data_store, self, self.csv_path)
        initialise.cmdloop()

    def do_status(self):
        """Prints table summaries and database version."""
        if is_schema_created(self.data_store.engine, self.data_store.db_type) is False:
            return

        with self.data_store.session_scope(), handle_status_errors():
            measurement_summary = self.data_store.get_status(report_measurement=True)
            report = measurement_summary.report()
            print(f"## Measurements\n{report}\n")

            metadata_summary = self.data_store.get_status(report_metadata=True)
            report = metadata_summary.report()
            print(f"## Metadata\n{report}\n")

            reference_summary = self.data_store.get_status(report_reference=True)
            report = reference_summary.report()
            print(f"## Reference\n{report}\n")

        print(f"## Database Version")
        command.current(self.cfg, verbose=True)

    def do_migrate(self):
        """Runs Alembic's :code:`upgrade` command to migrate the database to the latest version."""
        confirmation = input(
            "Your database schema is going to be updated. Are you sure to continue? (y/N) "
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
        print("-" * 61)
        shell = ViewDataShell(self.data_store)
        shell.cmdloop()

    @staticmethod
    def do_exit():
        """Exit the application"""
        print("Thank you for using Pepys Admin")
        sys.exit()

    def default(self, line):
        command_, arg, line = self.parseline(line)
        if command_ in self.aliases:
            self.aliases[command_]()
        else:
            print(f"*** Unknown syntax: {line}")

    def postcmd(self, stop, line):
        if line != "0":
            print("-" * 61)
            print(self.intro)
        return cmd.Cmd.postcmd(self, stop, line)
