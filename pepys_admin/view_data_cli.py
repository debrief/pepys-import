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
from pepys_import.core.store import constants
from pepys_import.utils.table_name_utils import table_name_to_class_name


def bottom_toolbar():
    return HTML("Press <b>ESC then Enter</b> to exit!")


class ViewDataShell(BaseShell):
    """Offers to view table and run SQL."""

    intro = """--- Menu ---
    (1) View Table
    (2) Run SQL
    (.) Back
    """
    prompt = "(pepys-admin) (view) "

    def __init__(self, data_store):
        super(ViewDataShell, self).__init__()
        self.data_store = data_store
        self.aliases = {
            ".": self.do_cancel,
            "1": self.do_view_table,
            "2": self.do_run_sql,
        }

    @staticmethod
    def do_cancel():
        """Returns to the previous menu"""
        print("Returning to the previous menu...")

    def do_view_table(self):
        """Asks user to select a table name. Converts table name to class name,
        fetches the first 50 objects, and prints them in table format.
        """
        headers = list()
        associated_attributes = list()
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
                    tablefmt="github",
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
        # Fetch first 10 rows, create a table from these rows
        with self.data_store.session_scope():
            try:
                values = (
                    self.data_store.session.query(table_cls)
                    .options(load_only(*headers))
                    .limit(50)
                    .all()
                )
                headers.extend(associated_attributes)
                # Sort headers
                headers.sort()
                res = f"{selected_table}\n"
                res += tabulate(
                    [[str(getattr(row, column)) for column in headers] for row in values],
                    headers=headers,
                    tablefmt="github",
                    floatfmt=".3f",
                )
                res += "\n"
                print(res)
            except Exception as e:
                print(f"Viewing table failed! Please check the error message: {e}")
                return

    def do_run_sql(self):
        """Executes the input. Prints the results of the query in table format."""
        query = prompt(
            "> ", multiline=True, bottom_toolbar=bottom_toolbar, lexer=PygmentsLexer(SqlLexer)
        )
        if query:
            with self.data_store.engine.connect() as connection:
                try:
                    result = connection.execute(query)
                    result = result.fetchall()
                except (ProgrammingError, OperationalError, InvalidRequestError,) as e:
                    print(
                        f"SQL Exception details: {e}\n\n"
                        "ERROR: Query couldn't be executed successfully.\n"
                        "See above for the full error from SQLAlchemy."
                    )
                    return

            res = f"QUERY\n{'-' * 20}\n{query}\n{'-' * 20}\nRESULT\n"
            res += tabulate(
                [[str(column) for column in row] for row in result],
                tablefmt="github",
                floatfmt=".3f",
            )
            res += "\n"
            print(res)
