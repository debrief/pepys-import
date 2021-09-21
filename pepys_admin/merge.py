from datetime import datetime
from getpass import getuser

from geoalchemy2.shape import to_shape
from sqlalchemy.orm import undefer
from sqlalchemy.orm.session import make_transient
from tabulate import tabulate
from tqdm import tqdm

from pepys_admin.utils import (
    create_statistics_from_ids,
    get_name_for_obj,
    make_query_for_unique_cols_or_all,
    print_names_added,
    statistics_to_table_data,
)
from pepys_import.core.formats.location import Location
from pepys_import.core.store.db_status import TableTypes
from pepys_import.utils.sqlalchemy_utils import get_primary_key_for_table
from pepys_import.utils.table_name_utils import table_name_to_class_name


class MergeDatabases:
    def __init__(self, master_store, slave_store):
        self.master_store = master_store
        self.slave_store = slave_store
        self.ref_statistics = dict()
        self.meta_statistics = dict()
        self.measurement_statistics = dict()
        self.merge_change_id = None

    def merge_all_reference_tables(self):
        """Merges all reference tables from the slave_store into the master_store."""
        self.master_store.setup_table_type_mapping()
        reference_table_objects = self.master_store.meta_classes[TableTypes.REFERENCE]

        reference_table_names = [obj.__name__ for obj in reference_table_objects]

        # Put the GeometryType table at the front of the list, so that it gets
        # done first - as GeometrySubType depends on it
        reference_table_names.remove("GeometryType")
        reference_table_names.insert(0, "GeometryType")

        added_names = {}

        print("Merging reference tables")
        for ref_table in tqdm(reference_table_names):
            id_results = self.merge_reference_table(ref_table)
            self.update_synonyms_table(id_results["modified"])
            self.update_logs_table(id_results["modified"])

            self.ref_statistics[ref_table] = create_statistics_from_ids(id_results)
            if len(id_results["added"]) > 0:
                added_names[ref_table] = [d["name"] for d in id_results["added"]]

        return added_names

    def merge_reference_table(self, table_object_name):
        """Merges a reference table (table_object_name should be the singular name of the table object, such as
        PlatformType) from the slave_store into the master_store.
        """
        # Until we added the HelpText table, all the reference tables had a name field
        # but the HelpText table has an id field instead (but it is unique and has the same
        # characteristics as a name field)
        if table_object_name == "HelpText":
            name_field = "id"
        else:
            name_field = "name"
        # Get references to the table from the master and slave DataStores
        master_table = getattr(self.master_store.db_classes, table_object_name)
        slave_table = getattr(self.slave_store.db_classes, table_object_name)

        primary_key = get_primary_key_for_table(master_table)

        # Keep track of each ID and what its status is
        ids_already_there = []
        ids_added = []
        ids_modified = []

        with self.slave_store.session_scope():
            with self.master_store.session_scope():
                slave_entries = (
                    self.slave_store.session.query(slave_table).options(undefer("*")).all()
                )

                for slave_entry in slave_entries:
                    guid = getattr(slave_entry, primary_key)

                    results = (
                        self.master_store.session.query(master_table)
                        .filter(getattr(master_table, primary_key) == guid)
                        .all()
                    )

                    n_results = len(results)

                    if n_results == 0:
                        search_by_name_results = (
                            self.master_store.session.query(master_table)
                            .filter(
                                getattr(master_table, name_field)
                                == getattr(slave_entry, name_field)
                            )
                            .all()
                        )
                        n_name_results = len(search_by_name_results)

                        if n_name_results == 0:
                            ids_added.append({"id": guid, "name": getattr(slave_entry, name_field)})
                            self.slave_store.session.expunge(slave_entry)
                            make_transient(slave_entry)
                            self.master_store.session.merge(slave_entry)
                        elif n_name_results == 1:
                            ids_modified.append(
                                {
                                    "from": guid,
                                    "to": getattr(search_by_name_results[0], primary_key),
                                    "name": getattr(slave_entry, name_field),
                                    # Data can never be changed here, because there's only one field (name) and that's what we search by
                                    "data_changed": False,
                                }
                            )
                            setattr(
                                slave_entry,
                                primary_key,
                                getattr(search_by_name_results[0], primary_key),
                            )
                            self.slave_store.session.add(slave_entry)
                            self.slave_store.session.commit()
                        else:  # pragma: no cover
                            assert (
                                False
                            ), "Fatal assertion error: multiple entries in master reference table with same name"
                    elif n_results == 1:
                        ids_already_there.append(
                            {"id": guid, "name": getattr(slave_entry, name_field)}
                        )
                    else:  # pragma: no cover
                        assert (
                            False
                        ), "Fatal assertion error: multiple entries in master reference table with same GUID"

        return {
            "already_there": ids_already_there,
            "added": ids_added,
            "modified": ids_modified,
        }

    def merge_all_metadata_tables(self):
        """Merge *most* metadata tables from the slave_store into the master_store, using the merge_change_id
        as the change_id for any modifications occuring as part of the merge.

        Note: this does not merge the Datafile, Synonym, Log or Change tables - these are handled separately.
        """
        self.master_store.setup_table_type_mapping()
        metadata_table_objects = self.master_store.meta_classes[TableTypes.METADATA]

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
        metadata_table_names.remove("Extraction")

        added_names = {}

        print("Merging metadata tables")
        for met_table in tqdm(metadata_table_names):
            id_results = self.merge_metadata_table(met_table)
            self.update_synonyms_table(id_results["modified"])
            self.update_logs_table(id_results["modified"])

            self.meta_statistics[met_table] = create_statistics_from_ids(id_results)
            if len(id_results["added"]) > 0:
                added_names[met_table] = [d["name"] for d in id_results["added"]]

        return added_names

    def update_master_from_slave_entry(self, master_entry, slave_entry):
        """Updates the entry in master with any fields that are set on slave but not on master
        (ie. optional fields like trigraph that may be left blank), or if the slave privacy
        is higher (ie. more secure) than in the entry on master.

        Returns True if the entry has been modified.
        """
        column_names = [col.name for col in master_entry.__table__.columns.values()]

        primary_key = get_primary_key_for_table(master_entry)

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
                    self.master_store.add_to_logs(
                        table=master_entry.__table__.name,
                        row_id=getattr(master_entry, primary_key),
                        field=col_name,
                        change_id=self.merge_change_id,
                    )
                    # Note that we modified it, so we can update in DB if necessary
                    modified = True

        if hasattr(master_entry, "privacy"):
            master_privacy = master_entry.privacy.level
            slave_privacy = slave_entry.privacy.level

            # If master privacy has a level less than the slave privacy, then update with the slave privacy
            if master_privacy < slave_privacy:
                master_entry.privacy_id = slave_entry.privacy_id
                modified = True

        if modified:
            self.master_store.session.add(master_entry)
            self.master_store.session.commit()

        return modified

    def merge_metadata_table(self, table_object_name):
        """Merge the specified metadata table (table_object_name should be the singular name for the table,
        such as "Platform") from the slave_store into the master_store. Use the given change_id for any
        modifications that occur because of the merge (these modifications would happen if an optional value
        is set on the slave but not on the master, and it is therefore copied across).
        """
        # Get references to the table from the master and slave DataStores
        master_table = getattr(self.master_store.db_classes, table_object_name)
        slave_table = getattr(self.slave_store.db_classes, table_object_name)

        primary_key = get_primary_key_for_table(master_table)

        # Keep track of each ID and what its status is
        ids_already_there = []
        ids_added = []
        ids_modified = []

        with self.slave_store.session_scope():
            with self.master_store.session_scope():
                # Get all entries in this table in the slave database
                slave_entries = (
                    self.slave_store.session.query(slave_table).options(undefer("*")).all()
                )

                for slave_entry in slave_entries:
                    guid = getattr(slave_entry, primary_key)

                    # Find all entries with this GUID in the same table in the master database
                    results = (
                        self.master_store.session.query(master_table)
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
                        search_by_all_fields_results = make_query_for_unique_cols_or_all(
                            master_table, slave_entry, self.master_store.session
                        ).all()
                        n_all_field_results = len(search_by_all_fields_results)

                        if n_all_field_results == 0:
                            # We can't find an entry which matches in the master db,
                            # so this is a new entry from the slave which needs copying over
                            ids_added.append({"id": guid, "name": get_name_for_obj(slave_entry)})
                            self.slave_store.session.expunge(slave_entry)
                            make_transient(slave_entry)
                            self.master_store.session.merge(slave_entry)
                        elif n_all_field_results == 1:
                            # We found an entry that matches in the master db, but it'll have a different
                            # GUID - so update the GUID in the slave database and let it propagate
                            # so we can copy over other tables later and
                            # all the foreign key integrity will work
                            setattr(
                                slave_entry,
                                primary_key,
                                getattr(search_by_all_fields_results[0], primary_key),
                            )
                            self.slave_store.session.add(slave_entry)
                            self.slave_store.session.commit()

                            # We also need to compare the fields of the slave entry and the master entry
                            # and update any master fields that are currently None with values from the slave entry
                            was_modified = self.update_master_from_slave_entry(
                                search_by_all_fields_results[0],
                                slave_entry,
                            )

                            ids_modified.append(
                                {
                                    "from": guid,
                                    "to": getattr(search_by_all_fields_results[0], primary_key),
                                    "name": get_name_for_obj(slave_entry),
                                    "data_changed": was_modified,
                                }
                            )
                        else:  # pragma: no cover
                            assert (
                                False
                            ), "Fatal assertion error: multiple entries in master metadata table with same name"
                    elif n_results == 1:
                        # The GUID is in the master db - so the record must also be there(as GUIDs are unique)
                        ids_already_there.append(
                            {"id": guid, "name": get_name_for_obj(slave_entry)}
                        )
                    else:  # pragma: no cover
                        # We should never get here: the GUID should always appear in the master database
                        # either zero or one times, never more
                        assert (
                            False
                        ), "Fatal assertion error: multiple entries in master metadata table with same GUID"

        return {
            "already_there": ids_already_there,
            "added": ids_added,
            "modified": ids_modified,
        }

    def update_synonyms_table(self, modified_ids):
        """Updates the Synonyms table in the slave_store for entries which have had their GUID modified
        when they were merged with the master_store.

        This occurs in the situation where there are entries in both master_store and slave_store with
        the same details, and therefore the slave GUID for that entry is updated to match the master GUID.
        A list of information about those entries is passed to this function, and their original IDs
        ('from_id') are searched in the Synonyms table and updated (to 'to_id') if found.
        """
        with self.slave_store.session_scope():
            # For each modified ID
            for details in modified_ids:
                from_id = details["from"]
                to_id = details["to"]
                # Search for it in the Synonyms table
                results = (
                    self.slave_store.session.query(self.slave_store.db_classes.Synonym)
                    .filter(self.slave_store.db_classes.Synonym.entity == from_id)
                    .all()
                )

                if len(results) > 0:
                    # If it exists, then modify the old ID to the new ID
                    for result in results:
                        result.entity = to_id

                # Commit changes
                self.slave_store.session.add_all(results)
                self.slave_store.session.commit()

    def update_logs_table(self, modified_ids):
        """Updates the Logs table in the slave_store for entries which have had their GUID modified
        when they were merged with the master_store.

        This occurs in the situation where there are entries in both master_store and slave_store with
        the same details, and therefore the slave GUID for that entry is updated to match the master GUID.
        A list of information about those entries is passed to this function, and their original IDs
        ('from_id') are searched in the Logs table and updated (to 'to_id') if found.
        """
        with self.slave_store.session_scope():
            # For each modified ID
            for details in modified_ids:
                from_id = details["from"]
                to_id = details["to"]

                # Search for it in the Logs table
                results = (
                    self.slave_store.session.query(self.slave_store.db_classes.Log)
                    .filter(self.slave_store.db_classes.Log.id == from_id)
                    .all()
                )

                if len(results) > 0:
                    # If it exists, then modify the old ID to the new ID
                    for result in results:
                        result.id = to_id

                # Commit changes
                self.slave_store.session.add_all(results)
                self.slave_store.session.commit()

    @staticmethod
    def split_list(lst, n=100):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i : i + n]

    @staticmethod
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

        Note: This will currently fail for any table with a generic geometry field in it
        (ie. the geometry1 table), but this is not used currently.
        """
        dict_results = []
        attributes_to_use = None
        for row in results:
            if attributes_to_use is None:
                attributes_to_use = [attrib for attrib in dir(row) if not attrib.startswith("__")]
                attributes_to_remove = [
                    "_decl_class_registry",
                    "_sa_class_manager",
                    "_sa_instance_state",
                ]
                for attribute_name in attributes_to_remove:
                    if attribute_name in attributes_to_use:
                        attributes_to_use.remove(attribute_name)

            d = {key: getattr(row, key) for key in attributes_to_use}

            # Deal with the location field, making sure it gets converted to WKT so it can be inserted
            # into the db
            if "location" in d and d["location"] is not None:
                d["_location"] = d["location"].to_wkt()

            # Deal with the geometry table where we have a generic geometry in the table
            # If it is a Location object then convert to WKT. If not then, convert the
            # WKB geometry field to a WKT field, going via Shapely
            if "geometry" in d:
                if isinstance(d["geometry"], Location):
                    d["_geometry"] = d["geometry"].to_wkt()
                else:
                    shply_geom = to_shape(d["geometry"])
                    d["_geometry"] = "SRID=4326;" + shply_geom.wkt

            dict_results.append(d)

        return dict_results

    def merge_measurement_table(self, table_object_name, added_datafile_ids):
        """Merge the specified metadata table (specified as the object name, so singular) from the slave_store
        into the master_store, copying across entries which have a source_id in added_datafile_ids.
        """
        # We don't need to do a 'merge' as such for the measurement tables. Instead we just need to add
        # the measurement entries for datafiles which hadn't already been imported into the master
        # database.
        # These come from the 'added' list of IDs from the datafile merging function and are
        # passed to this function

        master_table = getattr(self.master_store.db_classes, table_object_name)
        slave_table = getattr(self.slave_store.db_classes, table_object_name)

        to_add = []

        with self.slave_store.session_scope():
            with self.master_store.session_scope():
                # Split the IDs list up into 100 at a time, as otherwise the SQL query could get longer
                # than SQLite or Postgres allows - as it'll have a full UUID string in it for each
                # datafile ID
                print(f"Merging measurement table {table_object_name}")
                for datafile_ids_chunk in tqdm(self.split_list(added_datafile_ids)):
                    # Search for all slave measurement table entries with IDs in this list
                    results = (
                        self.slave_store.session.query(slave_table)
                        .filter(slave_table.source_id.in_(datafile_ids_chunk))
                        .options(undefer("*"))
                        .all()
                    )

                    # Convert the rows to a list of dicts, taking into account
                    # the location field, and the properties used in the table classes
                    dict_results = self.rows_to_list_of_dicts(results)

                    to_add.extend(dict_results)

                self.master_store.session.bulk_insert_mappings(master_table, to_add)

        return len(to_add)

    def merge_all_measurement_tables(self, added_datafile_ids):
        """Copies across all entries in all measurement tables that have a source_id in the list of
        added_datafile_ids.

        Must be run *after* reference and metadata tables have been merged.
        """
        self.master_store.setup_table_type_mapping()
        measurement_table_objects = self.master_store.meta_classes[TableTypes.MEASUREMENT]

        measurement_table_names = [obj.__name__ for obj in measurement_table_objects]

        n_added = {}

        print("Merging measurement tables")
        for measurement_table_name in tqdm(measurement_table_names):
            n_added[measurement_table_name] = self.merge_measurement_table(
                measurement_table_name, added_datafile_ids
            )

        return n_added

    def prepare_merge_logs(self):
        """Works out which Log and Change entries need copying from the slave_store to the master_store,
        by checking which entries refer to something that is actually in the master database.

        Must be run *after* all other merging is complete.
        """
        # Get references to the table from the master and slave DataStores
        master_table = self.master_store.db_classes.Log
        slave_table = self.slave_store.db_classes.Log

        # Keep track of logs that need to be added to master
        logs_to_add = []
        # Keep track of unique change IDs that need to be copied across
        changes_to_add = set()

        with self.slave_store.session_scope():
            with self.master_store.session_scope():
                # Get all entries in this table in the slave database
                slave_entries = (
                    self.slave_store.session.query(slave_table).options(undefer("*")).all()
                )

                print("Preparing to merge Logs and Changes")
                for slave_entry in tqdm(slave_entries):
                    guid = slave_entry.log_id

                    # Find all entries with this GUID in the same table in the master database
                    results = (
                        self.master_store.session.query(master_table)
                        .filter(master_table.log_id == guid)
                        .all()
                    )

                    n_results = len(results)

                    if n_results == 0:
                        # The GUID isn't present in the master database
                        # We now need to check whether the Log entry refers to an entry that actually exists
                        # in the master database (as we've done all other copying by now)

                        class_name = table_name_to_class_name(slave_entry.table)

                        referenced_table = getattr(self.master_store.db_classes, class_name)
                        pri_key_field = get_primary_key_for_table(referenced_table)
                        referenced_table_pri_key = getattr(referenced_table, pri_key_field)
                        id_to_match = slave_entry.id
                        query = self.master_store.session.query(referenced_table).filter(
                            referenced_table_pri_key == id_to_match
                        )
                        id_results = query.all()

                        if len(id_results) == 1:
                            # The Log's id entry DOES refer to something that exists in master
                            # Therefore put it in a list to be copied over
                            logs_to_add.append(slave_entry.log_id)

                            changes_to_add.add(slave_entry.change_id)
                    elif n_results == 1:
                        # The GUID is in the master db - so the record must also be there
                        # (as GUIDs are unique)
                        pass
                    else:  # pragma: no cover
                        # We should never get here: the GUID should always appear in the master database
                        # either zero or one times, never more
                        assert (
                            False
                        ), "Fatal assertion error: multiple entries in master Logs table with same GUID"

        return logs_to_add, changes_to_add

    def add_changes(self, changes_to_add):
        """Copies the Change entries with the specified ids in changes_to_add from the slave_store to
        the master_store.
        """
        to_add = []

        with self.slave_store.session_scope():
            with self.master_store.session_scope():
                # Split the IDs list up into 100 at a time, as otherwise the SQL query could get longer
                # than SQLite or Postgres allows - as it'll have a full UUID string in it for each
                # change ID
                print("Merging Changes")
                for change_ids_chunk in tqdm(self.split_list(list(changes_to_add))):
                    # Search for all slave Change entries with IDs in this list
                    results = (
                        self.slave_store.session.query(self.slave_store.db_classes.Change)
                        .filter(self.slave_store.db_classes.Change.change_id.in_(change_ids_chunk))
                        .options(undefer("*"))
                        .all()
                    )

                    # Convert the rows to a list of dicts
                    dict_results = self.rows_to_list_of_dicts(results)

                    to_add.extend(dict_results)

                self.master_store.session.bulk_insert_mappings(
                    self.master_store.db_classes.Change, to_add
                )

    def add_logs(self, logs_to_add):
        """Copies the Log entries with the specified ids in logs_to_add from the slave_store to
        the master_store.
        """
        to_add = []

        with self.slave_store.session_scope():
            with self.master_store.session_scope():
                # Split the IDs list up into 100 at a time, as otherwise the SQL query could get longer
                # than SQLite or Postgres allows - as it'll have a full UUID string in it for each
                # change ID
                print("Merging Logs")
                for log_ids_chunk in tqdm(self.split_list(logs_to_add)):
                    # Search for all slave Change entries with IDs in this list
                    results = (
                        self.slave_store.session.query(self.slave_store.db_classes.Log)
                        .filter(self.slave_store.db_classes.Log.log_id.in_(log_ids_chunk))
                        .options(undefer("*"))
                        .all()
                    )

                    # Convert the rows to a list of dicts
                    dict_results = self.rows_to_list_of_dicts(results)

                    to_add.extend(dict_results)

                self.master_store.session.bulk_insert_mappings(
                    self.master_store.db_classes.Log, to_add
                )

    def merge_logs_and_changes(self):
        """Merges the Logs and Changes tables from the slave_store into the master_store.

        Must be run *after* all other merging is complete.
        """
        # Prepare to merge the logs by working out which ones need
        # adding, and which changes need adding
        logs_to_add, changes_to_add = self.prepare_merge_logs()

        # Add the change entries
        self.add_changes(changes_to_add)

        # Add the log entries
        self.add_logs(logs_to_add)

    def merge_extractions(self, added_datafile_ids):
        to_add = []

        with self.slave_store.session_scope():
            with self.master_store.session_scope():
                print("Merging Extractions")
                for datafile_ids_chunk in tqdm(self.split_list(added_datafile_ids)):
                    # Search for all slave Extraction entries with IDs in this list
                    results = (
                        self.slave_store.session.query(self.slave_store.db_classes.Extraction)
                        .filter(
                            self.slave_store.db_classes.Extraction.datafile_id.in_(
                                datafile_ids_chunk
                            )
                        )
                        .options(undefer("*"))
                        .all()
                    )

                    # Convert the rows to a list of dicts
                    dict_results = self.rows_to_list_of_dicts(results)

                    to_add.extend(dict_results)

                self.master_store.session.bulk_insert_mappings(
                    self.master_store.db_classes.Extraction, to_add
                )

    def merge_all_tables(self):
        """
        Does a full merge, taking all data from the slave_store database and merging it into the master_store
        database. At the end of merging, print some summary tables with merge statistics and lists of
        new objects added.

        Both master_store and data_store can be connected to either Postgres or SQLite databases.

        The overall outline of the merge is that we first merge the reference tables and most of the metadata
        tables, then merge the Synonyms and Datafiles tables, then copy across the relevant entries from the
        measurement tables, before finally filtering and copying the Logs and Changes tables.

        In general, "merging" here means comparing the two databases and dealing with these specific situations:
          a) The exact same entry exists in both databases, with the same GUID.
          This will occur when this entry was exported from the master database to the slave database.
          This is counted as 'already present', and nothing is done to change it.

          b) An entry exists in the slave database which isn't present in the master database
          This will occur when the entry is added to the slave database after the two databases have been
          separated This entry will be added to the master database, and counted as an item 'added'.

          c) An entry exists in the slave database with the same details as in the master database, but with
          a different GUID. The details that are compared to see if the entry is the same are the name field
          for a reference table, the fields defined in a unique constraint for any other table (eg. `name` and
          `host` for Sensors) or all fields if a unique constraint isn't defined. If optional fields are present
           in the slave database that are not present in the entry in the master database, then these are
           copied across. If the privacy value in the slave database  is higher (ie. more secure) than the
           entry in the master database, then the privacy is updated to match the slave value. This entry
           counts as a 'modified' entry, as the GUID in the slave database is modified to match the GUID in
           the master, so that other objects can be copied without failing foreign key integrity checks.
           This does NOT mean that the data for the entry has been modified - this is only the case if the
           `data_changed` field is set to True in the resulting list of ids.

        The measurement tables (States, Contacts etc) aren't merged as such: new entries are just copied
        across. This is done based on the entries in the Datafiles table: we keep track of the IDs of all
        datafile entries that are added to the master from the slave, and then just copy the measurement data
        that has come from those datafiles.

        Logs and Changes are merged at the end, so that we can check each Log entry to see if it refers to
        something that actually exists in the master database, and only copy it if it does.

        The results from the merge_all_* functions consist of:

         - A list of 'added names': a dictionary with keys for each table merged, and values of a list of all
          the new 'names' that have been added (the 'name' is either the name field, if it exists, or the
          'reference' or 'synonym' field if it doesn't.)
         - A list of statistics: a dictionary with keys for each table merged, and values of a dictionary
         with counts of items 'already there', 'modified' and 'added'.
        """
        # Create a Change for this merge
        with self.master_store.session_scope():
            self.merge_change_id = self.master_store.add_to_changes(
                user=getuser(),
                modified=datetime.utcnow(),
                reason=f"Merging from database {self.slave_store.db_name}",
            ).change_id

        # Merge the reference tables first
        ref_added_names = self.merge_all_reference_tables()

        # Merge all the metadata tables, excluding the complicated ones
        meta_added_names = self.merge_all_metadata_tables()

        # Merge the synonyms table now we've merged all the reference and metadata tables
        syn_ids = self.merge_metadata_table("Synonym")
        # Get the list of added names, and add the statistics to the meta_statistics list
        syn_added_names = [d["name"] for d in syn_ids["added"]]
        self.meta_statistics["Synonyms"] = create_statistics_from_ids(syn_ids)

        # Merge the Datafiles table, keeping track of the IDs that changed
        df_ids = self.merge_metadata_table("Datafile")
        # Get the list of added names, and add the statistics to the meta_statistics list
        df_added_names = [d["name"] for d in df_ids["added"]]
        self.meta_statistics["Datafiles"] = create_statistics_from_ids(df_ids)

        # Merge the measurement tables, only merging measurements that come from one of the datafiles that
        # has been added
        self.measurement_statistics = self.merge_all_measurement_tables(
            [d["id"] for d in df_ids["added"]]
        )

        # Merge the Logs and Changes table, only merging ones which still match something in the new db
        self.merge_logs_and_changes()

        # Merge the Extractions table, only merging those that match a Datafile that has been added
        self.merge_extractions([d["id"] for d in df_ids["added"]])

        print("Statistics:\n")
        print("Reference tables:")
        print(
            tabulate(
                statistics_to_table_data(self.ref_statistics),
                headers=["Table", "Already present", "Added", "Modified"],
                tablefmt="grid",
            )
        )

        print("\nMetadata tables:")
        print(
            tabulate(
                statistics_to_table_data(self.meta_statistics),
                headers=["Table", "Already present", "Added", "Modified"],
                tablefmt="grid",
            )
        )

        print("\nMeasurement tables:")
        print(
            tabulate(
                list(self.measurement_statistics.items()),
                headers=["Table", "Added"],
                tablefmt="grid",
            )
        )

        all_added_names = {**ref_added_names, **meta_added_names}
        if len(syn_added_names) > 0:
            all_added_names["Synonyms"] = syn_added_names
        if len(df_added_names) > 0:
            all_added_names["Datafiles"] = df_added_names

        print_names_added(all_added_names)
