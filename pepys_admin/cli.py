import argparse

from config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_TYPE, DB_USERNAME
from pepys_admin.admin_cli import AdminShell
from pepys_import.core.store.data_store import DataStore
from pepys_import.utils.error_handling import handle_database_errors


def main():  # pragma: no cover
    """
    Main function which parses the command line arguments, creates a :code:`DataStore` object and
    calls :code:`run_admin_shell` to open a shell.
    """
    db_help = (
        "SQLite database file to use (overrides config file database settings). "
        "Use `:memory:` for temporary in-memory instance"
    )
    parser = argparse.ArgumentParser(description="Pepys Admin CLI")
    parser.add_argument("--path", type=str, help="CSV files path")
    parser.add_argument("--db", help=db_help, required=False, default=None)
    args = parser.parse_args()

    if args.db is None:
        data_store = DataStore(
            db_username=DB_USERNAME,
            db_password=DB_PASSWORD,
            db_host=DB_HOST,
            db_port=DB_PORT,
            db_name=DB_NAME,
            db_type=DB_TYPE,
            welcome_text="Pepys_admin",
        )
    else:
        data_store = DataStore(
            db_username="",
            db_password="",
            db_host="",
            db_port=0,
            db_name=args.db,
            db_type="sqlite",
            welcome_text="Pepys_admin",
        )

    run_admin_shell(data_store, args.path)


def run_admin_shell(data_store, path):
    """Runs the :code:`AdminShell`.

    :param data_store: A :class:`DataStore` object
    :type data_store: DataStore
    :param path: CSV files path which will be used by import reference & metadata options
    :type path: String
    :return:
    """
    with handle_database_errors():
        AdminShell(data_store, path).cmdloop()


if __name__ == "__main__":
    main()
