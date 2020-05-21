from sqlalchemy.orm import undefer
from sqlalchemy.orm.session import make_transient


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
