from datetime import datetime
from getpass import getuser

from sqlalchemy.orm import undefer
from sqlalchemy.orm.session import make_transient

from pepys_admin.utils import make_query_for_unique_cols_or_all
from pepys_import.core.store.db_status import TableTypes
from pepys_import.utils.data_store_utils import shorten_uuid


def merge_all_reference_tables(master_store, slave_store):
    """Merges all reference tables from the slave_store into the master_store.

    Deals with all possible differences between slave and master, for example, data that is in both already
    data only in slave, data added to both separately (so fields match but primary keys don't) etc.
    """
    master_store.setup_table_type_mapping()
    reference_table_objects = master_store.meta_classes[TableTypes.REFERENCE]

    reference_table_names = [obj.__name__ for obj in reference_table_objects]

    # Put the GeometryType table at the front of the list, so that it gets
    # done first - as GeometrySubType depends on it
    reference_table_names.remove("GeometryType")
    reference_table_names.insert(0, "GeometryType")

    for ref_table in reference_table_names:
        id_results = merge_reference_table(ref_table, master_store, slave_store)
        update_synonyms_table(master_store, slave_store, id_results["modified"])
        # update_logs_table(master_store, slave_store, id_results["modified"])


def merge_reference_table(table_object_name, master_store, slave_store):
    # Get references to the table from the master and slave DataStores
    master_table = getattr(master_store.db_classes, table_object_name)
    slave_table = getattr(slave_store.db_classes, table_object_name)

    primary_key = master_table.__table__.primary_key.columns.values()[0].name

    # Keep track of each ID and what its status is
    ids_already_there = []
    ids_added = []
    ids_modified_from = []
    ids_modified_to = []

    with slave_store.session_scope():
        with master_store.session_scope():
            slave_entries = slave_store.session.query(slave_table).options(undefer("*")).all()

            for slave_entry in slave_entries:
                print(f"Slave entry: {slave_entry}")
                guid = getattr(slave_entry, primary_key)

                results = (
                    master_store.session.query(master_table)
                    .filter(getattr(master_table, primary_key) == guid)
                    .all()
                )

                n_results = len(results)

                if n_results == 0:
                    print(" - No results, searching by name")
                    search_by_name_results = (
                        master_store.session.query(master_table)
                        .filter(master_table.name == slave_entry.name)
                        .all()
                    )
                    n_name_results = len(search_by_name_results)

                    if n_name_results == 0:
                        print("  - Not in master db, copying over")
                        ids_added.append(guid)
                        make_transient(slave_entry)
                        master_store.session.add(slave_entry)
                    elif n_name_results == 1:
                        print("  - In master db, making GUIDs match and cascading")
                        ids_modified_from.append(guid)
                        ids_modified_to.append(getattr(search_by_name_results[0], primary_key))
                        setattr(
                            slave_entry,
                            primary_key,
                            getattr(search_by_name_results[0], primary_key),
                        )
                        slave_store.session.add(slave_entry)
                        slave_store.session.commit()
                    else:
                        assert False
                elif n_results == 1:
                    print(" - Already in master DB with same GUID, don't need to copy")
                    ids_already_there.append(guid)
                else:
                    assert False

    return {
        "already_there": ids_already_there,
        "added": ids_added,
        "modified": {"from": ids_modified_from, "to": ids_modified_to},
    }


def merge_all_metadata_tables(master_store, slave_store, merge_change_id):
    master_store.setup_table_type_mapping()
    metadata_table_objects = master_store.meta_classes[TableTypes.METADATA]

    metadata_table_names = [obj.__name__ for obj in metadata_table_objects]

    # Crude ordering system for now (TODO: Improve)
    # Put Platform first, then Sensor, then rest of them
    metadata_table_names.remove("Platform")
    metadata_table_names.remove("Sensor")
    metadata_table_names.insert(0, "Sensor")
    metadata_table_names.insert(0, "Platform")

    # Remove various entries for now - deal with those separately later
    metadata_table_names.remove("Datafile")
    metadata_table_names.remove("Log")
    metadata_table_names.remove("Change")
    metadata_table_names.remove("Synonym")

    for ref_table in metadata_table_names:
        id_results = merge_metadata_table(ref_table, master_store, slave_store, merge_change_id)
        update_synonyms_table(master_store, slave_store, id_results["modified"])
        # update_logs_table(master_store, slave_store, id_results["modified"])


def update_master_from_slave_entry(
    master_store, slave_store, master_entry, slave_entry, merge_change_id
):
    column_names = [col.name for col in master_entry.__table__.columns.values()]
    primary_key = master_entry.__table__.primary_key.columns.values()[0].name

    modified = False

    # Loop through all fields on master entry
    for col_name in column_names:
        # If field is missing on master entry
        if getattr(master_entry, col_name) is None:
            # Look to see if it has a value in the slave entry
            if getattr(slave_entry, col_name) is not None:
                # Set it on the master entry, and note that we've modified the entry
                setattr(master_entry, col_name, getattr(slave_entry, col_name))
                # Create a Log entry to say that we changed this attribute
                master_store.add_to_logs(
                    table=master_entry.__table__.name,
                    row_id=getattr(master_entry, primary_key),
                    field=col_name,
                    new_value=getattr(slave_entry, col_name),
                    change_id=merge_change_id,
                )
                # Note that we modified it, so we can update in DB if necessary
                modified = True

    if modified:
        master_store.session.add(master_entry)
        master_store.session.commit()


def merge_metadata_table(table_object_name, master_store, slave_store, merge_change_id):
    # Get references to the table from the master and slave DataStores
    master_table = getattr(master_store.db_classes, table_object_name)
    slave_table = getattr(slave_store.db_classes, table_object_name)

    primary_key = master_table.__table__.primary_key.columns.values()[0].name

    # Keep track of each ID and what its status is
    ids_already_there = []
    ids_added = []
    ids_modified_from = []
    ids_modified_to = []

    with slave_store.session_scope():
        with master_store.session_scope():
            # Get all entries in this table in the slave database
            slave_entries = slave_store.session.query(slave_table).options(undefer("*")).all()

            for slave_entry in slave_entries:
                print(f"Slave entry: {slave_entry}")
                guid = getattr(slave_entry, primary_key)

                # Find all entries with this GUID in the same table in the master database
                results = (
                    master_store.session.query(master_table)
                    .filter(getattr(master_table, primary_key) == guid)
                    .all()
                )

                n_results = len(results)

                if n_results == 0:
                    # The GUID isn't present in the master database
                    # This means this record wasn't originally taken from the master db
                    # but both the master and slave dbs may have had the same entry added
                    # with the same details - so we need to check whether there is an entry
                    # with the same values
                    print(" - No results, searching by all fields")
                    search_by_all_fields_results = make_query_for_unique_cols_or_all(
                        master_table, slave_entry, master_store.session
                    ).all()
                    n_all_field_results = len(search_by_all_fields_results)

                    if n_all_field_results == 0:
                        # We can't find an entry which matches in the master db,
                        # so this is a new entry from the slave which needs copying over
                        print("  - Not in master db, copying over")
                        ids_added.append(guid)
                        slave_store.session.expunge(slave_entry)
                        make_transient(slave_entry)
                        master_store.session.merge(slave_entry)
                    elif n_all_field_results == 1:
                        # We found an entry that matches in the master db, but it'll have a different
                        # GUID - so update the GUID in the slave database and let it propagate
                        # so we can copy over other tables later and all the foreign key integrity will work
                        print("  - In master db, making GUIDs match and cascading")
                        ids_modified_from.append(guid)
                        ids_modified_to.append(
                            getattr(search_by_all_fields_results[0], primary_key)
                        )
                        setattr(
                            slave_entry,
                            primary_key,
                            getattr(search_by_all_fields_results[0], primary_key),
                        )
                        slave_store.session.add(slave_entry)
                        slave_store.session.commit()

                        # We also need to compare the fields of the slave entry and the master entry
                        # and update any master fields that are currently None with values from the slave entry
                        update_master_from_slave_entry(
                            master_store,
                            slave_store,
                            search_by_all_fields_results[0],
                            slave_entry,
                            merge_change_id,
                        )
                    else:
                        assert False
                elif n_results == 1:
                    # The GUID is in the master db - so the record must also be there (as GUIDs are unique)
                    print(" - Already in master DB with same GUID, don't need to copy")
                    ids_already_there.append(guid)
                else:
                    # We should never get here: the GUID should always appear in the master database either zero or one times,
                    # never more
                    assert False

    return {
        "already_there": ids_already_there,
        "added": ids_added,
        "modified": {"from": ids_modified_from, "to": ids_modified_to},
    }


def update_synonyms_table(master_store, slave_store, modified_ids):
    with slave_store.session_scope():
        # For each modified ID
        for from_id, to_id in zip(modified_ids["from"], modified_ids["to"]):
            # Search for it in the Synonyms table
            results = (
                slave_store.session.query(slave_store.db_classes.Synonym)
                .filter(slave_store.db_classes.Synonym.entity == from_id)
                .all()
            )

            if len(results) > 0:
                print(f"Found {len(results)} results")
                # If it exists, then modify the old ID to the new ID
                for result in results:
                    print(
                        f"Changing synonym for {result.synonym} with id {shorten_uuid(result.entity)} to {shorten_uuid(to_id)}"
                    )
                    result.entity = to_id

            # Commit changes
            slave_store.session.add_all(results)
            slave_store.session.commit()


def update_logs_table(master_store, slave_store, modified_ids):
    with slave_store.session_scope():
        # For each modified ID
        for from_id, to_id in zip(modified_ids["from"], modified_ids["to"]):
            # Search for it in the Logs table
            results = (
                slave_store.session.query(slave_store.db_classes.Log)
                .filter(slave_store.db_classes.Log.id == from_id)
                .all()
            )

            if len(results) > 0:
                print(f"Found {len(results)} results")
                # If it exists, then modify the old ID to the new ID
                for result in results:
                    print(
                        f"Changing log id with id {shorten_uuid(result.id)} to {shorten_uuid(to_id)}"
                    )
                    result.id = to_id

            # Commit changes
            slave_store.session.add_all(results)
            slave_store.session.commit()


def split_list(lst, n=100):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def rows_to_list_of_dicts(results):
    """Converts a list of rows returned from a SQLAlchemy query into a list of dicts.

    The obvious way to do this would be to look in the __table__ attribute of the row
    and get the column names, and then extract those values from the row. However, this
    will not work for the Measurement tables, as the attributes of the class have different
    names to the column names. For example, the column name is "speed" but the attribute
    name is "_speed" and a property (with getter and setter methods) is used to convert
    between the two. The bulk_insert_mappings method doesn't use the Table object,
    so doesn't use the properties to do the conversion.

    Therefore, we need to have *all* of the attributes of this class, including the attributes
    starting with _. However, we don't want the SQLAlchemy internal attributes, or the 'dunder'
    methods that start with a __. Therefore, this function excludes those, but keeps all others.

    We also need to process the location field to make sure it is in WKT format so the database
    can understand it.

    """
    dict_results = []
    attributes_to_use = None
    for row in results:
        if attributes_to_use is None:
            attributes_to_use = [attrib for attrib in dir(row) if not attrib.startswith("__")]
            attributes_to_use.remove("_decl_class_registry")
            attributes_to_use.remove("_sa_class_manager")
            attributes_to_use.remove("_sa_instance_state")

        d = {key: getattr(row, key) for key in attributes_to_use}

        # Deal with the location field, making sure it gets converted to WKT so it can be inserted
        # into the db
        if "location" in d:
            d["_location"] = d["location"].to_wkt()

        # TODO: This function will fail for Geometry1 objects at the moment, as the geometry field is
        # not processed properly. This table isn't used at the moment, but this should be fixed
        # before the table is used

        dict_results.append(d)

    return dict_results


def merge_measurement_table(table_object_name, master_store, slave_store, added_datafile_ids):
    # We don't need to do a 'merge' as such for the measurement tables. Instead we just need to add
    # the measurement entries for datafiles which hadn't already been imported into the master
    # database.
    # These come from the 'added' list of IDs from the datafile merging function and are
    # passed to this function

    master_table = getattr(master_store.db_classes, table_object_name)
    slave_table = getattr(slave_store.db_classes, table_object_name)

    to_add = []

    with slave_store.session_scope():
        with master_store.session_scope():
            # Split the IDs list up into 100 at a time, as otherwise the SQL query could get longer
            # than SQLite or Postgres allows - as it'll have a full UUID string in it for each
            # datafile ID
            for datafile_ids_chunk in split_list(added_datafile_ids):
                # Search for all slave measurement table entries with IDs in this list
                results = (
                    slave_store.session.query(slave_table)
                    .filter(slave_table.source_id.in_(datafile_ids_chunk))
                    .options(undefer("*"))
                    .all()
                )

                # Convert the rows to a list of dicts, taking into account
                # the location field, and the properties used in the table classes
                dict_results = rows_to_list_of_dicts(results)

                to_add.extend(dict_results)

            master_store.session.bulk_insert_mappings(master_table, to_add)


def merge_all_measurement_tables(master_store, slave_store, added_datafile_ids):
    master_store.setup_table_type_mapping()
    measurement_table_objects = master_store.meta_classes[TableTypes.MEASUREMENT]

    measurement_table_names = [obj.__name__ for obj in measurement_table_objects]

    for measurement_table_name in measurement_table_names:
        merge_measurement_table(
            measurement_table_name, master_store, slave_store, added_datafile_ids
        )


def table_name_to_class_name(table_name):
    if table_name.endswith("ies"):
        return table_name[:-3] + "y"
    elif table_name.endswith("s"):
        return table_name[:-1]


def prepare_merge_logs(master_store, slave_store):
    # Get references to the table from the master and slave DataStores
    master_table = master_store.db_classes.Log
    slave_table = slave_store.db_classes.Log

    # Keep track of logs that need to be added to master
    logs_to_add = []
    # Keep track of unique change IDs that need to be copied across
    changes_to_add = set()

    with slave_store.session_scope():
        with master_store.session_scope():
            # Get all entries in this table in the slave database
            slave_entries = slave_store.session.query(slave_table).options(undefer("*")).all()

            for slave_entry in slave_entries:
                print(f"Slave entry: {slave_entry}")
                guid = slave_entry.log_id

                # Find all entries with this GUID in the same table in the master database
                results = (
                    master_store.session.query(master_table)
                    .filter(master_table.log_id == guid)
                    .all()
                )

                n_results = len(results)

                if n_results == 0:
                    # The GUID isn't present in the master database
                    # We now need to check whether the Log entry refers to an entry that actually exists in the master
                    # database (as we've done all other copying by now)
                    print(" - Log GUID not present in master db")

                    class_name = table_name_to_class_name(slave_entry.table)

                    referenced_table = getattr(master_store.db_classes, class_name)
                    pri_key_field = referenced_table.__table__.primary_key.columns.values()[0].name
                    referenced_table_pri_key = getattr(referenced_table, pri_key_field)
                    id_to_match = slave_entry.id
                    query = master_store.session.query(referenced_table).filter(
                        referenced_table_pri_key == id_to_match
                    )
                    # breakpoint()
                    id_results = query.all()

                    if len(id_results) == 1:
                        # The Log's id entry DOES refer to something that exists in master
                        # Therefore put it in a list to be copied over
                        print(" - Log ID matches in referred table, adding to list to copy")
                        logs_to_add.append(slave_entry.log_id)

                        changes_to_add.add(slave_entry.change_id)
                elif n_results == 1:
                    # The GUID is in the master db - so the record must also be there (as GUIDs are unique)
                    print(" - Already in master DB with same GUID, don't need to copy")
                else:
                    # We should never get here: the GUID should always appear in the master database either zero or one times,
                    # never more
                    assert False

    return logs_to_add, changes_to_add


def add_changes(master_store, slave_store, changes_to_add):
    to_add = []

    with slave_store.session_scope():
        with master_store.session_scope():
            # Split the IDs list up into 100 at a time, as otherwise the SQL query could get longer
            # than SQLite or Postgres allows - as it'll have a full UUID string in it for each
            # change ID
            for change_ids_chunk in split_list(list(changes_to_add)):
                # Search for all slave Change entries with IDs in this list
                results = (
                    slave_store.session.query(slave_store.db_classes.Change)
                    .filter(slave_store.db_classes.Change.change_id.in_(change_ids_chunk))
                    .options(undefer("*"))
                    .all()
                )

                # Convert the rows to a list of dicts
                dict_results = rows_to_list_of_dicts(results)

                to_add.extend(dict_results)

            master_store.session.bulk_insert_mappings(master_store.db_classes.Change, to_add)


def add_logs(master_store, slave_store, logs_to_add):
    to_add = []

    with slave_store.session_scope():
        with master_store.session_scope():
            # Split the IDs list up into 100 at a time, as otherwise the SQL query could get longer
            # than SQLite or Postgres allows - as it'll have a full UUID string in it for each
            # change ID
            for log_ids_chunk in split_list(logs_to_add):
                # Search for all slave Change entries with IDs in this list
                results = (
                    slave_store.session.query(slave_store.db_classes.Log)
                    .filter(slave_store.db_classes.Log.log_id.in_(log_ids_chunk))
                    .options(undefer("*"))
                    .all()
                )

                # Convert the rows to a list of dicts
                dict_results = rows_to_list_of_dicts(results)

                to_add.extend(dict_results)

            master_store.session.bulk_insert_mappings(master_store.db_classes.Log, to_add)


def merge_logs_and_changes(master_store, slave_store):
    # Prepare to merge the logs by working out which ones need
    # adding, and which changes need adding
    logs_to_add, changes_to_add = prepare_merge_logs(master_store, slave_store)

    # Add the change entries
    add_changes(master_store, slave_store, changes_to_add)

    # Add the log entries
    add_logs(master_store, slave_store, logs_to_add)


def merge_all_tables(master_store, slave_store):
    # TODO: Add database name to this change ID
    with master_store.session_scope():
        merge_change_id = master_store.add_to_changes(
            user=getuser(),
            modified=datetime.utcnow(),
            reason=f"Merging from database {slave_store.db_name}",
        ).change_id

    # Merge the reference tables first
    merge_all_reference_tables(master_store, slave_store)

    # Merge all the metadata tables, excluding the complicated ones
    merge_all_metadata_tables(master_store, slave_store, merge_change_id)

    # Merge the synonyms table now we've merged all the reference and metadata tables
    merge_metadata_table("Synonym", master_store, slave_store, merge_change_id)

    # Merge the Datafiles table, keeping track of the IDs that changed
    datafile_ids = merge_metadata_table("Datafile", master_store, slave_store, merge_change_id)

    # Merge the measurement tables, only merging measurements that come from one of the datafiles that has been added
    merge_all_measurement_tables(master_store, slave_store, datafile_ids["added"])

    # Merge the Logs and Changes table, only merging ones which still match something in the new db
    merge_logs_and_changes(master_store, slave_store)
