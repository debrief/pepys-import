import cmd

from iterfzf import iterfzf
from prompt_toolkit import PromptSession
from prompt_toolkit.lexers import PygmentsLexer
from pygments.lexers.sql import SqlLexer
from sqlalchemy import inspect
from tabulate import tabulate


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
        if selected_table.endswith("ies"):
            table = selected_table[:-3] + "y"
        else:
            table = selected_table[:-1]
        # Find the class
        table_obj = getattr(self.data_store.db_classes, table)
        assert table_obj.__tablename__ == selected_table, "Table couldn't find!"

        headers = [m.key for m in table_obj.__table__.columns]
        # Fetch first 10 rows, create a table from these rows
        with self.data_store.session_scope():
            values = self.data_store.session.query(table_obj).limit(10).all()
            res = f"{selected_table}\n"
            res += tabulate(
                [[str(getattr(row, column)) for column in headers] for row in values],
                headers=headers,
                tablefmt="github",
            )
            res += "\n"
        print(res)

    def do_run_sql(self):
        session = PromptSession(lexer=PygmentsLexer(SqlLexer))
        query = session.prompt("Press ESC+Enter to exit> ", multiline=True)
        with self.data_store.engine.connect() as connection:
            result = connection.execute(query)
            result = result.fetchall()
        print(result)

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
