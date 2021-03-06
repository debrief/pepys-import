import inspect

from pepys_import.core.store import sqlite_db


def row_to_dict(table_object, data_store):
    """Converts all entities of a table into a dict of {column_name: value}s.

    :param table_object: A table object
    :type table_object: sqlalchemy.ext.declarative.DeclarativeMeta
    :param data_store: A :class:`DataStore` object
    :type data_store: DataStore
    :return: Returns a dictionary with values
    :rtype: Dict
    """
    with data_store.session_scope():
        values = data_store.session.query(table_object).all()
        objects = list()
        for row in values:
            d = {column.name: getattr(row, column.name) for column in row.__table__.columns}
            objects.append(d)
    return objects


def find_sqlite_table_object(table_object, data_store):
    """Finds and returns a SQLite Base class which will be used to create and insert values.

    :param table_object: A table object
    :type table_object: sqlalchemy.ext.declarative.DeclarativeMeta
    :param data_store: A :class:`DataStore` object
    :type data_store: DataStore
    :return: Returns a table object
    :rtype: sqlalchemy.ext.declarative.DeclarativeMeta
    """
    if data_store.db_type == "postgres":
        for name, obj in inspect.getmembers(sqlite_db):
            if inspect.isclass(obj) and name == table_object.__name__:
                return obj
    else:
        return table_object


def export_reference_tables(source_store, destination_store, table_objects):
    """Copies table objects from :code:`source_store` to :code:`destination_store`.

    :param source_store: A :class:`DataStore` object to fetch objects
    :type source_store: DataStore
    :param destination_store: A :class:`DataStore` object to copy the objects from source_store
    :type destination_store: DataStore
    :param table_objects: A list of table objects
    :type table_objects: List
    :return:
    """
    for table_object in table_objects:
        dict_values = row_to_dict(table_object, source_store)
        object_ = find_sqlite_table_object(table_object, source_store)
        with destination_store.session_scope():
            destination_store.session.bulk_insert_mappings(object_, dict_values)


def export_metadata_tables(source_store, destination_store, privacy_ids):
    """Copies :code:`Platform`, :code:`Sensor` and :code:`Synonym` objects from
    :code:`source_store` to :code:`destination_store`.

    :param source_store: A :class:`DataStore` object to fetch objects
    :type source_store: DataStore
    :param destination_store: A :class:`DataStore` object to copy the objects from source_store
    :type destination_store: DataStore
    :param privacy_ids: A list of Privacy ID's which is used to filter Platform and Sensor objects
    :type privacy_ids: List
    :return:
    """
    for table_object in [
        source_store.db_classes.Platform,
        source_store.db_classes.Sensor,
        source_store.db_classes.Synonym,
    ]:
        with source_store.session_scope():
            dict_values = list()
            if table_object.__name__ == "Platform":
                values = (
                    source_store.session.query(table_object)
                    .filter(table_object.privacy_id.in_(privacy_ids))
                    .all()
                )
                platform_ids = [row.platform_id for row in values]
            elif table_object.__name__ == "Sensor":
                values = (
                    source_store.session.query(table_object)
                    .filter(table_object.host.in_(platform_ids))
                    .filter(table_object.privacy_id.in_(privacy_ids))
                    .all()
                )
                sensor_ids = [row.sensor_id for row in values]
            else:
                all_ids = list()
                all_ids.extend(platform_ids)
                all_ids.extend(sensor_ids)
                values = (
                    source_store.session.query(source_store.db_classes.Synonym)
                    .filter(source_store.db_classes.Synonym.entity.in_(all_ids))
                    .all()
                )
            for row in values:
                d = {column.name: getattr(row, column.name) for column in row.__table__.columns}
                dict_values.append(d)

            object_ = find_sqlite_table_object(table_object, source_store)
            with destination_store.session_scope():
                destination_store.session.bulk_insert_mappings(object_, dict_values)
