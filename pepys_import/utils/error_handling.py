import sys
from contextlib import contextmanager

import sqlalchemy


@contextmanager
def handle_database_errors():
    try:
        yield
    except (
        sqlalchemy.exc.ProgrammingError,
        sqlalchemy.exc.OperationalError,
        sqlalchemy.exc.InvalidRequestError,
    ) as e:
        print(
            f"SQL Exception details: {e}\n\n"
            "ERROR: SQL error when communicating with database\n"
            "Please check your database structure is up-to-date with that expected "
            "by the version of Pepys you have installed.\n"
            "See above for the full error from SQLAlchemy."
        )
    except ValueError as e:
        if "UUID" in str(e):
            print(
                f"Error converting UUIDs from database.\n"
                "This probably means you're using an outdated SQLite database "
                "which still uses integer primary keys.\nIf possible, delete your database "
                "and start from scratch.\nIf that's not possible then contact support."
            )
        else:
            # Re-raises the ValueError if it wasn't a UUID error
            raise


@contextmanager
def handle_status_errors():
    try:
        yield
    except (
        sqlalchemy.exc.ProgrammingError,
        sqlalchemy.exc.OperationalError,
        sqlalchemy.exc.InvalidRequestError,
    ) as e:
        print(
            "ERROR: Table summaries couldn't be printed.\n"
            "Please check your database structure is up-to-date with that expected "
            "by the version of Pepys you have installed.\n"
        )


@contextmanager
def handle_first_connection_error(connection_string):
    try:
        yield
    except (
        sqlalchemy.exc.ProgrammingError,
        sqlalchemy.exc.OperationalError,
        sqlalchemy.exc.InvalidRequestError,
        sqlalchemy.exc.DatabaseError,
    ) as e:
        print(
            f"SQL Exception details: {e}\n\n"
            "ERROR: SQL error when communicating with database\n"
            f"Please check your database file and the config file's database section.\n"
            f"Current database URL: '{connection_string}'\n"
            "See above for the full error from SQLAlchemy."
        )
        sys.exit(1)
