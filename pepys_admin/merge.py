from sqlalchemy.orm import undefer
from sqlalchemy.orm.session import make_transient

from pepys_admin.utils import make_query_for_all_data_columns
from pepys_import.core.store.db_status import TableTypes


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
        merge_reference_table(ref_table, master_store, slave_store)


def merge_reference_table(table_object_name, master_store, slave_store):
    # Get references to the table from the master and slave DataStores
    master_table = getattr(master_store.db_classes, table_object_name)
    slave_table = getattr(slave_store.db_classes, table_object_name)

    primary_key = master_table.__table__.primary_key.columns.values()[0].name

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
                        make_transient(slave_entry)
                        master_store.session.add(slave_entry)
                    elif n_name_results == 1:
                        print("  - In master db, making GUIDs match and cascading")
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
                else:
                    assert False


def merge_all_metadata_tables(master_store, slave_store):
    master_store.setup_table_type_mapping()
    metadata_table_objects = master_store.meta_classes[TableTypes.METADATA]

    metadata_table_names = [obj.__name__ for obj in metadata_table_objects]

    # Crude ordering system for now (TODO: Improve)
    # Put Platform first, then Sensor, then rest of them
    metadata_table_names.remove("Platform")
    metadata_table_names.remove("Sensor")
    metadata_table_names.insert(0, "Sensor")
    metadata_table_names.insert(0, "Platform")

    # Remove Log and Change entries for now - deal with those separately later
    metadata_table_names.remove("Log")
    metadata_table_names.remove("Change")

    for ref_table in metadata_table_names:
        merge_metadata_table(ref_table, master_store, slave_store)


def merge_metadata_table(table_object_name, master_store, slave_store):
    # Get references to the table from the master and slave DataStores
    master_table = getattr(master_store.db_classes, table_object_name)
    slave_table = getattr(slave_store.db_classes, table_object_name)

    primary_key = master_table.__table__.primary_key.columns.values()[0].name

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
                    search_by_all_fields_results = make_query_for_all_data_columns(
                        master_table, slave_entry, master_store.session
                    ).all()
                    # breakpoint()
                    n_all_field_results = len(search_by_all_fields_results)

                    if n_all_field_results == 0:
                        # We can't find an entry which matches in the master db,
                        # so this is a new entry from the slave which needs copying over
                        print("  - Not in master db, copying over")
                        slave_store.session.expunge(slave_entry)
                        make_transient(slave_entry)
                        master_store.session.merge(slave_entry)
                    elif n_all_field_results == 1:
                        # We found an entry that matches in the master db, but it'll have a different
                        # GUID - so update the GUID in the slave database and let it propagate
                        # so we can copy over other tables later and all the foreign key integrity will work
                        print("  - In master db, making GUIDs match and cascading")
                        setattr(
                            slave_entry,
                            primary_key,
                            getattr(search_by_all_fields_results[0], primary_key),
                        )
                        slave_store.session.add(slave_entry)
                        slave_store.session.commit()
                    else:
                        assert False
                elif n_results == 1:
                    # The GUID is in the master db - so the record must also be there (as GUIDs are unique)
                    print(" - Already in master DB with same GUID, don't need to copy")
                else:
                    # We should never get here: the GUID should always appear in the master database either zero or one times,
                    # never more
                    assert False
