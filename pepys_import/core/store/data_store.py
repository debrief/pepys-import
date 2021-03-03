import os
import sys
import uuid
from contextlib import contextmanager
from datetime import datetime
from getpass import getuser
from importlib import import_module

import sqlalchemy
from sqlalchemy import create_engine, inspect
from sqlalchemy.event import listen
from sqlalchemy.exc import ArgumentError, OperationalError
from sqlalchemy.orm import scoped_session, sessionmaker, undefer
from sqlalchemy.sql import func
from sqlalchemy_utils import dependent_objects, merge_references

from paths import PEPYS_IMPORT_DIRECTORY
from pepys_import import __version__
from pepys_import.core.formats import unit_registry
from pepys_import.core.store import constants
from pepys_import.resolvers.default_resolver import DefaultResolver
from pepys_import.utils.branding_util import show_software_meta_info, show_welcome_banner
from pepys_import.utils.data_store_utils import (
    MissingDataException,
    cache_results_if_not_none,
    create_alembic_version_table,
    create_spatial_tables_for_postgres,
    create_spatial_tables_for_sqlite,
    import_from_csv,
    lowercase_or_none,
)
from pepys_import.utils.sqlite_utils import load_spatialite, set_sqlite_foreign_keys_on
from pepys_import.utils.value_transforming_utils import format_datetime

from ...utils.error_handling import handle_first_connection_error
from ...utils.sqlalchemy_utils import get_primary_key_for_table
from ...utils.table_name_utils import table_name_to_class_name
from ...utils.text_formatting_utils import custom_print_formatted_text, format_error_message
from .db_base import BasePostGIS, BaseSpatiaLite
from .db_status import TableTypes
from .table_summary import TableSummary, TableSummarySet

DEFAULT_DATA_PATH = os.path.join(PEPYS_IMPORT_DIRECTORY, "database", "default_data")
USER = getuser()  # Login name of the current user


class DataStore:
    """Representation of database

    :returns: :class:`DataStore`
    """

    # Valid options for db_type are 'postgres' and 'sqlite'
    def __init__(
        self,
        db_username,
        db_password,
        db_host,
        db_port,
        db_name,
        db_type,
        missing_data_resolver=DefaultResolver(),
        welcome_text="Pepys_import",
        show_status=True,
    ):
        if db_type == "postgres":
            self.db_classes = import_module("pepys_import.core.store.postgres_db")
            driver = "postgresql+psycopg2"
        elif db_type == "sqlite":
            self.db_classes = import_module("pepys_import.core.store.sqlite_db")
            driver = "sqlite+pysqlite"
        else:
            raise Exception(
                f"Unknown db_type {db_type} supplied, if specified should be "
                "one of 'postgres' or 'sqlite'"
            )

        # setup meta_class data
        self.meta_classes = {}
        self.setup_table_type_mapping()

        if db_name == ":memory:":
            self.in_memory_database = True
        else:
            self.in_memory_database = False

        connection_string = "{}://{}:{}@{}:{}/{}".format(
            driver, db_username, db_password, db_host, db_port, db_name
        )
        try:
            if db_type == "postgres":
                self.engine = create_engine(connection_string, echo=False, executemany_mode="batch")
                BasePostGIS.metadata.bind = self.engine
            elif db_type == "sqlite":
                self.engine = create_engine(connection_string, echo=False)
                listen(self.engine, "connect", load_spatialite)
                listen(self.engine, "connect", set_sqlite_foreign_keys_on)
                BaseSpatiaLite.metadata.bind = self.engine
        except ArgumentError as e:
            custom_print_formatted_text(
                format_error_message(
                    f"SQL Exception details: {e}\n\n"
                    "ERROR: Invalid Connection URL Error!\n"
                    "Please check your config file. There might be missing/wrong values!\n"
                    "See above for the full error from SQLAlchemy."
                )
            )
            sys.exit(1)

        # Try to connect to the engine to check if there is any problem
        with handle_first_connection_error(connection_string):
            inspector = inspect(self.engine)
            _ = inspector.get_table_names()

        self.missing_data_resolver = missing_data_resolver
        self.welcome_text = welcome_text
        self.show_status = show_status

        # TEMP list of values for defaulted IDs, to be replaced by missing info lookup mechanism
        self.default_user_id = 1  # DevUser

        # Instance attributes which are necessary for initialise method
        self.db_name = db_name
        self.db_type = db_type

        # use session_scope() to create a new session
        self.session = None

        # dictionaries, to cache platform name
        self._platform_dict_on_sensor_id = dict()
        self._platform_dict_on_platform_id = dict()

        # dictionary to cache platform object based on name
        self._platform_cache = dict()

        # dictionary to cache sensor based on sensor_name and platform_id
        self._sensor_cache = dict()

        # dictionary to cache datafile based on datafile_name
        self._datafile_cache = dict()

        # dictionaries, to cache sensor name
        self._sensor_dict_on_sensor_id = dict()

        # dictionary, to cache comment type name
        self._comment_type_name_dict_on_comment_type_id = dict()

        self._search_privacy_cache = dict()
        self._search_platform_type_cache = dict()
        self._search_sensor_type_cache = dict()
        self._search_sensor_cache = dict()
        self._search_nationality_cache = dict()
        self._search_datafile_from_id_cache = dict()
        self._search_datafile_cache = dict()
        self._search_datafile_type_cache = dict()
        self._search_geometry_type_cache = dict()
        self._search_geometry_subtype_cache = dict()

        db_session = sessionmaker(bind=self.engine)
        self.scoped_session_creator = scoped_session(db_session)

        # Branding Text
        if self.welcome_text:
            show_welcome_banner(welcome_text)
        if self.show_status:
            show_software_meta_info(__version__, self.db_type, self.db_name, db_host)
            # The 'pepys-import' banner is 61 characters wide, so making a line
            # of the same length makes things prettier
            print("-" * 61)

    def initialise(self):
        """Create schemas for the database"""
        if self.db_type == "sqlite":
            try:
                create_spatial_tables_for_sqlite(self.engine)
                # Attempt to create schema if not present, to cope with fresh DB file
                BaseSpatiaLite.metadata.create_all(self.engine)
            except OperationalError as e:
                print(
                    f"SQL Exception details: {e}\n\n"
                    "ERROR: Database Connection Error! The schema couldn't be created.\n"
                    "Please check your config file. There might be missing/wrong values!\n"
                    "See above for the full error from SQLAlchemy."
                )
                sys.exit(1)
        elif self.db_type == "postgres":
            try:
                create_spatial_tables_for_postgres(self.engine)
                BasePostGIS.metadata.create_all(self.engine)
            except OperationalError as e:
                print(
                    f"SQL Exception details: {e}\n\n"
                    "ERROR: Database Connection Error! The schema couldn't be created.\n"
                    "Please check your config file. There might be missing/wrong values!\n"
                    "See above for the full error from SQLAlchemy."
                )
                sys.exit(1)
        create_alembic_version_table(self.engine, self.db_type)
        if self.show_status:
            print("Database tables were created by DataStore's initialisation.")

    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations."""
        self.session = self.scoped_session_creator()
        try:
            yield self
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        finally:
            self.session.close()

    #############################################################
    # Other DataStore Methods

    def setup_table_type_mapping(self):
        """Setup a map of tables keyed by :class:`TableType`"""
        db_classes = dict(
            [
                (name, cls)
                for name, cls in self.db_classes.__dict__.items()
                if isinstance(cls, type)
                and (issubclass(cls, BasePostGIS) or issubclass(cls, BaseSpatiaLite))
                and cls.__name__ != "Base"
            ]
        )
        for table_type in TableTypes:
            self.meta_classes[table_type] = [
                cls for name, cls in db_classes.items() if db_classes[name].table_type == table_type
            ]

    def populate_reference(self, reference_data_folder=None):
        """Import given CSV file to the given reference table"""
        change = self.add_to_changes(
            user=USER, modified=datetime.utcnow(), reason="Importing reference data"
        )

        if reference_data_folder is None:
            reference_data_folder = os.path.join(DEFAULT_DATA_PATH)

        files = sorted(os.listdir(reference_data_folder))

        reference_tables = []
        # Create reference table list
        self.setup_table_type_mapping()
        reference_table_objects = self.meta_classes[TableTypes.REFERENCE]
        for table_object in list(reference_table_objects):
            reference_tables.append(table_object.__tablename__)

        reference_files = [
            file for file in files if os.path.splitext(file)[0].replace(" ", "") in reference_tables
        ]
        import_from_csv(self, reference_data_folder, reference_files, change.change_id)

    def populate_metadata(self, sample_data_folder=None):
        """Import CSV files from the given folder to the related Metadata Tables"""
        change = self.add_to_changes(
            user=USER, modified=datetime.utcnow(), reason="Importing metadata data"
        )
        if sample_data_folder is None:
            sample_data_folder = os.path.join(DEFAULT_DATA_PATH)

        files = sorted(os.listdir(sample_data_folder))

        metadata_tables = []
        # Create metadata table list
        self.setup_table_type_mapping()
        metadata_table_objects = self.meta_classes[TableTypes.METADATA]
        for table_object in list(metadata_table_objects):
            metadata_tables.append(table_object.__tablename__)

        metadata_files = [file for file in files if os.path.splitext(file)[0] in metadata_tables]
        import_from_csv(self, sample_data_folder, metadata_files, change.change_id)

    # End of Data Store methods
    #############################################################

    def add_to_sensors(
        self,
        name,
        sensor_type,
        host_name,
        host_nationality,
        host_identifier,
        privacy,
        change_id,
        host_id=None,
    ):
        """
        Adds the specified sensor to the :class:`Sensor` table if not already present.

        :param name: Name of sensor
        :type name: String
        :param sensor_type: Type of sensor
        :type sensor_type: String
        :param host_name: Name of Platform that sensor belongs to
        :type host_name: String
        :param host_nationality: Nationality of Platform that sensor belongs to
        :type host_nationality: String
        :param host_identifier: Identifier of Platform that sensor belongs to
        :type host_identifier: String
        :param privacy: :class:`Privacy` of :class:`State`
        :type privacy: String
        :param change_id: ID of the :class:`Change` object
        :type change_id: Integer or UUID
        :param host_id: ID of Platform that sensor belongs to (optional, can be passed instead
                        of host_name, host_nationality and host_identifier)
        :return: Created Sensor entity

        Notes:
        To specify the platform that the added sensor should belong to you can either:
         - Specify the host_name, host_nationality and host_identifier parameters, to uniquely identify the Platform
         - Specify the host_id parameter to give the ID of the Platform, and set host_name, host_nationality and host_identifier to None
        """
        if host_id is not None:
            host = self.search_platform_by_id(host_id)
        else:
            host = self.search_platform(host_name, host_nationality, host_identifier)

        sensor_type = self.search_sensor_type(sensor_type)
        privacy = self.search_privacy(privacy)

        if sensor_type is None:
            raise MissingDataException("Sensor Type is missing/invalid")
        elif host is None:
            raise MissingDataException("Host is missing/invalid")
        elif privacy is None:
            raise MissingDataException("Privacy is missing/invalid")

        # Check if entry already exists with these details, and if so, just return it
        # Just check the unique fields - in this case: name and host
        # TODO: Possibly update when we get final uniqueness info from client
        results = (
            self.session.query(self.db_classes.Sensor)
            .filter(func.lower(self.db_classes.Sensor.name) == lowercase_or_none(name))
            .filter(self.db_classes.Sensor.host == host.platform_id)
            .all()
        )

        if len(results) == 1:
            # Don't add it, as it already exists - just return it
            return results[0]
        elif len(results) > 1:
            assert (
                False
            ), "Fatal error: Duplicate entries found in Sensors table"  # pragma: no cover

        sensor_obj = self.db_classes.Sensor(
            name=name,
            sensor_type_id=sensor_type.sensor_type_id,
            host=host.platform_id,
            privacy_id=privacy.privacy_id,
        )
        self.session.add(sensor_obj)
        self.session.flush()

        self.add_to_logs(table=constants.SENSOR, row_id=sensor_obj.sensor_id, change_id=change_id)
        return sensor_obj

    def add_to_datafiles(
        self,
        privacy,
        file_type,
        reference=None,
        simulated=False,
        file_size=None,
        file_hash=None,
        url=None,
        change_id=None,
    ):
        """
        Adds the specified datafile to the Datafile table if not already present.

        :param simulated: :class:`Datafile` is simulated or not
        :type simulated: Boolean
        :param privacy: :class:`Privacy` of :class:`Datafile`
        :type privacy: Privacy
        :param file_type: Type of :class:`Datafile`
        :type file_type: String
        :param reference: Reference of :class:`Datafile`
        :type reference: String
        :param file_size: Size of the file (in bytes)
        :type file_size: Integer
        :param file_hash: Hashed value of the file
        :type file_hash: String
        :param url: URL of datafile
        :type url: String
        :param change_id: ID of the :class:`Change` object
        :type change_id: Integer or UUID
        :return: Created :class:`Datafile` entity
        :rtype: Datafile
        """
        datafile_type = self.search_datafile_type(file_type)
        privacy = self.search_privacy(privacy)

        if datafile_type is None:
            raise MissingDataException("Datafile Type is invalid/missing")
        elif privacy is None:
            raise MissingDataException("Privacy is invalid/missing")

        # Check if entry already exists with these details, and if so, just return it
        # Just check the unique fields - in this case: size and hash
        # TODO: Possibly update when we get final uniqueness info from client
        results = (
            self.session.query(self.db_classes.Datafile)
            .filter(self.db_classes.Datafile.size == file_size)
            .filter(self.db_classes.Datafile.hash == file_hash)
            .all()
        )

        if len(results) == 1:
            # Don't add it, as it already exists - just return it
            return results[0]
        elif len(results) > 1:
            assert (
                False
            ), "Fatal error: Duplicate entries found in Datafiles table"  # pragma: no cover

        datafile_obj = self.db_classes.Datafile(
            simulated=bool(simulated),
            privacy_id=privacy.privacy_id,
            datafile_type_id=datafile_type.datafile_type_id,
            reference=reference,
            size=file_size,
            hash=file_hash,
            url=url,
        )

        self.session.add(datafile_obj)
        self.session.flush()

        self.add_to_logs(
            table=constants.DATAFILE,
            row_id=datafile_obj.datafile_id,
            change_id=change_id,
        )
        return datafile_obj

    def add_to_platforms(
        self,
        name,
        identifier,
        nationality,
        platform_type,
        privacy,
        trigraph=None,
        quadgraph=None,
        change_id=None,
    ):
        """
        Adds the specified platform to the Platform table if not already present.

        :param name: Name of :class:`Platform`
        :type name: String
        :param nationality: Nationality of :class:`Platform`
        :type nationality: Nationality
        :param platform_type: Type of :class:`Platform`
        :type platform_type: PlatformType
        :param privacy: :class:`Privacy` of :class:`Platform`
        :type privacy: Privacy
        :param trigraph: Trigraph of :class:`Platform`
        :type trigraph: String
        :param quadgraph: Quadgraph of :class:`Platform`
        :type quadgraph: String
        :param identifier: Identifier string of :class:`Platform`
        :type identifier: String
        :param change_id: ID of the :class:`Change` object
        :type change_id: Integer or UUID
        :return: Created Platform entity
        :rtype: Platform
        """
        nationality = self.search_nationality(nationality)
        platform_type = self.search_platform_type(platform_type)
        privacy = self.search_privacy(privacy)

        if nationality is None:
            raise MissingDataException("Nationality is invalid/missing")
        elif platform_type is None:
            raise MissingDataException("Platform Type is invalid/missing")
        elif privacy is None:
            raise MissingDataException("Privacy is invalid/missing")

        # Check if entry already exists with these details, and if so, just return it
        # Just check the unique fields - in this case: name, nationality_id and identifier
        # TODO: Possibly update when we get final uniqueness info from client
        results = (
            self.session.query(self.db_classes.Platform)
            .filter(func.lower(self.db_classes.Platform.name) == lowercase_or_none(name))
            .filter(self.db_classes.Platform.nationality_id == nationality.nationality_id)
            .filter(
                func.lower(self.db_classes.Platform.identifier) == lowercase_or_none(identifier)
            )
            .all()
        )

        if len(results) == 1:
            # Don't add it, as it already exists - just return it
            return results[0]
        elif len(results) > 1:
            assert (
                False
            ), "Fatal error: Duplicate entries found in Platforms table"  # pragma: no cover

        platform_obj = self.db_classes.Platform(
            name=name,
            trigraph=trigraph,
            quadgraph=quadgraph,
            identifier=identifier,
            nationality_id=nationality.nationality_id,
            platform_type_id=platform_type.platform_type_id,
            privacy_id=privacy.privacy_id,
        )

        self.session.add(platform_obj)
        self.session.flush()

        self.add_to_logs(
            table=constants.PLATFORM,
            row_id=platform_obj.platform_id,
            change_id=change_id,
        )
        return platform_obj

    def add_to_synonyms(self, table, name, entity, change_id):
        # Blacklist certain tables, and don't Synonyms for them be created
        if table in [constants.SENSOR, constants.GEOMETRY_SUBTYPE]:
            raise Exception(f"Synonyms are not allowed for table {table}")

        # Check if entry already exists with these details, and if so, just return it
        # Just check the unique fields - in this case: name and table
        # TODO: Possibly update when we get final uniqueness info from client
        results = (
            self.session.query(self.db_classes.Synonym)
            .filter(func.lower(self.db_classes.Synonym.synonym) == lowercase_or_none(name))
            .filter(self.db_classes.Synonym.table == table)
            .all()
        )

        if len(results) == 1:
            # Don't add it, as it already exists - just return it
            return results[0]
        elif len(results) > 1:
            assert (
                False
            ), "Fatal error: Duplicate entries found in Synonyms table"  # pragma: no cover

        # enough info to proceed and create entry
        synonym = self.db_classes.Synonym(table=table, synonym=name, entity=entity)
        self.session.add(synonym)
        self.session.flush()

        self.add_to_logs(table=constants.SYNONYM, row_id=synonym.synonym_id, change_id=change_id)
        return synonym

    #############################################################
    # Search/lookup functions for metadata
    #############################################################
    def search_sensor(self, name, platform_id):
        """Search for any sensor type featuring this name"""
        return (
            self.session.query(self.db_classes.Sensor)
            .filter(func.lower(self.db_classes.Sensor.name) == lowercase_or_none(name))
            .filter(self.db_classes.Sensor.host == platform_id)
            .first()
        )

    @cache_results_if_not_none("_search_datafile_cache")
    def search_datafile(self, name):
        """Search for any datafile with this name"""
        return (
            self.session.query(self.db_classes.Datafile)
            .options(undefer("simulated"))
            .filter(func.lower(self.db_classes.Datafile.reference) == lowercase_or_none(name))
            .first()
        )

    def search_platform(self, name, nationality, identifier):
        """Search for any platform with this name, nationality and identifier"""
        results = (
            self.session.query(self.db_classes.Platform)
            .join(self.db_classes.Nationality)
            .filter(func.lower(self.db_classes.Platform.name) == lowercase_or_none(name))
            .filter(
                func.lower(self.db_classes.Platform.identifier) == lowercase_or_none(identifier)
            )
            .filter(func.lower(self.db_classes.Nationality.name) == lowercase_or_none(nationality))
            .all()
        )

        if len(results) == 1:
            return results[0]
        elif len(results) == 0:
            return None
        else:  # pragma: no cover
            raise Exception(
                "Multiple platforms with the same name, nationality and identifier found"
            )

    def search_platform_by_id(self, platform_id):
        return (
            self.session.query(self.db_classes.Platform)
            .filter(self.db_classes.Platform.platform_id == platform_id)
            .first()
        )

    @cache_results_if_not_none("_search_datafile_from_id_cache")
    def get_datafile_from_id(self, datafile_id):
        """Search for datafile with this id"""
        return (
            self.session.query(self.db_classes.Datafile)
            .filter(self.db_classes.Datafile.datafile_id == datafile_id)
            .first()
        )

    #############################################################
    # Search/lookup functions for reference data
    #############################################################

    @cache_results_if_not_none("_search_datafile_type_cache")
    def search_datafile_type(self, name):
        """Search for any datafile type with this name"""
        return (
            self.session.query(self.db_classes.DatafileType)
            .filter(func.lower(self.db_classes.DatafileType.name) == lowercase_or_none(name))
            .first()
        )

    @cache_results_if_not_none("_search_platform_type_cache")
    def search_platform_type(self, name):
        """Search for any platform type with this name"""
        # print(f"Searching platform type with name = {name}")
        return (
            self.session.query(self.db_classes.PlatformType)
            .filter(func.lower(self.db_classes.PlatformType.name) == lowercase_or_none(name))
            .first()
        )

    @cache_results_if_not_none("_search_nationality_cache")
    def search_nationality(self, name):
        """Search for any nationality with this name"""
        return (
            self.session.query(self.db_classes.Nationality)
            .filter(func.lower(self.db_classes.Nationality.name) == lowercase_or_none(name))
            .first()
        )

    @cache_results_if_not_none("_search_sensor_type_cache")
    def search_sensor_type(self, name):
        """Search for any sensor type featuring this name"""
        return (
            self.session.query(self.db_classes.SensorType)
            .filter(func.lower(self.db_classes.SensorType.name) == lowercase_or_none(name))
            .first()
        )

    @cache_results_if_not_none("_search_geometry_type_cache")
    def search_geometry_type(self, name):
        """Search for any Geometry Type featuring this name"""
        return (
            self.session.query(self.db_classes.GeometryType)
            .filter(func.lower(self.db_classes.GeometryType.name) == lowercase_or_none(name))
            .first()
        )

    def search_geometry_sub_type(self, name, parent):
        """Search for any Geometry Sub Type featuring this name and parent"""
        return (
            self.session.query(self.db_classes.GeometrySubType)
            .filter(func.lower(self.db_classes.GeometrySubType.name) == lowercase_or_none(name))
            .filter(self.db_classes.GeometrySubType.parent == parent)
            .first()
        )

    @cache_results_if_not_none("_search_privacy_cache")
    def search_privacy(self, name):
        """Search for any privacy with this name"""
        return (
            self.session.query(self.db_classes.Privacy)
            .filter(func.lower(self.db_classes.Privacy.name) == lowercase_or_none(name))
            .first()
        )

    def synonym_search(self, name, table, pk_field):
        """
        This method looks up the Synonyms Table and returns if there is any matched entity.

        :param name: Name to search
        :type name: String
        :param table: Table object to query found synonym entity
        :type table: :class:`BasePostGIS` or :class``BaseSpatiaLite
        :param pk_field: Primary Key field of the table
        :type pk_field: :class:`sqlalchemy.orm.attributes.InstrumentedAttribute`
        :return: Returns found entity or None
        """

        synonym = (
            self.session.query(self.db_classes.Synonym)
            .filter(
                func.lower(self.db_classes.Synonym.synonym) == lowercase_or_none(name),
                self.db_classes.Synonym.table == table.__tablename__,
            )
            .first()
        )
        if synonym:
            match = self.session.query(table).filter(pk_field == synonym.entity).first()
            if match:
                return match

        return None

    def find_datafile(self, datafile_name):
        """
        This method tries to find a Datafile entity with the given datafile_name. If it
        finds, it returns the entity. If it is not found, it searches synonyms.

        :param datafile_name:  Name of Datafile
        :type datafile_name: String
        :return:
        """
        cached_result = self._datafile_cache.get(datafile_name)
        if cached_result:
            return cached_result

        datafile = (
            self.session.query(self.db_classes.Datafile)
            .filter(
                func.lower(self.db_classes.Datafile.reference) == lowercase_or_none(datafile_name)
            )
            .first()
        )
        if datafile:
            self._datafile_cache[datafile_name] = datafile
            return datafile

        # Datafile is not found, try to find a synonym
        return self.synonym_search(
            name=datafile_name,
            table=self.db_classes.Datafile,
            pk_field=self.db_classes.Datafile.datafile_id,
        )

    def get_datafile(
        self,
        datafile_name=None,
        datafile_type=None,
        file_size=None,
        file_hash=None,
        change_id=None,
        privacy=None,
    ):
        """
        Adds an entry to the datafiles table of the specified name (path)
        and type if not already present. It uses find_datafile method to search existing datafiles.

        :param datafile_name:  Name of Datafile
        :type datafile_name: String
        :param datafile_type: Type of Datafile
        :type datafile_type: String
        :param file_size: Size of the file (in bytes)
        :type file_size: Integer
        :param file_hash: Hashed value of the file
        :type file_hash: String
        :param change_id: ID of the :class:`Change` object
        :type change_id: Integer or UUID
        :param privacy: Name of :class:`Privacy`
        :type privacy: String
        :return:  Created Datafile entity
        :rtype: Datafile
        """

        # Check for name match in Datafile and Synonym Tables
        if datafile_name:
            datafile = self.find_datafile(datafile_name=datafile_name)
            if datafile:
                # found object should be initialised because of _measurement variable
                if not hasattr(datafile, "measurements"):
                    datafile.__init__()
                return datafile

        datafile_type_obj = self.search_datafile_type(datafile_type)
        privacy_obj = self.search_privacy(privacy)
        if datafile_type_obj is None or privacy_obj is None:
            resolved_data = self.missing_data_resolver.resolve_datafile(
                self, datafile_name, datafile_type, privacy, change_id=change_id
            )

            datafile_name, datafile_type_obj, privacy_obj = resolved_data

        assert isinstance(
            datafile_type_obj, self.db_classes.DatafileType
        ), "Type error for DatafileType entity"
        assert isinstance(privacy_obj, self.db_classes.Privacy), "Type error for Privacy entity"

        return self.add_to_datafiles(
            simulated=False,
            privacy=privacy_obj.name,
            file_type=datafile_type_obj.name,
            reference=datafile_name,
            file_size=file_size,
            file_hash=file_hash,
            change_id=change_id,
        )

    def find_platform(self, name, nationality=None, identifier=None):
        """
        This method tries to find a Platform entity with the given platform details.

        If only the platform_name is given, then it searches synonyms ONLY. If all details
        are given then it searches for all the details in the database

        It does not currently use a cache.
        """
        # TODO: Add caching here if things get slow

        # Must have a name regardless what sort of search we're doing
        if name is None:
            return None

        if (nationality is None) and (identifier is None):
            # No nat or identifier, so just search synonyms
            synonym_result = self.synonym_search(
                name=name,
                table=self.db_classes.Platform,
                pk_field=self.db_classes.Platform.platform_id,
            )
            return synonym_result
        else:
            # Got all details, so search for all details and return results
            return self.search_platform(name, nationality, identifier)

    def get_platform(
        self,
        platform_name=None,
        identifier=None,
        nationality=None,
        platform_type=None,
        privacy=None,
        trigraph=None,
        quadgraph=None,
        change_id=None,
    ):
        """
        Adds an entry to the platforms table for the specified platform
        if not already present. It uses find_platform method to search existing platforms.

        :param platform_name: Name of :class:`Platform`
        :type platform_name: String
        :param nationality: Name of :class:`Nationality`
        :type nationality: String
        :param platform_type: Name of :class:`PlatformType`
        :type platform_type: String
        :param privacy: Name of :class:`Privacy`
        :type privacy: String
        :param trigraph: Trigraph of :class:`Platform`
        :type trigraph: String
        :param quadgraph: Quadgraph of :class:`Platform`
        :type quadgraph: String
        :param identifier: Identifier string of :class:`Platform`
        :type identifier: String
        :param change_id: ID of the :class:`Change` object
        :type change_id: Integer or UUID
        :return: Created Platform entity
        """

        # Check for name match in existing Platforms
        # If identifier and nationality are None then this just searches synonyms
        # otherwise, it searches the Platform table by all three fields
        if platform_name:
            platform = self.find_platform(
                name=platform_name, identifier=identifier, nationality=nationality
            )
            if platform:
                return platform

        nationality_obj = self.search_nationality(nationality)
        platform_type_obj = self.search_platform_type(platform_type)
        privacy_obj = self.search_privacy(privacy)

        if (
            platform_name is None
            or identifier is None
            or nationality_obj is None
            or platform_type_obj is None
            or privacy_obj is None
        ):
            resolved_data = self.missing_data_resolver.resolve_platform(
                self, platform_name, identifier, platform_type, nationality, privacy, change_id
            )
            # It means that new platform added as a synonym and existing platform returned
            if isinstance(resolved_data, self.db_classes.Platform):
                return resolved_data
            elif len(resolved_data) == 7:
                (
                    platform_name,
                    trigraph,
                    quadgraph,
                    identifier,
                    platform_type_obj,
                    nationality_obj,
                    privacy_obj,
                ) = resolved_data

        assert isinstance(
            nationality_obj, self.db_classes.Nationality
        ), "Type error for Nationality entity"
        assert isinstance(
            platform_type_obj, self.db_classes.PlatformType
        ), "Type error for PlatformType entity"
        assert isinstance(privacy_obj, self.db_classes.Privacy), "Type error for Privacy entity"

        return self.add_to_platforms(
            name=platform_name,
            trigraph=trigraph,
            quadgraph=quadgraph,
            identifier=identifier,
            nationality=nationality_obj.name,
            platform_type=platform_type_obj.name,
            privacy=privacy_obj.name,
            change_id=change_id,
        )

    def get_status(
        self,
        table_type,
        exclude=None,
    ):
        """
        Provides a summary of the contents of the :class:`DataStore`.

        :param table_type: one of Table Types
        :type table_type: Enum
        :param exclude: List of table names to exclude from the report
        :type exclude: List
        :return: The summary of the contents of the :class:`DataStore`
        :rtype: TableSummarySet
        """

        if exclude is None:
            exclude = []
        table_summaries = []
        for table_object in list(self.meta_classes[table_type]):
            if table_object.__tablename__ not in exclude:
                summary = TableSummary(self.session, table_object)
                table_summaries.append(summary)
        table_summaries_set = TableSummarySet(table_summaries)

        return table_summaries_set

    def search_comment_type(self, name):
        """Search for any comment type featuring this name"""
        return (
            self.session.query(self.db_classes.CommentType)
            .filter(func.lower(self.db_classes.CommentType.name) == lowercase_or_none(name))
            .first()
        )

    def add_to_comment_types(self, name, change_id):
        """
        Adds the specified comment type to the CommentType table if not already present

        :param name: Name of :class:`CommentType`
        :type name: String
        :param change_id: ID of the :class:`Change` object
        :type change_id: Integer or UUID
        :return: Created entity of :class:`CommentType` table
        :rtype: CommentType
        """
        comment_types = self.search_comment_type(name)
        if comment_types:
            return comment_types

        # enough info to proceed and create entry
        comment_type = self.db_classes.CommentType(name=name)
        self.session.add(comment_type)
        self.session.flush()

        self.add_to_logs(
            table=constants.COMMENT_TYPE,
            row_id=comment_type.comment_type_id,
            change_id=change_id,
        )

        return comment_type

    # End of Measurements
    #############################################################
    # Reference Type Maintenance

    def add_to_platform_types(self, name, change_id):
        """
        Adds the specified platform type to the platform types table if not already
        present.

        :param name: Name of :class:`PlatformType`
        :type name: String
        :param change_id: ID of the :class:`Change` object
        :type change_id: Integer or UUID
        :return: Created :class:`PlatformType` entity
        :rtype: PlatformType
        """
        platform_types = self.search_platform_type(name)
        if platform_types:
            return platform_types

        # enough info to proceed and create entry
        platform_type = self.db_classes.PlatformType(name=name)
        self.session.add(platform_type)
        self.session.flush()

        self.add_to_logs(
            table=constants.PLATFORM_TYPE,
            row_id=platform_type.platform_type_id,
            change_id=change_id,
        )

        return platform_type

    def add_to_nationalities(self, name, change_id, priority=None):
        """
        Adds the specified nationality to the nationalities table if not already present

        :param name: Name of :class:`Nationality`
        :type name: String
        :param change_id: ID of the :class:`Change` object
        :type change_id: Integer or UUID
        :param priority: Priority to print in defaults of CLI
        :type priority: Integer
        :return: Created :class:`Nationality` entity
        :rtype: Nationality
        """
        nationalities = self.search_nationality(name)
        if nationalities:
            return nationalities

        # enough info to proceed and create entry
        nationality = self.db_classes.Nationality(name=name)
        if priority:
            nationality.priority = priority
        self.session.add(nationality)
        self.session.flush()

        self.add_to_logs(
            table=constants.NATIONALITY,
            row_id=nationality.nationality_id,
            change_id=change_id,
        )
        return nationality

    def add_to_privacies(self, name, level, change_id):
        """
        Adds the specified privacy entry to the :class:`Privacy` table if not already present.

        :param name: Name of :class:`Privacy`
        :type name: String
        :param level: Level of :class:`Privacy`
        :type level: Integer
        :param change_id: ID of the :class:`Change` object
        :type change_id: Integer or UUID
        :return: Created :class:`Privacy` entity
        :rtype: Privacy
        """
        privacies = self.search_privacy(name)
        if privacies:
            return privacies

        # enough info to proceed and create entry
        privacy = self.db_classes.Privacy(name=name, level=level)
        self.session.add(privacy)
        self.session.flush()

        self.add_to_logs(table=constants.PRIVACY, row_id=privacy.privacy_id, change_id=change_id)
        return privacy

    def add_to_datafile_types(self, name, change_id):
        """
        Adds the specified datafile type to the datafile types table if not already
        present.

        :param name: Name of :class:`DatafileType`
        :type name: String
        :param change_id: ID of the :class:`Change` object
        :type change_id: Integer or UUID
        :return: Wrapped database entity for :class:`DatafileType`
        :rtype: DatafileType
        """
        datafile_types = self.search_datafile_type(name)
        if datafile_types:
            return datafile_types

        # proceed and create entry
        datafile_type_obj = self.db_classes.DatafileType(name=name)

        self.session.add(datafile_type_obj)
        self.session.flush()

        self.add_to_logs(
            table=constants.DATAFILE_TYPE,
            row_id=datafile_type_obj.datafile_type_id,
            change_id=change_id,
        )
        return datafile_type_obj

    def add_to_sensor_types(self, name, change_id):
        """
        Adds the specified sensor type to the :class:`SensorType` table if not already present.

        :param name: Name of :class:`SensorType`
        :type name: String
        :param change_id: ID of the :class:`Change` object
        :type change_id: Integer or UUID
        :return: Created :class:`SensorType` entity
        :rtype: SensorType
        """
        sensor_types = self.search_sensor_type(name)
        if sensor_types:
            return sensor_types

        # enough info to proceed and create entry
        sensor_type = self.db_classes.SensorType(name=name)
        self.session.add(sensor_type)
        self.session.flush()

        self.add_to_logs(
            table=constants.SENSOR_TYPE,
            row_id=sensor_type.sensor_type_id,
            change_id=change_id,
        )
        return sensor_type

    def add_to_geometry_types(self, name, change_id):
        """
        Adds the specified geometry type to the :class:`GeometryType` table if not already present.

        :param name: Name of :class:`GeometryType`
        :type name: String
        :param change_id: ID of the :class:`Change` object
        :type change_id: Integer or UUID
        :return: Created :class:`GeometryType` entity
        :rtype: GeometryType
        """
        geom_type = self.search_geometry_type(name)
        if geom_type:
            return geom_type

        # enough info to proceed and create entry
        geom_type = self.db_classes.GeometryType(name=name)
        self.session.add(geom_type)
        self.session.flush()

        self.add_to_logs(
            table=constants.GEOMETRY_TYPE,
            row_id=geom_type.geo_type_id,
            change_id=change_id,
        )
        return geom_type

    def add_to_geometry_sub_types(self, name, parent_name, change_id):
        """
        Adds the specified geometry sub type to the :class:`GeometrySubType` table if not already present.

        :param name: Name of :class:`GeometrySubType`
        :type name: String
        :param parent_name: Name of parent :class:`GeometryType`
        :type parent_name: String
        :param change_id: ID of the :class:`Change` object
        :type change_id: Integer or UUID
        :return: Created :class:`GeometrySubType` entity
        :rtype: GeometrySubType
        """
        geo_type_obj = self.search_geometry_type(parent_name)
        if geo_type_obj is None:
            geo_type_obj = self.add_to_geometry_types(parent_name, change_id)

        geom_sub_type = self.search_geometry_sub_type(name, geo_type_obj.geo_type_id)
        if geom_sub_type:
            return geom_sub_type

        # enough info to proceed and create entry
        geom_sub_type = self.db_classes.GeometrySubType(name=name, parent=geo_type_obj.geo_type_id)
        self.session.add(geom_sub_type)
        self.session.flush()

        self.add_to_logs(
            table=constants.GEOMETRY_SUBTYPE,
            row_id=geom_sub_type.geo_sub_type_id,
            change_id=change_id,
        )
        return geom_sub_type

    def add_to_help_texts(self, id, guidance, change_id):
        """
        Adds the specified help text to the :class:`HelpText` table if not already present.

        :param id: ID of prompt question
        :type id: Integer
        :param guidance: Guidance text for contextual help
        :type guidance: String
        :param change_id: ID of the :class:`Change` object
        :type change_id: Integer or UUID
        :return: Created :class:`HelpText` entity
        :rtype: HelpText
        """

        # enough info to proceed and create entry
        help_text = self.db_classes.HelpText(id=id, guidance=guidance)
        self.session.add(help_text)
        self.session.flush()

        self.add_to_logs(
            table=constants.SENSOR_TYPE,
            row_id=help_text.help_text_id,
            change_id=change_id,
        )
        return help_text

    # End of References
    #############################################################
    # Metadata Maintenance

    def add_to_logs(self, table, row_id, field=None, previous_value=None, change_id=None):
        """
        Adds the specified event to the :class:`Logs` table if not already present.

        :param table: Name of the table
        :param row_id: Entity ID of the tale
        :param field:  Name of the field
        :param previous_value:  Previous value of the field
        :param change_id: ID of the :class:`Change` object
        :type change_id: Integer or UUID
        :param change_id:  Row ID of entity of :class:`Changes` about the change
        :return: Created :class:`Logs` entity
        """
        log = self.db_classes.Log(
            table=table,
            id=row_id,
            field=field,
            previous_value=previous_value,
            change_id=change_id,
        )
        self.session.add(log)
        self.session.flush()

        return log

    def add_to_changes(self, user, modified, reason):
        """
        Adds the specified event to the :class:`Change` table if not already present.

        :param user: Username of the current login
        :param modified: Change date
        :param reason:  Reason of the change
        :return: Created :class:`Change` entity
        """
        change = self.db_classes.Change(
            user=user,
            modified=modified,
            reason=reason,
        )
        self.session.add(change)
        self.session.flush()

        return change

    # End of Metadata Maintenance
    #############################################################

    def clear_db_contents(self):
        """Delete contents of all database tables"""
        if self.db_type == "sqlite":
            meta = BaseSpatiaLite.metadata
        else:
            meta = BasePostGIS.metadata

        with self.session_scope():
            for table in reversed(meta.sorted_tables):
                self.session.execute(table.delete())

    def clear_db_schema(self):
        """Delete the database schema (ie all of the tables)"""
        if self.db_type == "sqlite":
            meta = BaseSpatiaLite.metadata
            with self.session_scope():
                meta.drop_all()
                self.session.execute("DROP TABLE IF EXISTS alembic_version;")
        else:
            with self.engine.connect() as connection:
                connection.execute('DROP SCHEMA IF EXISTS "pepys" CASCADE;')

    def get_all_datafiles(self):
        """Returns all datafiles.

        :return: All Datafile entities in the DB
        :rtype: List
        """
        datafiles = self.session.query(self.db_classes.Datafile).all()
        return datafiles

    def get_cached_comment_type_name(self, comment_type_id):
        """
        Get comment type name from cache on "comment_type_id"
        If name is not found in the cache, sytem will load from the data store,
        and add it into cache.
        """
        if comment_type_id:
            # return from cache
            if comment_type_id in self._comment_type_name_dict_on_comment_type_id:
                return self._comment_type_name_dict_on_comment_type_id[comment_type_id]
            comment_type = (
                self.session.query(self.db_classes.CommentType)
                .filter(self.db_classes.CommentType.comment_type_id == comment_type_id)
                .first()
            )

            if comment_type:
                self._comment_type_name_dict_on_comment_type_id[comment_type_id] = comment_type.name
                return comment_type.name
            else:
                raise Exception(f"No Comment Type found with Comment type id: {comment_type_id}")

    def get_cached_sensor_name(self, sensor_id):
        # return from cache
        if sensor_id in self._sensor_dict_on_sensor_id:
            return self._sensor_dict_on_sensor_id[sensor_id]
        sensor = (
            self.session.query(self.db_classes.Sensor)
            .filter(self.db_classes.Sensor.sensor_id == sensor_id)
            .first()
        )

        if sensor:
            self._sensor_dict_on_sensor_id[sensor_id] = sensor.name
            return sensor.name
        else:
            raise Exception(f"No Sensor found with sensor id: {sensor_id}")

    def get_cached_platform_name(self, sensor_id=None, platform_id=None):
        """
        Get platform name from cache on either "sensor_id" or "platform_id"
        If name is not found in the cache, system will load from this data store,
        and cache it.

        :param sensor_id: ID of the :class:`Sensor`
        :type sensor_id: Integer or UUID
        :param platform_id: ID of the :class:`Platform`
        :type platform_id: Integer or UUID
        """
        # invalid parameter handling
        if sensor_id is None and platform_id is None:
            raise Exception(
                "Either 'sensor_id' or 'platform_id' has to be provided to get 'platform name'"
            )

        if sensor_id:
            # return from cache
            if sensor_id in self._platform_dict_on_sensor_id:
                return self._platform_dict_on_sensor_id[sensor_id]
            sensor = (
                self.session.query(self.db_classes.Sensor)
                .filter(self.db_classes.Sensor.sensor_id == sensor_id)
                .first()
            )

            if sensor:
                platform_id = sensor.host
            else:
                raise Exception(f"No Sensor found with sensor id: {sensor_id}")

        if platform_id:
            # return from cache
            if platform_id in self._platform_dict_on_platform_id:
                return self._platform_dict_on_platform_id[platform_id]
            platform = (
                self.session.query(self.db_classes.Platform)
                .filter(self.db_classes.Platform.platform_id == platform_id)
                .first()
            )

            if platform:
                self._platform_dict_on_platform_id[platform_id] = platform.name
                if sensor_id:
                    self._platform_dict_on_sensor_id[sensor_id] = platform.name
                return platform.name
            else:
                raise Exception(f"No Platform found with platform id: {platform_id}")

    def find_min_and_max_date(self, table, filter_by, value):
        """
        Queries the given table, finds the minimum date and the maximum date. Returns these values
        with including the source id.

        :param table: A Base Database Class
        :type table: State, Contact, or Comment
        :param filter_by: Attribute of the DB class
        :type filter_by:
        :param value: Value (an ID, e.g. sensor_id) to filter the given table
        :type value: Integer or UUID
        :return: Minimum date, maximum date, and source_id
        :rtype: tuple
        """
        if table.__tablename__ not in [constants.STATE, constants.CONTACT, constants.COMMENT]:
            raise ValueError(
                "Table should be one of the following classes: " "State, Contact, Comment"
            )
        return (
            self.session.query(func.min(table.time), func.max(table.time), table.source_id)
            .filter(filter_by == value)
            .group_by(table.source_id)
            .first()
        )

    def find_related_datafile_objects(self, platform_id, sensors_dict):
        """
        Finds all related datafile objects for the given platform ID and sensor IDs. Creates a list,
        which has the information of the found objects, and returns it.

        :param platform_id: ID of the :class:`Platform`
        :type platform_id: Integer or UUID
        :param sensors_dict: A dictionary that contains Sensor names and IDs of the given Platform
        :type sensors_dict: dict
        :return: Returns found State-Contact-Comment objects in a list form
        :rtype: list
        """
        objects = list()
        State = self.db_classes.State
        Contact = self.db_classes.Contact
        Comment = self.db_classes.Comment

        # Iterate over each sensor of the platform
        for sensor_name, sensor_id in sensors_dict.items():
            datafile_name, datafile_id, datafile_id_2 = None, None, None
            # Find minimum date, maximum date, and datafile name of the filtered State objects
            result = self.find_min_and_max_date(State, State.sensor_id, sensor_id)
            min_time, max_time = datetime.utcnow(), datetime(day=1, month=1, year=1700)
            if result:
                assert (
                    len(result) == 3
                ), "It should return minimum date, maximum date and datafile id in a row!"
                min_time, max_time, datafile_id = result
                # Extract datafile name from the given datafile id
                datafile_name = self.get_datafile_from_id(datafile_id).reference

            # Find minimum date, maximum date, and datafile name of the filtered Contact objects
            result = self.find_min_and_max_date(Contact, Contact.sensor_id, sensor_id)
            min_time_2, max_time_2 = datetime.utcnow(), datetime(day=1, month=1, year=1700)
            if result:
                assert (
                    len(result) == 3
                ), "It should return minimum date, maximum date and datafile id in a row!"
                min_time_2, max_time_2, datafile_id_2 = result
                if not datafile_name:
                    datafile_name = self.get_datafile_from_id(datafile_id_2).reference
            # Compare min and max dates of State and Contact objects
            min_, max_ = min(min_time, min_time_2), max(max_time, max_time_2)
            # Append to list if every value is assigned
            if sensor_name and datafile_name and min_ and max_:
                objects.append(
                    {
                        "name": sensor_name,
                        "filename": datafile_name,
                        "min": str(min_),
                        "max": str(max_),
                        "sensor_id": sensor_id,
                        "datafile_id": datafile_id or datafile_id_2,
                    }
                )
        # Find minimum date, maximum date, and datafile name of the filtered Comment objects
        comment_objects = self.find_min_and_max_date(Comment, Comment.platform_id, platform_id)
        if comment_objects:
            min_time, max_time, datafile_id = comment_objects
            datafile_name = self.get_datafile_from_id(datafile_id).reference
            objects.append(
                {
                    "name": "Comment",
                    "filename": datafile_name,
                    "min": min_time,
                    "max": max_time,
                    "platform_id": platform_id,
                    "datafile_id": datafile_id,
                }
            )

        return objects

    def export_datafile(self, datafile_id, file_path, sensor_id=None, platform_id=None):
        """Gets states, contacts and comments of a Datafile.

        :param datafile_id:  ID of Datafile
        :type datafile_id: Integer or UUID
        :param file_path: Path of a file to export
        :type file_path: String
        :param sensor_id: ID of Sensor to export a specific sensor in the datafile, default is None
        :type sensor_id: Integer or UUID
        :param platform_id: ID of Platform to export comments of a specific platform in the datafile,
        default is None
        :type platform_id: Integer or UUID
        """

        with open(f"{file_path}", "w+") as file:
            states, contacts, comments = list(), list(), list()
            # If States and Contacts are going to be exported
            if sensor_id:
                states = (
                    self.session.query(self.db_classes.State)
                    .filter(self.db_classes.State.source_id == datafile_id)
                    .filter(self.db_classes.State.sensor_id == sensor_id)
                    .all()
                )
                contacts = (
                    self.session.query(self.db_classes.Contact)
                    .filter(self.db_classes.Contact.source_id == datafile_id)
                    .filter(self.db_classes.Contact.sensor_id == sensor_id)
                    .all()
                )
            # If Comments are going to be exported
            elif platform_id:
                comments = (
                    self.session.query(self.db_classes.Comment)
                    .filter(self.db_classes.Comment.source_id == datafile_id)
                    .filter(self.db_classes.Comment.platform_id == platform_id)
                    .all()
                )
            # If all datafile are going to be exported
            else:
                states = (
                    self.session.query(self.db_classes.State)
                    .filter(self.db_classes.State.source_id == datafile_id)
                    .all()
                )
                contacts = (
                    self.session.query(self.db_classes.Contact)
                    .filter(self.db_classes.Contact.source_id == datafile_id)
                    .all()
                )
                comments = (
                    self.session.query(self.db_classes.Comment)
                    .filter(self.db_classes.Comment.source_id == datafile_id)
                    .all()
                )

            # Export states
            for state in states:
                #  load platform name from cache.
                platform_name = self.get_cached_platform_name(sensor_id=state.sensor_id)

                if state.elevation is None:
                    depth_str = "NaN"
                elif state.elevation == 0.0:
                    depth_str = "0.0"
                else:
                    depth_str = str(-1 * state.elevation.magnitude)

                state_rep_line = [
                    format_datetime(state.time),
                    platform_name,
                    "AA",
                    state.location.convert_point(),
                    f"{state.heading.magnitude:.2f}" if state.heading else "0",
                    f"{state.speed.to(unit_registry.knot).magnitude:.2f}" if state.speed else "0",
                    depth_str,
                ]
                data = "\t".join(state_rep_line)
                file.write(data + "\n")

            # Export contacts
            for contact in contacts:
                #  load platform name from cache.
                platform_name = self.get_cached_platform_name(sensor_id=contact.sensor_id)
                sensor_name = self.get_cached_sensor_name(sensor_id=contact.sensor_id)

                contact_rep_line = [
                    format_datetime(contact.time),
                    platform_name,
                    "@@",
                    contact.location.convert_point() if contact.location else "NULL",
                    f"{contact.bearing.magnitude:.2f}" if contact.bearing else "NULL",
                    f"{contact.range.to(unit_registry.yard).magnitude:.2f}"
                    if contact.range
                    else "NULL",
                    sensor_name,
                    "N/A",
                ]

                if contact.ambig_bearing or contact.freq:
                    contact_rep_line.insert(0, ";SENSOR2:")

                    contact_rep_line.insert(
                        6,
                        f"{contact.ambig_bearing.magnitude:.2f}"
                        if contact.ambig_bearing
                        else "NULL",
                    )
                    contact_rep_line.insert(
                        7,
                        f"{contact.freq.magnitude:.2f}" if contact.freq else "NULL",
                    )
                else:
                    contact_rep_line.insert(0, ";SENSOR:")
                data = "\t".join(contact_rep_line)
                file.write(data + "\n")

            # Export comments
            for comment in comments:
                vessel_name = self.get_cached_platform_name(platform_id=comment.platform_id)
                message = comment.content
                comment_type_name = self.get_cached_comment_type_name(comment.comment_type_id)

                comment_rep_line = [
                    format_datetime(comment.time),
                    vessel_name,
                    comment_type_name,
                    message,
                ]

                if comment_type_name == "None":
                    comment_rep_line.insert(0, ";NARRATIVE:")
                    del comment_rep_line[3]
                else:
                    comment_rep_line.insert(0, ";NARRATIVE2:")

                data = "\t".join(comment_rep_line)
                file.write(data + "\n")

    def is_datafile_loaded_before(self, file_size, file_hash):
        """
        Queries the Datafile table to check whether the given file is loaded before or not.

        :param file_size: Size of the file (in bytes)
        :type file_size: Integer
        :param file_hash: Hashed value of the file
        :type file_hash: String
        :return: True if the datafile is loaded before, False otherwise
        :rtype: bool
        """
        is_loaded_before = (
            self.session.query(self.db_classes.Datafile)
            .filter(self.db_classes.Datafile.size == file_size)
            .filter(self.db_classes.Datafile.hash == file_hash)
            .first()
        )
        if is_loaded_before:
            print(
                f"'{is_loaded_before.reference}' was already loaded at {is_loaded_before.created_date:%Y-%m-%d %H:%M}! Skipping the file."
            )
            return True
        return False

    def is_empty(self):
        """ Returns True if sample table (Privacy) is empty, False otherwise"""
        reference = self.session.query(self.db_classes.Privacy).first()
        if reference:
            return False
        return True

    def get_logs_by_change_id(self, change_id):
        """Returns Logs objects filtered by change_id"""
        return (
            self.session.query(self.db_classes.Log)
            .filter(self.db_classes.Log.change_id == change_id)
            .all()
        )

    def _check_master_id(self, table_obj, master_id):
        master_obj = (
            self.session.query(table_obj)
            .filter(getattr(table_obj, get_primary_key_for_table(table_obj)) == master_id)
            .scalar()
        )
        if not master_obj:
            raise ValueError(f"No object found with the given master_id: '{master_id}'!")
        return master_obj

    def _get_table_object(self, table_name):
        # Table names are plural in the database, therefore make it singular
        table = table_name_to_class_name(table_name)
        return getattr(self.db_classes, table)

    def _get_comments_and_sensors_of_platform(self, platform) -> list:
        Sensor = self.db_classes.Sensor
        Comment = self.db_classes.Comment
        objects = list(dependent_objects(platform))
        objects = [obj for obj in objects if isinstance(obj, Sensor) or isinstance(obj, Comment)]
        return objects

    def _find_datafiles_and_measurements_for_platform(self, platform) -> dict:
        objects = self._get_comments_and_sensors_of_platform(platform)
        datafile_ids = dict()

        while objects:
            obj = objects.pop(0)
            if isinstance(obj, self.db_classes.Sensor):
                objects.extend(list(dependent_objects(obj)))
            else:
                if obj.source_id not in datafile_ids:
                    datafile_ids[obj.source_id] = {"time": obj.time, "objects": []}
                if obj.time < datafile_ids[obj.source_id]["time"]:
                    datafile_ids[obj.source_id]["time"] = obj.time
                if not isinstance(obj, self.db_classes.Comment):  # They are handled differently
                    datafile_ids[obj.source_id]["objects"].append(obj)

        return datafile_ids

    def update_platform_ids(self, merge_platform_id, master_platform_id, change_id):
        Comment = self.db_classes.Comment
        Participant = self.db_classes.Participant
        LogsHolding = self.db_classes.LogsHolding
        Geometry1 = self.db_classes.Geometry1
        Media = self.db_classes.Media
        tables_with_platform_id_fields = [Comment, Participant, LogsHolding, Geometry1, Media]
        possible_field_names = [
            "platform_id",
            "subject_id",
            "host_id",
            "subject_platform_id",
            "sensor_platform_id",
        ]
        for table in tables_with_platform_id_fields:
            for field in possible_field_names:
                try:
                    table_platform_id = getattr(table, field)
                    primary_key_field = get_primary_key_for_table(table)
                    query = self.session.query(table).filter(table_platform_id == merge_platform_id)
                    [
                        self.add_to_logs(
                            table=table.__tablename__,
                            row_id=getattr(s, primary_key_field),
                            field=field,
                            previous_value=str(merge_platform_id),
                            change_id=change_id,
                        )
                        for s in query.all()
                    ]
                    query.update({field: master_platform_id})
                except Exception:
                    pass
        self.session.flush()

    def merge_platforms(self, platform_list, master_id, change_id, set_percentage=None) -> bool:
        """Merges given platforms. Moves sensors from other platforms to the Target platform.
        If sensor with same name is already present on Target platform, moves measurements
        to that sensor. Also moves entities in Comments, Participants, LogsHoldings, Geometry, Media
        tables from other platforms to the Target platform.

        :param platform_list: A list of platform IDs or platform objects
        :type platform_list: List
        :param master_id: Target platform's ID or objects itself
        :type master_id: UUID or Platform
        :return: True if merging completed successfully, False otherwise.
        :rtype: bool
        """
        Platform = self.db_classes.Platform
        Sensor = self.db_classes.Sensor
        self._check_master_id(Platform, master_id)
        master_sensor_names = self.session.query(Sensor.name).filter(Sensor.host == master_id).all()
        master_sensor_names = set([n for (n,) in master_sensor_names])
        sensor_list = list()

        # Make this bit of the processing take up 40% of the progress bar
        percentage_per_iteration = 40.0 / len(platform_list)

        for i, p_id in enumerate(platform_list):
            self.update_platform_ids(p_id, master_id, change_id)

            sensors = self.session.query(Sensor).filter(Sensor.host == p_id).all()
            sensor_list.extend(sensors)
            if callable(set_percentage):
                set_percentage(10 + (i * percentage_per_iteration))

        # Make this bit of the processing take up 50% of the progress bar
        percentage_per_iteration = 50.0 / len(platform_list)

        for sensor in sensor_list:
            if sensor.name not in master_sensor_names:
                query = self.session.query(Sensor).filter(Sensor.sensor_id == sensor.sensor_id)
                [
                    self.add_to_logs(
                        table=constants.SENSOR,
                        row_id=s.sensor_id,
                        field="host",
                        previous_value=str(s.host),
                        change_id=change_id,
                    )
                    for s in query.all()
                ]
                query.update({"host": master_id})
                master_sensor_names.add(sensor.name)
            else:  # Move measurements only
                master_sensor_id = (
                    self.session.query(Sensor.sensor_id)
                    .filter(Sensor.host == master_id, Sensor.name == sensor.name)
                    .scalar()
                )
                self.merge_measurements(
                    constants.SENSOR, [sensor.sensor_id], master_sensor_id, change_id
                )
            if callable(set_percentage):
                set_percentage(50 + (i * percentage_per_iteration))

        # Delete merged platforms
        self.delete_objects(constants.PLATFORM, platform_list)
        self.session.flush()
        return True

    def merge_measurements(self, table_name, id_list, master_id, change_id, set_percentage=None):
        if table_name == constants.SENSOR:
            table_obj = self.db_classes.Sensor
            field = "sensor_id"
            self._check_master_id(table_obj, master_id)
            table_objects = [self.db_classes.State, self.db_classes.Contact]
        elif table_name == constants.DATAFILE:
            table_obj = self.db_classes.Datafile
            field = "source_id"
            self._check_master_id(table_obj, master_id)
            table_objects = [
                self.db_classes.State,
                self.db_classes.Contact,
                self.db_classes.Activation,
                self.db_classes.LogsHolding,
                self.db_classes.Comment,
                self.db_classes.Geometry1,
                self.db_classes.Media,
            ]
        else:
            raise ValueError(
                f"You should give one of the following tables to merge measurements: "
                f"{constants.SENSOR}, {constants.DATAFILE}"
            )
        values = ",".join(map(str, id_list))

        # We've already used 10% of the progress bar in merge_generic
        percentage_per_iteration = 90.0 / len(table_objects)

        for i, t_obj in enumerate(table_objects):
            query = self.session.query(t_obj).filter(getattr(t_obj, field).in_(id_list))
            [
                self.add_to_logs(
                    table=t_obj.__tablename__,
                    row_id=getattr(s, field),
                    field=field,
                    previous_value=values,
                    change_id=change_id,
                )
                for s in query.all()
            ]
            query.update({field: master_id}, synchronize_session="fetch")

            if callable(set_percentage):
                set_percentage(10 + (i * percentage_per_iteration))

        # Delete merged objects
        self.delete_objects(table_name, id_list)

    def merge_objects(self, table_name, id_list, master_id, change_id, set_percentage=None):
        table_obj = self._get_table_object(table_name)
        to_obj = self._check_master_id(table_obj, master_id)

        # We've already used 10% of the progress bar in merge_generic,
        # and want to keep 10% for deleting objects
        percentage_per_iteration = 80.0 / len(id_list)

        for i, obj_id in enumerate(id_list):
            primary_key_field = get_primary_key_for_table(table_obj)
            from_obj = (
                self.session.query(table_obj)
                .filter(getattr(table_obj, primary_key_field) == obj_id)
                .scalar()
            )
            merge_references(from_obj, to_obj)
            self.add_to_logs(
                table=table_obj.__tablename__,
                row_id=getattr(from_obj, primary_key_field),
                field=primary_key_field,
                previous_value=str(obj_id),
                change_id=change_id,
            )
            self.session.flush()

            if callable(set_percentage):
                set_percentage(10 + (i * percentage_per_iteration))
        # Delete merged objects
        self.delete_objects(table_name, id_list)

    def merge_generic(self, table_name, id_list, master_id, set_percentage=None) -> bool:
        reference_table_objects = self.meta_classes[TableTypes.REFERENCE]
        reference_table_names = [obj.__tablename__ for obj in reference_table_objects]

        table_obj = self._get_table_object(table_name)
        if id_list and not isinstance(id_list[0], uuid.UUID):
            id_list = [getattr(i, get_primary_key_for_table(table_obj)) for i in id_list]

        if not isinstance(master_id, uuid.UUID):
            master_id = getattr(master_id, get_primary_key_for_table(table_obj))

        reason_list = ",".join([str(p) for p in id_list])
        change_id = self.add_to_changes(
            user=USER,
            modified=datetime.utcnow(),
            reason=f"Merging {table_name} '{reason_list}' to '{master_id}'.",
        ).change_id

        if callable(set_percentage):
            set_percentage(10)

        if master_id in id_list:
            id_list.remove(master_id)  # We don't need to change these values

        if table_name == constants.PLATFORM:
            self.merge_platforms(id_list, master_id, change_id, set_percentage)
        elif table_name in [constants.SENSOR, constants.DATAFILE]:
            self.merge_measurements(table_name, id_list, master_id, change_id, set_percentage)
        elif table_name in reference_table_names + [constants.TAG, constants.TASK]:
            self.merge_objects(table_name, id_list, master_id, change_id, set_percentage)
        else:
            return False

        if callable(set_percentage):
            set_percentage(100)
        return True

    def split_platform(self, platform_id, set_percentage=None) -> bool:
        to_delete = list()
        Platform = self.db_classes.Platform
        Sensor = self.db_classes.Sensor
        if isinstance(platform_id, Platform):
            platform_id = platform_id.platform_id

        platform = self._check_master_id(Platform, platform_id)
        change_id = self.add_to_changes(
            user=USER,
            modified=datetime.utcnow(),
            reason=f"Splitting platform: '{platform_id}'.",
        ).change_id
        datafile_ids = self._find_datafiles_and_measurements_for_platform(platform)
        objects = self._get_comments_and_sensors_of_platform(platform)

        i = 0
        percent_per_iteration = 100.0 / len(datafile_ids)

        for key, values in datafile_ids.items():
            time, measurement_objects = values["time"], values["objects"]
            new_platform = self.add_to_platforms(
                name=platform.name,
                nationality=platform.nationality_name,
                platform_type=platform.platform_type_name,
                privacy=platform.privacy_name,
                trigraph=platform.trigraph,
                quadgraph=platform.quadgraph,
                identifier=f"{time:%Y%m%d-%H%M%S}-{str(key)[-4:]}",
                change_id=change_id,
            )
            for obj in objects:
                primary_key_field = get_primary_key_for_table(obj)
                if isinstance(obj, Sensor):
                    for m_obj in measurement_objects:
                        if m_obj.sensor_id == obj.sensor_id:
                            new_sensor = new_platform.get_sensor(
                                data_store=self,
                                sensor_name=obj.name,
                                sensor_type=obj.sensor_type_name,
                                privacy=obj.privacy_name,
                                change_id=change_id,
                            )
                            old_id = m_obj.sensor_id
                            m_obj.sensor_id = new_sensor.sensor_id
                            self.add_to_logs(
                                table=obj.__tablename__,
                                row_id=getattr(obj, primary_key_field),
                                field="sensor_id",
                                previous_value=str(old_id),
                                change_id=change_id,
                            )
                    if obj not in to_delete:
                        to_delete.append(obj)
                    self.session.flush()
                else:
                    if key == obj.source_id:
                        table = type(obj)
                        field = "platform_id"
                        table_platform_id = getattr(table, field)
                        source_field = getattr(table, "source_id")
                        query = self.session.query(table).filter(
                            table_platform_id == platform.platform_id, source_field == key
                        )
                        [
                            self.add_to_logs(
                                table=obj.__tablename__,
                                row_id=getattr(s, primary_key_field),
                                field=field,
                                previous_value=str(platform.platform_id),
                                change_id=change_id,
                            )
                            for s in query.all()
                        ]
                        query.update({field: new_platform.platform_id}, synchronize_session="fetch")

            if callable(set_percentage):
                set_percentage(i * percent_per_iteration)

        # delete the split platform
        self.session.delete(platform)
        for s in to_delete:
            self.session.delete(s)
        self.session.flush()

    def edit_items(self, items, edit_dict):
        """
        Edits the given list of items, changing the fields to the new ones specified in edit_dict

        :param items: List of objects to edit
        :type items: Database objects (eg. Platform, Sensor, Nationality)
        :param edit_dict: Dictionary with keys specifying the fields to be edited, and values specifying the new value.
        For foreign keyed fields, the new value should be the ID of an existing entry in the foreign table
        :type edit_dict: Dict
        """
        table_object = type(items[0])

        ids = [str(getattr(item, get_primary_key_for_table(table_object))) for item in items]
        ids_list_str = ", ".join(ids)

        change_id = self.add_to_changes(
            user=USER,
            modified=datetime.utcnow(),
            reason=f"Editing {table_object.__tablename__} items: {ids_list_str}",
        ).change_id

        # Get a query for all objects that match the IDs
        query = self.session.query(table_object).filter(
            getattr(table_object, get_primary_key_for_table(table_object)).in_(ids)
        )
        update_dict = {}
        # Convert the edit_dict we get from the GUI into a dict suitable for use in the update function
        # This involves converting any association proxy column names into the relevant foreign key name to set
        for col_name, new_value in edit_dict.items():
            attr_from_db_class = getattr(table_object, col_name)
            if isinstance(
                attr_from_db_class, sqlalchemy.ext.associationproxy.ColumnAssociationProxyInstance
            ):
                relationship_name = attr_from_db_class.target_collection
                relationship_obj = getattr(table_object, relationship_name)
                foreign_key_col_name = list(relationship_obj.property.local_columns)[0].key
                update_dict[foreign_key_col_name] = new_value
            else:
                update_dict[col_name] = new_value

        query.update(update_dict, synchronize_session="fetch")
        self.session.commit()

        # Add a log entry for each field we've updated
        # (We do all the updates in one SQL query above, for efficiency, but have to loop through the items
        # and fields here to create the logs entries)
        for item in items:
            for col_name, new_value in update_dict.items():
                self.add_to_logs(
                    table_object.__tablename__,
                    row_id=getattr(item, get_primary_key_for_table(table_object)),
                    field=col_name,
                    previous_value=str(getattr(item, col_name)),
                    change_id=change_id,
                )

    def find_dependent_objects(self, table_obj, id_list: list) -> dict:
        """
        Finds the dependent objects of the given list of items. Counts them by their type,
        i.e. X Sensors, Y Platforms. Returns a dictionary that has table names as keys,
        and number of dependent objects as values.

        :param table_obj: A table object, or name of the table that IDs belong to
        :type table_obj: SQLAlchemy Model or str
        :param id_list: List of objects IDs
        :type id_list: list
        """
        output = dict()
        object_list = list()
        if isinstance(table_obj, str):
            table_obj = self._get_table_object(table_obj)
        objects = (
            self.session.query(table_obj)
            .filter(getattr(table_obj, get_primary_key_for_table(table_obj)).in_(id_list))
            .all()
        )
        if objects:
            output[table_obj.__tablename__] = len(objects)
        while objects:  # find all dependent objects and add them to object_list
            curr_obj = objects.pop(0)
            dependent_objs = list(dependent_objects(curr_obj))
            objects.extend(dependent_objs)
            object_list.extend(dependent_objs)
        # remove duplicated entities
        object_list = list(set(object_list))
        for o in object_list:
            table_name = type(o).__tablename__
            if table_name not in output:
                output[table_name] = 1
            else:
                output[table_name] += 1

        return output

    def delete_objects(self, table_obj, id_list):
        """
        Deletes the given objects.

        :param table_obj: A table object, or name of the table that IDs belong to
        :type table_obj: SQLAlchemy Model or str
        :param id_list: List of objects IDs
        :type id_list: list
        """
        if isinstance(table_obj, str):
            table_obj = self._get_table_object(table_obj)
        # Delete merged objects
        self.session.query(table_obj).filter(
            getattr(table_obj, get_primary_key_for_table(table_obj)).in_(id_list)
        ).delete(synchronize_session="fetch")
        self.session.flush()
