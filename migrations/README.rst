Database Migration
==================

Pepys repository uses `Alembic <https://github.com/alembic/alembic>`_ for data migration.

Instructions
------------
If this is your first time using Alembic, please do the followings:

1. Alembic reads DB configurations from the repository's config file( :code:`config.py`). Please check your :code:`PEPYS_CONFIG`
environment variable. If it doesn't exist, it means that :code:`default_config.ini` will be used to create a connection.

2. If you have an existing DB with tables and values, you have two options:

  - The easiest option is removing your schema (or entire DB for SQLite) completely and creating from the scratch.
    You might run :code:`alembic upgrade head` which is going to create all DB tables and :code:`alembic_version table`.
    It will *stamp* Alembic's head to the latest migration. You might see this migration revision ID in :code:`alembic_version table`.
  - (**NOT SUGGESTED!**) If you don't want to lose your data in the DB, you might create alembic_version table and stamp it manually.
    For doing that, please run the following commands:

    **Postgres**

    .. code-block:: none

        CREATE TABLE pepys.alembic_version
        (
            version_num VARCHAR(32) NOT NULL,
            CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
        );

        INSERT INTO pepys.alembic_version VALUES ('5154f7db278d');

    If you have the same schema with the base migration script, you won't have any problem. You can test it with this command:
    :code:`alembic current`. If it doesn't throw any error, it is okay to go!

    **SQLite**

    .. code-block:: none
        CREATE TABLE alembic_version
        (
            version_num VARCHAR(32) NOT NULL,
            CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
        );
        INSERT INTO alembic_version (version_num)
        VALUES ('7df9dcbd47e7');

    Please try the same command as above and check if there is any error or not.

If it is working without any problem, you can use now Alembic according to your needs.

Possible Errors and Solutions
-----------------------------

.. code-block:: none

    File "migrations/env.py", line 9, in <module>
    from config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_TYPE, DB_USERNAME
    ModuleNotFoundError: No module named 'config'

If you face this error, it means that pepys-import repository should be added to :code:`PYTHONPATH. Please run the
following command when you are at the root of the repository:

.. code-block:: none

    export PYTHONPATH=.

Error should be corrected now. Please try to run the same command again.

Helpful Commands
----------------
If you would like to see the current head of Alembic: :code:`alembic current`

If you would like to see the history of the migration: :code:`alembic history`

If you have changed schema and want to create a migration script: :code:`alembic revision -m "YOUR MESSAGE" --autogenerate`

If you woud like to see SQL script of migration scripts: :code:`alembic upgrade START:END --sql`

