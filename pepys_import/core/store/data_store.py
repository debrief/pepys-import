import csv
import os

from datetime import datetime
from getpass import getuser
from sqlalchemy import create_engine, or_
from sqlalchemy.event import listen
from sqlalchemy.sql import select, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from importlib import import_module
from contextlib import contextmanager

from paths import PEPYS_IMPORT_DIRECTORY
from pepys_import.resolvers.default_resolver import DefaultResolver
from pepys_import.utils.data_store_utils import import_from_csv
from pepys_import.utils.geoalchemy_utils import load_spatialite
from pepys_import.core.store import constants
from .db_base import BasePostGIS, BaseSpatiaLite
from .db_status import TableTypes

from pepys_import import __version__
from pepys_import.utils.branding_util import (
    show_welcome_banner,
    show_software_meta_info,
)
import pepys_import.utils.value_transforming_utils as transformer
import pepys_import.utils.unit_utils as unit_converter
from .table_summary import TableSummary, TableSummarySet
from shapely import wkb

DEFAULT_DATA_PATH = os.path.join(PEPYS_IMPORT_DIRECTORY, "database", "default_data")
USER = getuser()  # Login name of the current user


class DataStore(object):
    """ Representation of database

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
        db_type="postgres",
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
                f"Unknown db_type {db_type} supplied, if specified should be one of 'postgres' or 'sqlite'"
            )

        # setup meta_class data
        self.meta_classes = {}
        self.setup_table_type_mapping()

        connection_string = "{}://{}:{}@{}:{}/{}".format(
            driver, db_username, db_password, db_host, db_port, db_name
        )
        self.engine = create_engine(connection_string, echo=False)

        if db_type == "postgres":
            BasePostGIS.metadata.bind = self.engine
        elif db_type == "sqlite":
            listen(self.engine, "connect", load_spatialite)
            BaseSpatiaLite.metadata.bind = self.engine

        self.missing_data_resolver = missing_data_resolver
        self.welcome_text = welcome_text
        self.show_status = show_status

        # caches of known data
        self.privacies = {}
        self.nationalities = {}
        self.datafile_types = {}
        self.datafiles = {}
        self.platform_types = {}
        self.platforms = {}
        self.sensor_types = {}
        self.sensors = {}
        self.comment_types = {}

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

        # dictionary, to cache comment type name
        self._comment_type_name_dict_on_comment_type_id = dict()

        # Branding Text
        if self.welcome_text:
            show_welcome_banner(welcome_text)
        if self.show_status:
            show_software_meta_info(__version__, self.db_type, self.db_name, db_host)
            # The 'pepys-import' banner is 61 characters wide, so making a line
            # of the same length makes things prettier
            print("-" * 61)

    def initialise(self):
        """Create schemas for the database
        """

        if self.db_type == "sqlite":
            try:
                # Create geometry_columns and spatial_ref_sys metadata table
                if not self.engine.dialect.has_table(self.engine, "spatial_ref_sys"):
                    with self.engine.connect() as conn:
                        conn.execute(select([func.InitSpatialMetaData(1)]))
                # Attempt to create schema if not present, to cope with fresh DB file
                BaseSpatiaLite.metadata.create_all(self.engine)
            except OperationalError:
                raise Exception(
                    f"Error creating database schema, possible invalid path? ('{self.db_name}'). Quitting"
                )
        elif self.db_type == "postgres":
            try:
                # Create schema pepys and extension for PostGIS first
                query = """
                    CREATE SCHEMA IF NOT EXISTS pepys;
                    CREATE EXTENSION IF NOT EXISTS postgis;
                    SET search_path = pepys,public;
                """
                with self.engine.connect() as conn:
                    conn.execute(query)
                BasePostGIS.metadata.create_all(self.engine)
            except OperationalError:
                raise Exception(f"Error creating database({self.db_name})! Quitting")

    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations."""
        db_session = sessionmaker(bind=self.engine)
        self.session = db_session()
        try:
            yield self
            self.session.commit()
        except:
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
                cls
                for name, cls in db_classes.items()
                if db_classes[name].table_type == table_type
            ]

    def populate_reference(self, reference_data_folder=None):
        """Import given CSV file to the given reference table"""
        self.add_to_changes(
            user=USER, modified=datetime.utcnow(), reason="Importing reference data"
        )

        if reference_data_folder is None:
            reference_data_folder = os.path.join(DEFAULT_DATA_PATH)

        files = os.listdir(reference_data_folder)

        reference_tables = []
        # Create reference table list
        self.setup_table_type_mapping()
        reference_table_objects = self.meta_classes[TableTypes.REFERENCE]
        for table_object in list(reference_table_objects):
            reference_tables.append(table_object.__tablename__)

        reference_files = [
            file
            for file in files
            if os.path.splitext(file)[0].replace(" ", "") in reference_tables
        ]
        import_from_csv(self, reference_data_folder, reference_files)

    def populate_metadata(self, sample_data_folder=None):
        """Import CSV files from the given folder to the related Metadata Tables"""
        self.add_to_changes(
            user=USER, modified=datetime.utcnow(), reason="Importing metadata data"
        )
        if sample_data_folder is None:
            sample_data_folder = os.path.join(DEFAULT_DATA_PATH)

        files = os.listdir(sample_data_folder)

        metadata_tables = []
        # Create metadata table list
        self.setup_table_type_mapping()
        metadata_table_objects = self.meta_classes[TableTypes.METADATA]
        for table_object in list(metadata_table_objects):
            metadata_tables.append(table_object.__tablename__)

        metadata_files = [
            file for file in files if os.path.splitext(file)[0] in metadata_tables
        ]
        import_from_csv(self, sample_data_folder, metadata_files)

    def populate_measurement(self, sample_data_folder=None):
        """Import CSV files from the given folder to the related Measurement Tables"""
        self.add_to_changes(
            user=USER, modified=datetime.utcnow(), reason="Importing measurement data"
        )
        if sample_data_folder is None:
            sample_data_folder = DEFAULT_DATA_PATH

        files = os.listdir(sample_data_folder)

        measurement_tables = []
        # Create measurement table list
        measurement_table_objects = self.meta_classes[TableTypes.MEASUREMENT]
        for table_object in list(measurement_table_objects):
            measurement_tables.append(table_object.__tablename__)

        measurement_files = [
            file for file in files if os.path.splitext(file)[0] in measurement_tables
        ]
        import_from_csv(self, sample_data_folder, measurement_files)

    # End of Data Store methods
    #############################################################

    def add_to_states(
        self,
        time,
        sensor,
        datafile,
        location=None,
        elevation=None,
        heading=None,
        course=None,
        speed=None,
        privacy=None,
    ):
        """
        Adds the specified state to the :class:`State` table if not already present.

        :param time: Timestamp of :class:`State`
        :type time: datetime
        :param sensor: Sensor of :class:`State`
        :type sensor: Sensor
        :param datafile: Datafile of :class:`State`
        :type datafile: Datafile
        :param location: Location of :class:`State`
        :type location: Point
        :param elevation: Elevation of :class:`State` (use negative for depth)
        :type elevation: String
        :param heading: Heading of :class:`State` (Which converted to radians)
        :type heading: String
        :param course: Course of :class:`State`
        :type course:
        :param speed: Speed of :class:`State` (Which converted to m/sec)
        :type speed: String
        :param privacy: :class:`Privacy` of :class:`State`
        :type privacy: Privacy
        :return: Created :class:`State` entity
        :rtype: State
        """
        if type(time) == str:
            # TODO we can't assume the time is in this format. We should throw
            # exception if time isn't of type datetime
            time = datetime.strptime(time, "%Y-%m-%d %H:%M:%S")

        sensor = self.search_sensor(sensor)
        datafile = self.search_datafile(datafile)
        privacy = self.search_privacy(privacy)

        if sensor is None or datafile is None:
            raise Exception(f"There is missing value(s) in '{sensor}, {datafile}'!")

        if elevation == "":
            elevation = None
        if heading == "":
            heading = None
        if course == "":
            course = None
        if speed == "":
            speed = None

        state_obj = self.db_classes.State(
            time=time,
            sensor_id=sensor.sensor_id,
            location=location,
            elevation=elevation,
            heading=heading,
            course=course,
            speed=speed,
            source_id=datafile.datafile_id,
            privacy_id=privacy.privacy_id,
        )
        self.session.add(state_obj)
        self.session.flush()

        return state_obj

    def add_to_sensors(self, name, sensor_type, host):
        """
        Adds the specified sensor to the :class:`Sensor` table if not already present.

        :param name: Name of sensor
        :type name: String
        :param sensor_type: Type of sensor
        :type sensor_type: :class:`SensorType`
        :param host: Platform of sensor
        :type host: Platform
        :return: Created Sensor entity
        """
        sensor_type = self.search_sensor_type(sensor_type)
        host = self.search_platform(host)

        if sensor_type is None or host is None:
            raise Exception(f"There is missing value(s) in '{sensor_type}, {host}'!")

        sensor_obj = self.db_classes.Sensor(
            name=name, sensor_type_id=sensor_type.sensor_type_id, host=host.platform_id,
        )
        self.session.add(sensor_obj)
        self.session.flush()

        return sensor_obj

    def add_to_datafiles(
        self, privacy, file_type, reference=None, simulated=False, url=None
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
        :param url: URL of datafile
        :type url: String
        :return: Created :class:`Datafile` entity
        :rtype: Datafile
        """
        datafile_type = self.search_datafile_type(file_type)
        privacy = self.search_privacy(privacy)

        datafile_obj = self.db_classes.Datafile(
            simulated=bool(simulated),
            privacy_id=privacy.privacy_id,
            datafile_type_id=datafile_type.datafile_type_id,
            reference=reference,
            url=url,
        )

        self.session.add(datafile_obj)
        self.session.flush()

        print(f"'{reference}' added to Datafile!")
        # add to cache and return created datafile
        self.datafiles[reference] = datafile_obj

        return datafile_obj

    def add_to_platforms(
        self,
        name,
        nationality,
        platform_type,
        privacy,
        trigraph=None,
        quadgraph=None,
        pennant_number=None,
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
        :param pennant_number: Pennant number of :class:`Platform`
        :type pennant_number: String
        :return: Created Platform entity
        :rtype: Platform
        """
        nationality = self.search_nationality(nationality)
        platform_type = self.search_platform_type(platform_type)
        privacy = self.search_privacy(privacy)

        platform_obj = self.db_classes.Platform(
            name=name,
            trigraph=trigraph,
            quadgraph=quadgraph,
            pennant=pennant_number,
            nationality_id=nationality.nationality_id,
            platform_type_id=platform_type.platform_type_id,
            privacy_id=privacy.privacy_id,
        )

        self.session.add(platform_obj)
        self.session.flush()

        print(f"'{name}' added to Platform!")
        # add to cache and return created platform
        self.platforms[name] = platform_obj

        return platform_obj

    def add_to_synonyms(self, table, name, entity):
        # enough info to proceed and create entry
        synonym = self.db_classes.Synonym(table=table, synonym=name, entity=entity)
        self.session.add(synonym)
        self.session.flush()

        return synonym

    #############################################################
    # Search/lookup functions

    def get_datafile_from_id(self, datafile_id):
        """Search for datafile with this id"""
        return (
            self.session.query(self.db_classes.Datafile)
            .filter(self.db_classes.Datafile.datafile_id == datafile_id)
            .first()
        )

    def search_datafile_type(self, name):
        """Search for any datafile type with this name"""
        return (
            self.session.query(self.db_classes.DatafileType)
            .filter(self.db_classes.DatafileType.name == name)
            .first()
        )

    def search_datafile(self, name):
        """Search for any datafile with this name"""
        return (
            self.session.query(self.db_classes.Datafile)
            .filter(self.db_classes.Datafile.reference == name)
            .first()
        )

    def search_platform(self, name):
        """Search for any platform with this name"""
        return (
            self.session.query(self.db_classes.Platform)
            .filter(self.db_classes.Platform.name == name)
            .first()
        )

    def search_platform_type(self, name):
        """Search for any platform type with this name"""
        return (
            self.session.query(self.db_classes.PlatformType)
            .filter(self.db_classes.PlatformType.name == name)
            .first()
        )

    def search_nationality(self, name):
        """Search for any nationality with this name"""
        return (
            self.session.query(self.db_classes.Nationality)
            .filter(self.db_classes.Nationality.name == name)
            .first()
        )

    def search_sensor(self, name):
        """Search for any sensor type featuring this name"""
        return (
            self.session.query(self.db_classes.Sensor)
            .filter(self.db_classes.Sensor.name == name)
            .first()
        )

    def search_sensor_type(self, name):
        """Search for any sensor type featuring this name"""
        return (
            self.session.query(self.db_classes.SensorType)
            .filter(self.db_classes.SensorType.name == name)
            .first()
        )

    def search_privacy(self, name):
        """Search for any privacy with this name"""
        return (
            self.session.query(self.db_classes.Privacy)
            .filter(self.db_classes.Privacy.name == name)
            .first()
        )

    #############################################################
    # New methods
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
                self.db_classes.Synonym.synonym == name,
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
        datafile = (
            self.session.query(self.db_classes.Datafile)
            .filter(self.db_classes.Datafile.reference == datafile_name)
            .first()
        )
        if datafile:
            return datafile

        # Datafile is not found, try to find a synonym
        return self.synonym_search(
            name=datafile_name,
            table=self.db_classes.Datafile,
            pk_field=self.db_classes.Datafile.datafile_id,
        )

    def get_datafile(self, datafile_name=None, datafile_type=None):
        """
        Adds an entry to the datafiles table of the specified name (path)
        and type if not already present. It uses find_datafile method to search existing datafiles.

        :param datafile_name:  Name of Datafile
        :type datafile_name: String
        :param datafile_type: Type of Datafile
        :type datafile_type: DatafileType
        :return:  Created Datafile entity
        :rtype: Datafile
        """

        # Check for name match in Datafile and Synonym Tables
        if datafile_name:
            datafile = self.find_datafile(datafile_name=datafile_name)
            if datafile:
                # found object should be initialised because of _measurement variable
                datafile.__init__()
                return datafile

        resolved_data = self.missing_data_resolver.resolve_datafile(
            self, datafile_name, datafile_type, None
        )
        # It means that new datafile added as a synonym and existing datafile returned
        if isinstance(resolved_data, self.db_classes.Datafile):
            return resolved_data

        datafile_name, datafile_type, privacy = resolved_data

        assert isinstance(
            datafile_type, self.db_classes.DatafileType
        ), "Type error for DatafileType entity"
        assert isinstance(
            privacy, self.db_classes.Privacy
        ), "Type error for Privacy entity"

        return self.add_to_datafiles(
            simulated=False,
            privacy=privacy.name,
            file_type=datafile_type.name,
            reference=datafile_name,
        )

    def find_platform(self, platform_name):
        """
        This method tries to find a Platform entity with the given platform_name. If it
        finds, it returns the entity. If it is not found, it searches synonyms.

        :param platform_name: Name of :class:`Platform`
        :type platform_name: String
        :return:
        """
        platform = (
            self.session.query(self.db_classes.Platform)
            .filter(
                or_(
                    self.db_classes.Platform.name == platform_name,
                    self.db_classes.Platform.trigraph == platform_name,
                    self.db_classes.Platform.quadgraph == platform_name,
                )
            )
            .first()
        )
        if platform:
            return platform

        # Platform is not found, try to find a synonym
        return self.synonym_search(
            name=platform_name,
            table=self.db_classes.Platform,
            pk_field=self.db_classes.Platform.platform_id,
        )

    def get_platform(
        self,
        platform_name=None,
        nationality=None,
        platform_type=None,
        privacy=None,
        trigraph=None,
        quadgraph=None,
        pennant_number=None,
    ):
        """
        Adds an entry to the platforms table for the specified platform
        if not already present. It uses find_platform method to search existing platforms.

        :param platform_name: Name of :class:`Platform`
        :type platform_name: String
        :param nationality: Name of :class:`Nationality`
        :type nationality: Nationality
        :param platform_type: Name of :class:`PlatformType`
        :type platform_type: PlatformType
        :param privacy: Name of :class:`Privacy`
        :type privacy: Privacy
        :param trigraph: Trigraph of :class:`Platform`
        :type trigraph: String
        :param quadgraph: Quadgraph of :class:`Platform`
        :type quadgraph: String
        :param pennant_number: Pennant number of :class:`Platform`
        :type pennant_number: String
        :return: Created Platform entity
        """

        # Check for name match in Platform and Synonym Tables
        if platform_name:
            platform = self.find_platform(platform_name)
            if platform:
                return platform

        nationality = self.search_nationality(nationality)
        platform_type = self.search_platform_type(platform_type)
        privacy = self.search_privacy(privacy)

        if (
            platform_name is None
            or nationality is None
            or platform_type is None
            or privacy is None
        ):
            resolved_data = self.missing_data_resolver.resolve_platform(
                self, platform_name, platform_type, nationality, privacy
            )
            # It means that new platform added as a synonym and existing platform returned
            if isinstance(resolved_data, self.db_classes.Platform):
                return resolved_data
            elif len(resolved_data) == 7:
                (
                    platform_name,
                    trigraph,
                    quadgraph,
                    pennant_number,
                    platform_type,
                    nationality,
                    privacy,
                ) = resolved_data

        assert isinstance(
            nationality, self.db_classes.Nationality
        ), "Type error for Nationality entity"
        assert isinstance(
            platform_type, self.db_classes.PlatformType
        ), "Type error for PlatformType entity"
        assert isinstance(
            privacy, self.db_classes.Privacy
        ), "Type error for Privacy entity"

        return self.add_to_platforms(
            name=platform_name,
            trigraph=trigraph,
            quadgraph=quadgraph,
            pennant_number=pennant_number,
            nationality=nationality.name,
            platform_type=platform_type.name,
            privacy=privacy.name,
        )

    def get_status(
        self,
        report_measurement: bool = False,
        report_metadata: bool = False,
        report_reference: bool = False,
    ):
        """
        Provides a summary of the contents of the :class:`DataStore`.

        :param report_measurement: Boolean flag includes Metadata Tables
        :type report_measurement: Boolean
        :param report_metadata: Boolean flag includes Metadata Tables
        :type report_metadata: Boolean
        :param report_reference: Boolean flag includes Metadata Tables
        :type report_reference: Boolean
        :return: The summary of the contents of the :class:`DataStore`
        :rtype: TableSummarySet
        """

        table_summaries = []
        if report_measurement:
            # Create measurement table list
            measurement_table_objects = self.meta_classes[TableTypes.MEASUREMENT]
            for table_object in list(measurement_table_objects):
                ts = TableSummary(self.session, table_object)
                table_summaries.append(ts)

        if report_metadata:
            # Create metadata table list
            metadata_table_objects = self.meta_classes[TableTypes.METADATA]
            for table_object in list(metadata_table_objects):
                ts = TableSummary(self.session, table_object)
                table_summaries.append(ts)

        if report_reference:
            # Create reference table list
            reference_table_objects = self.meta_classes[TableTypes.REFERENCE]
            for table_object in list(reference_table_objects):
                ts = TableSummary(self.session, table_object)
                table_summaries.append(ts)

        table_summaries_set = TableSummarySet(table_summaries)

        return table_summaries_set

    def search_comment_type(self, name):
        """Search for any comment type featuring this name"""
        return (
            self.session.query(self.db_classes.CommentType)
            .filter(self.db_classes.CommentType.name == name)
            .first()
        )

    def add_to_comment_types(self, name):
        """
        Adds the specified comment type to the CommentType table if not already present

        :param name: Name of :class:`CommentType`
        :type name: String
        :return: Created entity of :class:`CommentType` table
        :rtype: CommentType
        """

        # check in cache for comment type
        if name in self.comment_types:
            return self.comment_types[name]

        # doesn't exist in cache, try to lookup in DB
        comment_types = self.search_comment_type(name)
        if comment_types:
            # add to cache and return looked up platform type
            self.comment_types[name] = comment_types
            return comment_types

        # enough info to proceed and create entry
        comment_type = self.db_classes.CommentType(name=name)
        self.session.add(comment_type)
        self.session.flush()

        # add to cache and return created platform type
        self.comment_types[name] = comment_type

        return comment_type

    # End of Measurements
    #############################################################
    # Reference Type Maintenance

    def add_to_platform_types(self, platform_type_name):
        """
        Adds the specified platform type to the platform types table if not already
        present.

        :param platform_type_name: Name of :class:`PlatformType`
        :type platform_type_name: String
        :return: Created :class:`PlatformType` entity
        :rtype: PlatformType
        """
        # check in cache for nationality
        if platform_type_name in self.platform_types:
            return self.platform_types[platform_type_name]

        # doesn't exist in cache, try to lookup in DB
        platform_types = self.search_platform_type(platform_type_name)
        if platform_types:
            # add to cache and return looked up platform type
            self.platform_types[platform_type_name] = platform_types
            return platform_types

        # enough info to proceed and create entry
        platform_type = self.db_classes.PlatformType(name=platform_type_name)
        self.session.add(platform_type)
        self.session.flush()

        # add to cache and return created platform type
        self.platform_types[platform_type_name] = platform_type

        return platform_type

    def add_to_nationalities(self, nationality_name):
        """
        Adds the specified nationality to the nationalities table if not already present

        :param nationality_name: Name of :class:`Nationality`
        :type nationality_name: String
        :return: Created :class:`Nationality` entity
        :rtype: Nationality
        """
        # check in cache for nationality
        if nationality_name in self.nationalities:
            return self.nationalities[nationality_name]

        # doesn't exist in cache, try to lookup in DB
        nationalities = self.search_nationality(nationality_name)
        if nationalities:
            # add to cache and return looked up nationality
            self.nationalities[nationality_name] = nationalities
            return nationalities

        # enough info to proceed and create entry
        nationality = self.db_classes.Nationality(name=nationality_name)
        self.session.add(nationality)
        self.session.flush()

        # add to cache and return created platform
        self.nationalities[nationality_name] = nationality

        return nationality

    def add_to_privacies(self, privacy_name):
        """
        Adds the specified privacy entry to the :class:`Privacy` table if not already present.

        :param privacy_name: Name of :class:`Privacy`
        :type privacy_name: String
        :return: Created :class:`Privacy` entity
        :rtype: Privacy
        """
        # check in cache for privacy
        if privacy_name in self.privacies:
            return self.privacies[privacy_name]

        # doesn't exist in cache, try to lookup in DB
        privacies = self.search_privacy(privacy_name)
        if privacies:
            # add to cache and return looked up platform
            self.privacies[privacy_name] = privacies
            return privacies

        # enough info to proceed and create entry
        privacy = self.db_classes.Privacy(name=privacy_name)
        self.session.add(privacy)
        self.session.flush()

        # add to cache and return created platform
        self.privacies[privacy_name] = privacy

        return privacy

    def add_to_datafile_types(self, datafile_type):
        """
        Adds the specified datafile type to the datafile types table if not already
        present.

        :param datafile_type: Name of :class:`DatafileType`
        :type datafile_type: String
        :return: Wrapped database entity for :class:`DatafileType`
        :rtype: DatafileType
        """
        # check in cache for datafile type
        if datafile_type in self.datafile_types:
            return self.datafile_types[datafile_type]

        # doesn't exist in cache, try to lookup in DB
        datafile_types = self.search_datafile_type(datafile_type)
        if datafile_types:
            # add to cache and return looked up datafile type
            self.datafile_types[datafile_type] = datafile_types
            return datafile_types

        # proceed and create entry
        datafile_type_obj = self.db_classes.DatafileType(name=datafile_type)

        self.session.add(datafile_type_obj)
        self.session.flush()

        # add to cache and return created datafile type
        self.datafile_types[datafile_type] = datafile_type_obj

        return datafile_type_obj

    def add_to_sensor_types(self, sensor_type_name):
        """
        Adds the specified sensor type to the :class:`SensorType` table if not already present.

        :param sensor_type_name: Name of :class:`SensorType`
        :type sensor_type_name: String
        :return: Created :class:`SensorType` entity
        :rtype: SensorType
        """
        # check in cache for sensor type
        if sensor_type_name in self.sensor_types:
            return self.sensor_types[sensor_type_name]

        # doesn't exist in cache, try to lookup in DB
        sensor_types = self.search_sensor_type(sensor_type_name)
        if sensor_types:
            # add to cache and return looked up sensor type
            self.sensor_types[sensor_type_name] = sensor_types
            return sensor_types

        # enough info to proceed and create entry
        sensor_type = self.db_classes.SensorType(name=sensor_type_name)
        self.session.add(sensor_type)
        self.session.flush()

        # add to cache and return created sensor type
        self.sensor_types[sensor_type_name] = sensor_type

        return sensor_type

    # End of References
    #############################################################
    # Metadata Maintenance

    def add_to_logs(self, table, row_id, field=None, new_value=None, change_id=None):
        """
        Adds the specified event to the :class:`Logs`table if not already present.

        :param table: Name of the table
        :param row_id: Entity ID of the tale
        :param field:  Name of the field
        :param new_value:  New value of the field
        :param change_id:  Row ID of entity of :class:`Changes` about the change
        :return: Created :class:`Logs` entity
        """
        log = self.db_classes.Log(
            table=table,
            id=row_id,
            field=field,
            new_value=new_value,
            change_id=change_id,
        )
        self.session.add(log)
        self.session.flush()

        return log

    def add_to_changes(self, user, modified, reason):
        """
        Adds the specified event to the :class:`Change`table if not already present.

        :param user: Username of the current login
        :param modified: Change date
        :param reason:  Reason of the change
        :return: Created :class:`Change` entity
        """
        change = self.db_classes.Change(user=user, modified=modified, reason=reason,)
        self.session.add(change)
        self.session.flush()

        return change

    # End of Metadata Maintenance
    #############################################################

    def clear_db(self):
        """Delete records of all database tables"""
        if self.db_type == "sqlite":
            meta = BaseSpatiaLite.metadata
        else:
            meta = BasePostGIS.metadata

        with self.session_scope():
            for table in reversed(meta.sorted_tables):
                self.session.execute(table.delete())

    def get_all_datafiles(self):
        """
        Gets all datafiles.

        :return: Datafile entity
        :rtype: Datafile
        """
        datafiles = self.session.query(self.db_classes.Datafile).all()
        return datafiles

    def get_cached_comment_type_name(self, comment_type_id):
        """
        Get comment type name from cache on either "comment_type_id"
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
                self._comment_type_name_dict_on_comment_type_id[
                    comment_type_id
                ] = comment_type.name
                return comment_type.name
            else:
                raise Exception(
                    "No Comment Type found with Comment type id: {}".format(
                        comment_type_id
                    )
                )

    def get_cached_platform_name(self, sensor_id=None, platform_id=None):
        """
        Get platform name from cache on either "sensor_id" or "platform_id"
        If name is not found in the cache, sytem will load from this data store,
        and add it into cache.
        """
        # invalid parameter handling
        if sensor_id is None and platform_id is None:
            raise Exception(
                'either "sensor_id" or "platform_id" has to be provided to get "platform name"'
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
                raise Exception("No sensor found with sensor id: {}".format(sensor_id))

        if platform_id:
            # return from cache
            if platform_id in self._platform_dict_on_platform_id:
                return self._platform_dict_on_platform_id[platform_id]
            platform = (
                self.session.query(self.db_classes.Sensor)
                .filter(self.db_classes.Sensor.sensor_id == sensor_id)
                .first()
            )

            if platform:
                self._platform_dict_on_platform_id[platform_id] = platform.name
                if sensor_id:
                    self._platform_dict_on_sensor_id[sensor_id] = platform.name
            else:
                raise Exception(
                    "No Platform found with platform id: {}".format(platform_id)
                )
        return platform.name

    def export_datafile(self, datafile_id, datafile):
        """
        Get states, contacts and comments based on Datafile ID.

        :param datafile_id:  ID of Datafile
        :type datafile_id: String
        """
        f = open("{}.rep".format(datafile), "w+")
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

        line_number = 0
        for i, state in enumerate(states):
            line_number += 1
            #  load platform name from cache.
            try:
                platform_name = self.get_cached_platform_name(sensor_id=state.sensor_id)
            except Exception as ex:
                print(str(ex))
                platform_name = "[Not Found]"

            # wkb hex conversion to "point"
            point = wkb.loads(state.location.desc, hex=True)
            state_rep_line = [
                transformer.format_datatime(state.time),
                '"' + platform_name + '"',
                "AA",
                transformer.format_point(point.x, point.y),
                str(unit_converter.convert_radian_to_degree(state.heading))
                if state.heading
                else "0",
                str(unit_converter.convert_mps_to_knot(state.speed))
                if state.speed
                else "0",
                str(abs(state.elevation)) if state.elevation else "NaN",
            ]
            data = " ".join(state_rep_line)
            f.write(data + "\r\n")

        # for contact in contacts:
        #     sensor = self.session.query(self.db_classes.Sensor).filter(
        #         self.db_classes.Sensor.sensor_id == contact.sensor_id
        #     ).first()
        # print(sensor.name)

        for i, comment in enumerate(comments):
            platform = (
                self.session.query(self.db_classes.Sensor)
                .filter(self.db_classes.Platform.platform_id == comment.platform_id)
                .first()
            )
            vessel_name = platform.name
            message = comment.content
            comment_type_name = self.get_cached_comment_type_name(
                comment.comment_type_id
            )

            comment_rep_line = [
                transformer.format_datatime(comment.time),
                vessel_name,
                comment_type_name,
                message,
            ]

            if comment_type_name == "None":
                comment_rep_line.insert(0, ";NARRATIVE:")
                del comment_rep_line[3]
            else:
                comment_rep_line.insert(0, ";NARRATIVE2:")

            data = " ".join(comment_rep_line)
            f.write(data + "\r\n")
        f.close()
