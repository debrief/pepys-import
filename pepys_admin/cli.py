import argparse
from importlib import reload
import os

import config
from pepys_admin.admin_cli import AdminShell
from pepys_import.cli import set_up_training_mode
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
    training_help = (
        "Uses training mode, where all interactions take place with a training database located "
        "in the user's home folder. No actions will affect the database configured in the Pepys config file."
    )
    parser = argparse.ArgumentParser(description="Pepys Admin CLI")
    parser.add_argument("--path", type=str, help="CSV files path")

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--training", help=training_help, dest="training", default=False, action="store_true"
    )
    group.add_argument("--db", help=db_help, required=False, default=None)

    args = parser.parse_args()

    run_admin_shell(db=args.db, path=args.path, training=args.training)


def run_admin_shell(path, training=False, data_store=None, db=None):
    """Runs the admin shell.

    Arguments allow specification of individual args from command-line
    (db, path, training) or specification of a data_store instead of a db name,
    to allow for advanced use in unit tests.
    """
    if data_store is not None and db is not None:
        raise ValueError("Cannot specify both db and data_store")

    if training:
        set_up_training_mode()

    # Reload the config file in case we're in a long-running process because of pytest and
    # the config file details have changed since the last test
    reload(config)

    if data_store is None:
        if db is None:
            data_store = DataStore(
                db_username=config.DB_USERNAME,
                db_password=config.DB_PASSWORD,
                db_host=config.DB_HOST,
                db_port=config.DB_PORT,
                db_name=config.DB_NAME,
                db_type=config.DB_TYPE,
                welcome_text="Pepys_admin",
                training_mode=training,
            )
        else:
            data_store = DataStore(
                db_username="",
                db_password="",
                db_host="",
                db_port=0,
                db_name=db,
                db_type="sqlite",
                welcome_text="Pepys_admin",
                training_mode=training,
            )

    try:
        with handle_database_errors():
            AdminShell(data_store, path).cmdloop()
    except SystemExit:
        # This makes sure that calling exit() from within our code doesn't actually exit immediately,
        # instead it drops out to here, where we can still ask the final training mode question
        pass

    if training:
        answer = input("Would you like to reset the training database? (y/n) ")
        if answer.upper() == "Y":
            if os.path.exists(config.DB_NAME):
                os.remove(config.DB_NAME)


if __name__ == "__main__":
    main()
