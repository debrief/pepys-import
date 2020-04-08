import argparse

import sqlalchemy

from config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_TYPE, DB_USERNAME
from pepys_admin.admin_cli import AdminShell
from pepys_import.core.store.data_store import DataStore


def main():
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

    try:
        AdminShell(data_store, args.path).cmdloop()
    except sqlalchemy.exc.ProgrammingError as e:
        print(
            f"SQL Exception details: {e}\n\n"
            "ERROR: SQL error when communicating with database\n"
            "Please check your database structure is up-to-date with that expected "
            "by the version of Pepys you have installed.\n"
            "See above for the full error from SQLAlchemy."
        )


if __name__ == "__main__":
    main()
