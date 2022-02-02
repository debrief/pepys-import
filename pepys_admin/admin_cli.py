import os
import subprocess
import sys
import webbrowser
from datetime import datetime
from getpass import getuser

from alembic import command
from alembic.config import Config
from prompt_toolkit import prompt
from waitress import serve

import config
from paths import MIGRATIONS_DIRECTORY, ROOT_DIRECTORY
from pepys_admin.base_cli import BaseShell
from pepys_admin.export_cli import ExportShell
from pepys_admin.initialise_cli import InitialiseShell
from pepys_admin.maintenance.gui import MaintenanceGUI
from pepys_admin.maintenance.tasks_gui import TasksGUI
from pepys_admin.snapshot_cli import SnapshotShell
from pepys_admin.utils import redirect_stdout_to_file_and_screen
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
from pepys_timeline.app import create_app

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
(8) Maintenance
(9) Maintain tasks
(10) View dashboard
(11) Run Jupyter Notebook server
(.) Exit
"""
    prompt = "(pepys-admin) "

    def __init__(self, data_store, csv_path=DIR_PATH):
        super(AdminShell, self).__init__()
        self.data_store = data_store
        self.csv_path = csv_path
        self.viewer = False
        self.aliases = {
            ".": self.do_exit,
            "1": self.do_initialise,
            "2": self.do_status,
            "3": self.do_export,
            "4": self.do_snapshot,
            "5": self.do_migrate,
            "6": self.do_view_data,
            "7": self.do_view_docs,
            "8": self.do_maintenance_gui,
            "9": self.do_tasks_gui,
            "10": self.do_view_dashboard,
            "11": self.do_run_jupyter,
        }

        self.cfg = Config(os.path.join(ROOT_DIRECTORY, "alembic.ini"))
        script_location = os.path.join(ROOT_DIRECTORY, "migrations")
        self.cfg.set_main_option("script_location", script_location)
        self.cfg.attributes["database_type"] = data_store.db_type
        self.cfg.attributes["connection"] = data_store.engine

    def do_run_jupyter(self):
        subprocess.run([sys.executable, "-m", "jupyter", "notebook"], cwd=os.path.expanduser("~"))

    def do_view_dashboard(self):
        if self.data_store.db_type == "sqlite":
            print("The Pepys dashboard cannot be used with a SQLite database")
            return

        app = create_app()

        print(
            "The Pepys timeline dashboard process is now running on: http://localhost:5000.\nA browser window should have "
            "opened displaying the timeline.\n"
            "Keep this window open for the server to continue running. The server process can be terminated by "
            "closing this window."
        )

        # Open the URL in the web browser just before we call run()
        # as the run call is blocking, so nothing else can run after it
        webbrowser.open("http://localhost:5000")
        serve(app, host="0.0.0.0", port=5000)

        # This is the code to run it through the Flask server, which works
        # fine, but prints a big warning message about how it shouldn't be used
        # in production, which may scare the clients
        # app.run(host='0.0.0.0', port=5000)

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

    def do_maintenance_gui(self):
        try:
            gui = MaintenanceGUI(self.data_store)
        except Exception as e:
            print(str(e))
            print("Database error: See full error above.")
            return
        gui.app.run()

    def do_tasks_gui(self):
        try:
            gui = TasksGUI(self.data_store)
        except Exception as e:
            print(str(e))
            print("Database error: See full error above.")
            return
        gui.app.run()

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
        try:
            command.current(self.cfg, verbose=True)
        except Exception as e:
            print("Error getting latest database version")
            print(str(e))

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

            migration_log_filename = os.path.join(MIGRATIONS_DIRECTORY, "migration_output.log")

            with open(migration_log_filename, "a") as f:
                current_timestamp = str(datetime.now())
                username = getuser()
                f.write(f"=== Migrations run by {username} on {current_timestamp}:\n\n")

            # Use a function to redirect stdout so it displays on *both* the screen (in real-time)
            # and is output to a file. This means the user still gets the real-time progress of the
            # migrations, while we write to a log file. If we just redirected to a variable and then
            # printed it, the user would receive no output on the screen until the process was finished
            # and so could not see the progress of the migrations
            with redirect_stdout_to_file_and_screen(migration_log_filename):
                try:
                    command.current(self.cfg, verbose=True)
                    command.upgrade(self.cfg, "head")
                except Exception as e:
                    print(
                        f"Exception details: {e}\n\nERROR: Alembic error when migrating the database!"
                    )
                else:
                    print("Migrations ran successfully")

            with open(migration_log_filename, "a") as f:
                f.write("\n=== End of migration run output")
                f.write("\n\n\n")

    def do_view_data(self):
        """Runs the :code:`ViewDataShell` which offers to view a table and run SQL."""
        if is_schema_created(self.data_store.engine, self.data_store.db_type) is False:
            return
        print("-" * 60)
        shell = ViewDataShell(self.data_store, viewer=self.viewer)
        shell.cmdloop()

    @staticmethod
    def do_exit():
        """Exit the application"""
        print("Thank you for using Pepys Admin")
        sys.exit()
