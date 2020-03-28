import argparse

from config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_TYPE, DB_USERNAME
from pepys_admin.admin_cli import AdminShell
from pepys_import.core.store.data_store import DataStore


def main():
    parser = argparse.ArgumentParser(description="Pepys Admin CLI")
    parser.add_argument("--path", type=str, help="CSV files path")
    args = parser.parse_args()

    data_store = DataStore(
        db_username=DB_USERNAME,
        db_password=DB_PASSWORD,
        db_host=DB_HOST,
        db_port=DB_PORT,
        db_name=DB_NAME,
        db_type=DB_TYPE,
    )

    AdminShell(data_store, args.path).cmdloop()


if __name__ == "__main__":
    main()