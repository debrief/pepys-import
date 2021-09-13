import csv
import os

from iterfzf import iterfzf
from prompt_toolkit import HTML, prompt
from prompt_toolkit.lexers import PygmentsLexer
from pygments.lexers.sql import SqlLexer
from sqlalchemy import inspect
from sqlalchemy.exc import InvalidRequestError, OperationalError, ProgrammingError
from sqlalchemy.orm import RelationshipProperty, class_mapper, load_only
from sqlalchemy.sql.expression import text
from tabulate import tabulate

from pepys_admin.base_cli import BaseShell
from pepys_admin.maintenance.column_data import get_assoc_proxy_names_and_objects
from pepys_admin.utils import get_default_export_folder
from pepys_import.core.store import constants
from pepys_import.utils.table_name_utils import table_name_to_class_name
from pepys_import.utils.text_formatting_utils import (
    custom_print_formatted_text,
    format_error_message,
)

MAX_ROWS_DISPLAYED = 500


def bottom_toolbar():
    return HTML("Press <b>ESC</b> then <b>Enter</b> to run query")


class ViewDataShell(BaseShell):
    """Offers to view table and run SQL."""

    choices = """(1) View Table
(2) Output Table to CSV
(3) Run SQL
(4) Output SQL Results to CSV
(.) Back
"""

    def __init__(self, data_store, viewer=False):
        super(ViewDataShell, self).__init__()
        self.data_store = data_store
        self.aliases = {
            ".": self.do_cancel,
            "1": self.do_view_table,
            "2": self.do_output_table_to_csv,
            "3": self.do_run_sql,
            "4": self.do_output_sql_to_csv,
        }

        self.viewer = viewer

        if viewer:
            self.prompt = "(pepys-viewer) (view) "
        else:
            self.prompt = "(pepys-admin) (view) "

    def do_cancel(self):
        """Returns to the previous menu"""
        print("Returning to the previous menu...")

    def _get_table_names(self):
        """Gets the table names using SQL Alchemy's inspect db functionality."""
        # Inspect the database and extract the table names
        inspector = inspect(self.data_store.engine)
        if self.data_store.db_type == "postgres":
            table_names = inspector.get_table_names(schema="pepys")
        else:
            table_names = inspector.get_table_names()
            # Exclude spatial tables
            table_names = [
                name
                for name in table_names
                if not name.startswith("idx")
                and not name.startswith("virts")
                and not name.startswith("geometry")
                and not name.startswith("views")
                and not name.startswith("sql")
                and not name.startswith("KNN")
                and not name.startswith("ElementaryGeometries")
                and not name.startswith("data_licenses")
                and not name.lower().startswith("spatial")
            ]
        # Sort table names in alphabetical order
        table_names = sorted(table_names, key=str.casefold, reverse=True)
        return table_names

    def do_view_table(self):
        """Asks user to select a table name. Converts table name to class name,
        fetches the objects up to the number of MAX_ROWS_DISPLAYED, and prints them in table format.
        """
        table_names = self._get_table_names()
        message = "Select a table >"
        selected_table = iterfzf(table_names, prompt=message)
        if selected_table is None:
            return

        text = self.generate_view_table_text(selected_table)
        print(text)

    def generate_view_table_text(self, selected_table):
        headers = []
        associated_attributes = []

        output_text = ""

        # Table names are plural in the database, therefore make it singular
        table = table_name_to_class_name(selected_table)

        if table == constants.ALEMBIC_VERSION:
            with self.data_store.engine.connect() as connection:
                if self.data_store.db_type == "postgres":
                    result = connection.execute(text("SELECT * FROM pepys.alembic_version;"))
                else:
                    result = connection.execute(text("SELECT * FROM alembic_version;"))
                    result = result.fetchall()
                output_text += "Alembic Version\n"
                output_text += tabulate(
                    [[str(column) for column in row] for row in result],
                    headers=["version_number"],
                    tablefmt="grid",
                    floatfmt=".3f",
                )
                output_text += "\n"
                return output_text
        # Find the class
        table_cls = getattr(self.data_store.db_classes, table)
        assert table_cls.__tablename__ == selected_table, "Couldn't find table!"

        # Inspect the class using mapper
        mapper = class_mapper(table_cls)
        for column, column_property in zip(mapper.columns, mapper.column_attrs):
            # Skip RelationshipProperty instances, because their associated attributes are going to be printed
            if column.primary_key is True or isinstance(column_property, RelationshipProperty):
                continue
            # Take only if column is not a foreign key and it is not deferred
            if column_property.deferred is False and not column.foreign_keys:
                headers.append(column.key)
        # Get the association proxy attributes for this table
        associated_attributes, _ = get_assoc_proxy_names_and_objects(table_cls)
        if "privacy_name" in associated_attributes:
            associated_attributes.remove("privacy_name")

        header_attributes = [getattr(table_cls, header_name) for header_name in headers]
        # Fetch first rows up to MAX_ROWS_DISPLAYED, create a table from these rows
        with self.data_store.session_scope():
            values = (
                self.data_store.session.query(table_cls)
                .options(load_only(*header_attributes))
                .limit(MAX_ROWS_DISPLAYED)
                .all()
            )
            headers.extend(associated_attributes)
            # Sort headers
            headers.sort()

            table_data = [[str(getattr(row, column)) for column in headers] for row in values]

            output_text += f"{selected_table}\n"
            output_text += tabulate(
                table_data,
                headers=headers,
                tablefmt="grid",
                floatfmt=".3f",
            )
        output_text += "\n"
        return output_text

    def do_output_table_to_csv(self):
        """Asks user to select a table name. Fetches all objects, and exports them to a CSV file."""
        table_names = self._get_table_names()
        message = "Select a table >"
        selected_table = iterfzf(table_names, prompt=message)
        if selected_table is None:
            return
        path = os.path.join(get_default_export_folder(), f"Pepys_Output_{selected_table}.csv")
        table = table_name_to_class_name(selected_table)
        with self.data_store.engine.connect() as connection:
            if self.data_store.db_type == "postgres":
                sqlQuery = f'SELECT * FROM pepys."{selected_table}";'
                # The nosec comment below tells the Bandit security analysis tool (used by Codacy)
                # to ignore this line. It can't cause a SQL injection attack as the inserted text
                # is selected by the user from a fixed list provided by our code
                results = connection.execute(text(sqlQuery))  # nosec
            else:
                results = connection.execute(text(f"SELECT * FROM {selected_table};"))  # nosec
            results = results.fetchall()

            if table != constants.ALEMBIC_VERSION:
                table_cls = getattr(self.data_store.db_classes, table)
                headers = list(table_cls.__table__.columns.keys())
            else:
                headers = ["version_num"]
            with open(path, "w") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(results)
            print(
                f"{selected_table} table is successfully exported!\nYou can find it here: '{path}'."
            )

    def _check_query_only_select(self, query):
        stripped = query.strip()

        split_by_whitespace = stripped.split()

        if len(split_by_whitespace) > 0:
            # If it doesn't start with SELECT then it is not acceptable
            if split_by_whitespace[0].upper() != "SELECT":
                return False

        split_by_semicolon = stripped.split(";")
        # If there is anything except whitespace after a ; then it is not acceptable
        if len(split_by_semicolon) > 2:
            return False

        if len(split_by_semicolon) == 2 and split_by_semicolon[1].strip() != "":
            return False

        # If we've got here then we're ok
        return True

    def _get_sql_results(self):
        """Asks user to enter a query, then runs it on the database.
        If there isn't any error, returns query and the results."""
        while True:
            print(
                "This feature of Pepys allows you to run arbitrary SQL queries against the Pepys database."
            )
            print("Please use with care, in admin mode these queries can alter data.")
            print("")
            print("Example SQLite query: SELECT * FROM Platforms;")
            print('Example Postgres query: SELECT * from pepys."Platforms";')
            print("")
            query = prompt(
                "> ", multiline=True, bottom_toolbar=bottom_toolbar, lexer=PygmentsLexer(SqlLexer)
            )
            if not self.viewer:
                # In admin mode, accept all queries
                break
            only_select = self._check_query_only_select(query)
            if only_select:
                break
            else:
                custom_print_formatted_text(
                    format_error_message(
                        "Error: Only SELECT queries are allowed in Pepys Viewer. Please enter another query.\n"
                    )
                )
        if query:
            with self.data_store.engine.connect() as connection:
                try:
                    results = connection.execute(text(query))
                    results = results.fetchall()
                    return query, results
                except (
                    ProgrammingError,
                    OperationalError,
                    InvalidRequestError,
                ) as e:
                    print(
                        f"SQL Exception details: {e}\n\n"
                        "ERROR: Query couldn't be executed successfully.\n"
                        "See above for the full error from SQLAlchemy."
                    )
        return None, None

    def do_run_sql(self):
        """Executes the input. Prints the results of the query in table format."""
        query, results = self._get_sql_results()
        if query and results:
            res = f"QUERY\n{'-' * 20}\n{query}\n{'-' * 20}\nRESULT\n"
            res += tabulate(
                [[str(column) for column in row] for row in results],
                tablefmt="grid",
                floatfmt=".3f",
            )
            res += "\n"
            print(res)

    def do_output_sql_to_csv(self):
        """Executes the input. Exports the results of the query to a CSV file."""
        query, results = self._get_sql_results()
        if query and results:
            path = os.path.join(get_default_export_folder(), "Pepys_Output_SQL_Query.csv")
            with open(path, "w") as f:
                writer = csv.writer(f)
                writer.writerow([f"Executed Query: {query}"])
                writer.writerows(results)
            print(f"SQL results are successfully exported!\nYou can find it here: '{path}'.")
