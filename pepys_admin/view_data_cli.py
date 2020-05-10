import cmd

from iterfzf import iterfzf
from prompt_toolkit import HTML, prompt
from prompt_toolkit.lexers import PygmentsLexer
from pygments.lexers.sql import SqlLexer
from sqlalchemy import inspect
from sqlalchemy.ext.associationproxy import AssociationProxy
from sqlalchemy.orm import RelationshipProperty, class_mapper, load_only
from tabulate import tabulate


def bottom_toolbar():
    return HTML('Press <b><style bg="ansired">ESC+Enter</style></b> to exit!')


class ViewDataShell(cmd.Cmd):
    intro = """--- Menu ---
    (1) View Table
    (2) Run SQL
    (0) Exit
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
        selected_table = iterfzf(table_names)
        # Table names are plural in the database, therefore make it singular
        if selected_table == "alembic_version":
            table = "alembic_version"
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
            if column.primary_key is True:
                primary_key_field = column.key
            # Skip RelationshipProperty instances, because their associated attributes are going to be printed
            if isinstance(column_property, RelationshipProperty):
                continue
            # Take only if column is not a foreign key and it is not deferred
            if column_property.deferred is False and not column.foreign_keys:
                headers.append(column.key)
        # In order to find and extract association_proxy attributes, iterate over all_orm_descriptors
        for descriptor in mapper.all_orm_descriptors:
            if isinstance(descriptor, AssociationProxy):
                name = f"{descriptor.target_collection}_{descriptor.value_attr}"
                associated_attributes.append(name)
        # Fetch first 10 rows, create a table from these rows
        with self.data_store.session_scope():
            values = (
                self.data_store.session.query(table_cls)
                .options(load_only(*headers))
                .limit(10)
                .all()
            )
            headers.extend(associated_attributes)
            res = f"{selected_table}\n"
            res += tabulate(
                [
                    [
                        str(getattr(row, column))[-10:]
                        if column == primary_key_field
                        else str(getattr(row, column))
                        for column in headers
                    ]
                    for row in values
                ],
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
                result = connection.execute(query)
                result = result.fetchall()
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
