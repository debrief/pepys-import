import inspect

from geoalchemy2.elements import WKTElement
from sqlalchemy import or_
from sqlalchemy.sql.functions import func

from pepys_import.core.store import sqlite_db
from pepys_import.core.store.db_status import TableTypes


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


def export_metadata_tables(source_store, destination_store, privacy_ids=None):
    """Copies :code:`Platform`, :code:`Sensor`, :code:`Datafile` and :code:`Synonym` objects from
    :code:`source_store` to :code:`destination_store`.

    :param source_store: A :class:`DataStore` object to fetch objects
    :type source_store: DataStore
    :param destination_store: A :class:`DataStore` object to copy the objects from source_store
    :type destination_store: DataStore
    :param privacy_ids: A list of Privacy ID's which is used to filter objects
    :type privacy_ids: List
    :return:
    """
    for table_object in [
        source_store.db_classes.Platform,
        source_store.db_classes.Sensor,
        source_store.db_classes.Datafile,
        source_store.db_classes.Synonym,
    ]:
        with source_store.session_scope():
            dict_values = list()
            if table_object.__name__ == "Platform":
                query = source_store.session.query(table_object)
                if privacy_ids is not None:
                    query = query.filter(table_object.privacy_id.in_(privacy_ids))
                values = query.all()

                platform_ids = [row.platform_id for row in values]
            elif table_object.__name__ == "Sensor":
                query = source_store.session.query(table_object).filter(
                    table_object.host.in_(platform_ids)
                )
                if privacy_ids is not None:
                    query = query.filter(table_object.privacy_id.in_(privacy_ids))
                values = query.all()
                sensor_ids = [row.sensor_id for row in values]
            elif table_object.__name__ == "Datafile":
                query = source_store.session.query(table_object)
                if privacy_ids is not None:
                    query = query.filter(table_object.privacy_id.in_(privacy_ids))

                values = query.all()
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


def export_all_measurement_tables(source_store, destination_store):
    measurement_table_objects = source_store.meta_classes[TableTypes.MEASUREMENT]

    for table in measurement_table_objects:
        export_measurement_table_with_filter(source_store, destination_store, table)


def export_measurement_table_with_filter(source_store, destination_store, table, filter=None):
    if isinstance(table, str):
        table_object = getattr(source_store.db_classes, table)
    else:
        table_object = table

    dict_values = []
    query = source_store.session.query(table_object)

    if filter is not None:
        query = filter(table_object, query)

    results = query.all()

    if len(results) == 0:
        return

    data_attributes = []
    for col in table_object.__table__.columns:
        prop = getattr(table_object, col.name).property
        data_attributes.append(prop.key)

    for row in results:
        d = {}
        for attrib in data_attributes:
            d[attrib] = getattr(row, attrib)
        # TODO: Improve this
        # This is not necessarily the most efficient way of doing this, as we're looking for
        # an attribute starting with _ for each
        # for col in row.__table__.columns:
        #     try:
        #         value = getattr(row, "_" + col.name)
        #     except AttributeError:
        #         value = getattr(row, col.name)
        #     d[col.name] = value
        # dict_values.append(row.__dict__)
        dict_values.append(d)

    object_ = find_sqlite_table_object(table, source_store)
    with destination_store.session_scope():
        destination_store.session.bulk_insert_mappings(object_, dict_values)


def export_measurement_tables_filtered_by_time(
    source_store, destination_store, start_time, end_time
):
    def time_attribute_filter(table_object, query):
        """Filters on the time attribute of a table, so works for State, Contact, LogsHolding and Comment"""
        query = query.filter(table_object.time >= start_time)
        query = query.filter(table_object.time <= end_time)

        return query

    def start_end_attribute_filter(table_object, query):
        query = query.filter(
            or_(
                (  # Deal with entries where start is missing, so just do a standard 'between' search on end
                    (table_object.start == None)  # noqa
                    & (table_object.end >= start_time)
                    & (table_object.end <= end_time)
                ),
                (  # Deal with entries where end is missing, so just do a standard 'between' search on start
                    (table_object.end == None)  # noqa
                    & (table_object.start >= start_time)
                    & (table_object.start <= end_time)
                ),
                or_(  # Deal with entries where we have both start and end, and want to test all overlap possibilities
                    ((table_object.start >= start_time) & (table_object.end <= end_time)),
                    ((table_object.start >= start_time) & (table_object.end >= end_time)),
                    ((table_object.start <= start_time) & (table_object.end <= end_time)),
                    ((table_object.start <= start_time) & (table_object.end >= end_time)),
                ),
            )
        )
        return query

    export_measurement_table_with_filter(
        source_store, destination_store, source_store.db_classes.State, time_attribute_filter
    )
    export_measurement_table_with_filter(
        source_store, destination_store, source_store.db_classes.Contact, time_attribute_filter
    )
    export_measurement_table_with_filter(
        source_store, destination_store, source_store.db_classes.Comment, time_attribute_filter
    )
    export_measurement_table_with_filter(
        source_store, destination_store, source_store.db_classes.LogsHolding, time_attribute_filter
    )
    export_measurement_table_with_filter(
        source_store, destination_store, source_store.db_classes.Media, time_attribute_filter
    )

    export_measurement_table_with_filter(
        source_store,
        destination_store,
        source_store.db_classes.Activation,
        start_end_attribute_filter,
    )
    export_measurement_table_with_filter(
        source_store,
        destination_store,
        source_store.db_classes.Geometry1,
        start_end_attribute_filter,
    )


def export_measurement_tables_filtered_by_location(
    source_store, destination_store, xmin, ymin, xmax, ymax
):
    def location_attribute_filter(table_object, query):
        # Note: We can't use the ST_MakeEnvelope function, as it's not supported by spatialite
        # so we have to create the WKT polygon manually. This is only done once for the filter
        # so it shouldn't have an efficiency impact
        wkt = f"POLYGON(({xmin} {ymin},{xmin} {ymax},{xmax} {ymax},{xmax} {ymin},{xmin} {ymin}))"
        query = query.filter(
            func.ST_Within(
                table_object.location,
                # func.ST_MakeEnvelope(xmin, ymin, xmax, ymax, 4326),
                WKTElement(wkt, srid=4326),
            )
        )
        return query

    export_measurement_table_with_filter(
        source_store, destination_store, source_store.db_classes.State, location_attribute_filter
    )
