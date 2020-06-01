import cmd

from iterfzf import iterfzf
from prompt_toolkit import HTML, prompt
from prompt_toolkit.lexers import PygmentsLexer
from pygments.lexers.sql import SqlLexer
from sqlalchemy import inspect
from sqlalchemy.exc import InvalidRequestError, OperationalError, ProgrammingError
from sqlalchemy.ext.associationproxy import AssociationProxy
from sqlalchemy.orm import RelationshipProperty, class_mapper, load_only
from tabulate import tabulate


def bottom_toolbar():
    return HTML("Press <b>ESC then Enter</b> to exit!")


class ViewDataShell(cmd.Cmd):
    intro = """--- Menu ---
    (1) View Table
    (2) Run SQL
    (0) Back
    """
    prompt = "(pepys-admin) (view) "

    def __init__(self, data_store):
        super(ViewDataShell, self).__init__()
        self.data_store = data_store
        self.aliases = {
            "0": self.do_cancel,
            "1": self.do_view_table,
            "2": self.do_run_sql,
        }

    @staticmethod
    def do_cancel():
        print("Returning to the previous menu...")

    def do_view_table(self):
        primary_key_field = None
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
        if (
            selected_table == "alembic_version"
            or selected_table == "HostedBy"
            or selected_table == "Media"
        ):
            table = selected_table
        elif selected_table == "Geometries":
            table = "Geometry1"
        elif selected_table.endswith("ies"):
            table = selected_table[:-3] + "y"
        else:
            table = selected_table[:-1]
        # Find the class
        table_cls = getattr(self.data_store.db_classes, table)
        assert table_cls.__tablename__ == selected_table, "Table couldn't find!"

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

    def do_run_sql(self):
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

    def default(self, line):
        cmd_, arg, line = self.parseline(line)
        if cmd_ in self.aliases:
            self.aliases[cmd_]()
            if cmd_ == "0":
                return True
        else:
            print(f"*** Unknown syntax: {line}")

    def postcmd(self, stop, line):
        if line != "0":
            print("-" * 61)
            print(self.intro)
        return cmd.Cmd.postcmd(self, stop, line)
