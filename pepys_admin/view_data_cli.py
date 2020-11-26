import csv
import os

from iterfzf import iterfzf
from prompt_toolkit import HTML, prompt
from prompt_toolkit.lexers import PygmentsLexer
from pygments.lexers.sql import SqlLexer
from sqlalchemy import inspect
from sqlalchemy.exc import InvalidRequestError, OperationalError, ProgrammingError
from sqlalchemy.ext.associationproxy import AssociationProxy
from sqlalchemy.orm import RelationshipProperty, class_mapper, load_only
from tabulate import tabulate

from pepys_admin.base_cli import BaseShell
from pepys_admin.utils import get_default_export_folder
from pepys_import.core.store import constants
from pepys_import.utils.table_name_utils import table_name_to_class_name

MAX_ROWS_DISPLAYED = 500


def bottom_toolbar():
    return HTML("Press <b>ESC then Enter</b> to exit!")


class ViewDataShell(BaseShell):
    """Offers to view table and run SQL."""

    intro = """--- Menu ---
    (1) View Table
    (2) Output Table to CSV
    (3) Run SQL
    (4) Output SQL Results to CSV
    (.) Back
    """
    prompt = "(pepys-admin) (view) "

    def __init__(self, data_store):
        super(ViewDataShell, self).__init__()
        self.data_store = data_store
        self.aliases = {
            ".": self.do_cancel,
            "1": self.do_view_table,
            "2": self.do_output_table_to_csv,
            "3": self.do_run_sql,
            "4": self.do_output_sql_to_csv,
        }

    @staticmethod
    def do_cancel():
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
                and not name.lower().startswith("spatial")
            ]
        # Sort table names in alphabetical order
        table_names = sorted(table_names, key=str.casefold, reverse=True)
        return table_names

    def do_view_table(self):
        """Asks user to select a table name. Converts table name to class name,
        fetches the objects up to the number of MAX_ROWS_DISPLAYED, and prints them in table format.
        """
        headers = list()
        associated_attributes = list()
        table_names = self._get_table_names()
        message = "Select a table >"
        selected_table = iterfzf(table_names, prompt=message)
        if selected_table is None:
            return
        # Table names are plural in the database, therefore make it singular
        table = table_name_to_class_name(selected_table)

        if table == constants.ALEMBIC_VERSION:
            with self.data_store.engine.connect() as connection:
                if self.data_store.db_type == "postgres":
                    result = connection.execute("SELECT * FROM pepys.alembic_version;")
                else:
                    result = connection.execute("SELECT * FROM alembic_version;")
                    result = result.fetchall()
                res = "Alembic Version\n"
                res += tabulate(
                    [[str(column) for column in row] for row in result],
                    headers=["version_number"],
                    tablefmt="grid",
                    floatfmt=".3f",
                )
                res += "\n"
                print(res)
            return
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
        # In order to find and extract association_proxy attributes, iterate over all_orm_descriptors
        for descriptor in mapper.all_orm_descriptors:
            if isinstance(descriptor, AssociationProxy):
                name = f"{descriptor.target_collection}_{descriptor.value_attr}"
                if name != "privacy_name":
                    associated_attributes.append(name)
        # Fetch first rows up to MAX_ROWS_DISPLAYED, create a table from these rows
        with self.data_store.session_scope():
            values = (
                self.data_store.session.query(table_cls)
                .options(load_only(*headers))
                .limit(MAX_ROWS_DISPLAYED)
                .all()
            )
            headers.extend(associated_attributes)
            # Sort headers
            headers.sort()
            res = f"{selected_table}\n"
            res += tabulate(
                [[str(getattr(row, column)) for column in headers] for row in values],
                headers=headers,
                tablefmt="grid",
                floatfmt=".3f",
            )
        res += "\n"
        print(res)

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
                results = connection.execute(f'SELECT * FROM pepys."{selected_table}";')
            else:
                results = connection.execute(f"SELECT * FROM {selected_table};")
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

    def _get_sql_results(self):
        """Asks user to enter a query, then runs it on the database.
        If there isn't any error, returns query and the results."""
        query = prompt(
            "> ", multiline=True, bottom_toolbar=bottom_toolbar, lexer=PygmentsLexer(SqlLexer)
        )
        if query:
            with self.data_store.engine.connect() as connection:
                try:
                    results = connection.execute(query)
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
