import csv
import os
from pathlib import Path

from tabulate import tabulate
from datetime import datetime
from sqlalchemy import create_engine, event
from sqlalchemy.event import listen
from sqlalchemy.schema import CreateSchema
from sqlalchemy.sql import select, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from importlib import import_module
from contextlib import contextmanager

from pepys_import.resolvers.default_resolver import DefaultResolver
from pepys_import.utils.data_store_utils import import_from_csv
from pepys_import.utils.geoalchemy_utils import load_spatialite
from .db_base import base_postgres, base_sqlite
from .db_status import TableTypes
from pepys_import.core.formats import unit_registry
from pepys_import.core.formats.state2 import State2

from pepys_import import __version__
from pepys_import.utils.branding_util import (
    show_welcome_banner,
    show_software_meta_info,
)
from .table_summary import table_summary

MAIN_DIRECTORY_PATH = Path(__file__).parent.parent.parent  # pepys_import/pepys_import
DEFAULT_DATA_PATH = os.path.join(MAIN_DIRECTORY_PATH, "database", "default_data")

# TODO: add foreign key refs
# TODO: add proper uuid funcs that interact with entries table

# TODO: probably move this module to the top level as it's the main one


class DataStore:
    """ Representation of database


    Returns:
        DataStore -- the data store
    """

    # TODO: supply or lookup user id
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
        show_welcome=True,
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
            base_postgres.metadata.bind = self.engine
        elif db_type == "sqlite":
            listen(self.engine, "connect", load_spatialite)
            base_sqlite.metadata.bind = self.engine

        self.missing_data_resolver = missing_data_resolver
        self.show_welcome = show_welcome
        self.show_status = show_status

        # caches of known data
        self.table_types = {}
        self.privacies = {}
        self.nationalities = {}
        self.datafile_types = {}
        self.datafiles = {}
        self.platform_types = {}
        self.platforms = {}
        self.sensor_types = {}
        self.sensors = {}

        # TEMP list of values for defaulted IDs, to be replaced by missing info lookup mechanism
        self.default_user_id = 1  # DevUser

        # Instance attributes which are necessary for initialise method
        self.db_name = db_name
        self.db_type = db_type

        # use session_scope() to create a new session
        self.session = None

        # Branding Text
        if self.show_welcome:
            show_welcome_banner()
        if self.show_status:
            show_software_meta_info(__version__, self.db_type, self.db_name, db_host)
            print("---------------------------------")

    def initialise(self):
        """Create schemas for the database
        """

        if self.db_type == "sqlite":
            try:
                # Create geometry_columns and spatial_ref_sys metadata table
                with self.engine.connect() as conn:
                    conn.execute(select([func.InitSpatialMetaData()]))
                # Attempt to create schema if not present, to cope with fresh DB file
                base_sqlite.metadata.create_all(self.engine)
            except OperationalError:
                print(
                    "Error creating database schema, possible invalid path? ('"
                    + self.db_name
                    + "'). Quitting"
                )
                exit()
        elif self.db_type == "postgres":
            try:
                # Create extension for PostGIS first
                with self.engine.connect() as conn:
                    conn.execute("CREATE EXTENSION postgis;")
                #  ensure that create schema scripts created before create table scripts
                event.listen(
                    base_postgres.metadata,
                    "before_create",
                    CreateSchema("datastore_schema"),
                )
                base_postgres.metadata.create_all(self.engine)
            except OperationalError:
                print(f"Error creating database({self.db_name})! Quitting")
                exit()

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
    def get_datafiles(self):
        # get list of all datafiles in the DB
        return self.session.query(self.db_classes.Datafiles).all()

    def get_platforms(self):
        # get list of all platforms in the DB
        return self.session.query(self.db_classes.Platforms).all()

    def setup_table_type_mapping(self):
        # setup a map of tables keyed by TableType
        db_classes = dict(
            [
                (name, cls)
                for name, cls in self.db_classes.__dict__.items()
                if isinstance(cls, type)
                and (issubclass(cls, base_postgres) or issubclass(cls, base_sqlite))
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
        if reference_data_folder is None:
            reference_data_folder = os.path.join("..", "default_data")

        files = os.listdir(reference_data_folder)

        reference_tables = []
        # Create reference table list
        with self.session_scope() as session:
            self.setup_table_type_mapping()
            reference_table_objects = self.meta_classes[TableTypes.REFERENCE]
            for table_object in list(reference_table_objects):
                reference_tables.append(table_object.__tablename__)

        reference_files = [
            file
            for file in files
            if os.path.splitext(file)[0].replace(" ", "") in reference_tables
        ]
        for file in reference_files:
            # split file into filename and extension
            table_name, _ = os.path.splitext(file)
            possible_method = "add_to_" + table_name.lower().replace(" ", "_")
            method_to_call = getattr(self, possible_method, None)
            if method_to_call:
                with open(os.path.join(reference_data_folder, file), "r") as f:
                    reader = csv.reader(f)
                    # skip header
                    _ = next(reader)
                    with self.session_scope() as session:
                        for row in reader:
                            method_to_call(*row)
            else:
                print(f"Method({possible_method}) not found!")

    def populate_metadata(self, sample_data_folder=None):
        """Import CSV files from the given folder to the related Metadata Tables"""
        if sample_data_folder is None:
            sample_data_folder = os.path.join("..", "default_data")

        files = os.listdir(sample_data_folder)

        metadata_tables = []
        # Create metadata table list
        with self.session_scope() as session:
            self.setup_table_type_mapping()
            metadata_table_objects = self.meta_classes[TableTypes.METADATA]
            for table_object in list(metadata_table_objects):
                metadata_tables.append(table_object.__tablename__)

        metadata_files = [
            file for file in files if os.path.splitext(file)[0] in metadata_tables
        ]
        for file in sorted(metadata_files):
            # split file into filename and extension
            table_name, _ = os.path.splitext(file)
            possible_method = "add_to_" + table_name.lower().replace(" ", "_")
            method_to_call = getattr(self, possible_method, None)
            if method_to_call:
                with open(os.path.join(sample_data_folder, file), "r") as f:
                    reader = csv.reader(f)
                    # skip header
                    _ = next(reader)
                    with self.session_scope() as session:
                        for row in reader:
                            method_to_call(*row)
            else:
                print(f"Method({possible_method}) not found!")

    def populate_measurement(self, sample_data_folder=None):
        """Import CSV files from the given folder to the related Measurement Tables"""
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

    def add_to_entries(self, table_type_id, table_name):
        # ensure table type exists to satisfy foreign key constraint
        self.add_to_table_types(table_type_id, table_name)

        # No cache for entries, just add new one when called
        entry_obj = self.db_classes.Entry(
            table_type_id=table_type_id, created_user=self.default_user_id
        )

        self.session.add(entry_obj)
        self.session.flush()

        return entry_obj.entry_id

    def add_to_datafile_from_rep(self, datafile_name, datafile_type):
        # check in cache for datafile
        if datafile_name in self.datafiles:
            return self.datafiles[datafile_name]

        # doesn't exist in cache, try to lookup in DB
        datafiles = self.search_datafile(datafile_name)
        if datafiles:
            # add to cache and return looked up datafile
            self.datafiles[datafile_name] = datafiles
            return datafiles

        datafile_type_obj = self.search_datafile_type(datafile_type)
        if datafile_type_obj is None:
            datafile_type_obj = self.add_to_datafile_types(datafile_type)

        # don't know privacy, use resolver to query for data
        privacy = self.missing_data_resolver.resolve_privacy(
            self,
            self.db_classes.Datafiles.table_type_id,
            self.db_classes.Datafiles.__tablename__,
        )

        # privacy should contain (tabletype, privacy_name)
        # enough info to proceed and create entry
        _, privacy = privacy
        entry_id = self.add_to_entries(
            self.db_classes.Datafiles.table_type_id,
            self.db_classes.Datafiles.__tablename__,
        )

        datafile_obj = self.db_classes.Datafiles(
            datafile_id=entry_id,
            simulated=False,
            reference=datafile_name,
            url=None,
            privacy_id=privacy.privacy_id,
            datafile_type_id=datafile_type_obj.datafile_type_id,
        )

        self.session.add(datafile_obj)
        self.session.flush()

        self.datafiles[datafile_name] = datafile_obj
        # should return DB type or something else decoupled from DB?
        return datafile_obj

    def add_to_platforms_from_rep(
        self, platform_name, platform_type, nationality, privacy
    ):
        # check in cache for platform
        # if platform_name in self.platforms:
        #     return self.platforms[platform_name]

        # doesn't exist in cache, try to lookup in DB
        platforms = self.search_platform(platform_name)
        if platforms:
            # add to cache and return looked up platform
            self.platforms[platform_name] = platforms
            return platforms

        # doesn't exist in DB, use resolver to query for data
        platform = self.missing_data_resolver.resolve_platform(
            self, platform_name, platform_type, nationality, privacy
        )

        # platform should contain (platform_name, platform_type, nationality)
        # enough info to proceed and create entry
        _, platform_type, nationality, privacy = platform
        entry_id = self.add_to_entries(
            self.db_classes.Platforms.table_type_id,
            self.db_classes.Platforms.__tablename__,
        )

        platform_obj = self.db_classes.Platforms(
            platform_id=entry_id,
            name=platform_name,
            nationality_id=nationality.nationality_id,
            platform_type_id=platform_type.platform_type_id,
            privacy_id=privacy.privacy_id,
        )

        self.session.add(platform_obj)
        self.session.flush()

        # add to cache and return created platform
        self.platforms[platform_name] = platform_obj
        # should return DB type or something else decoupled from DB?
        return platform_obj

    def add_to_sensors_from_rep(self, sensor_name, platform):
        # check in cache for sensor
        # if sensor_name in self.sensors:
        #     return self.sensors[sensor_name]

        # doesn't exist in cache, try to lookup in DB
        sensors = self.search_sensor(sensor_name)
        if sensors:
            # add to cache and return looked up sensor
            self.sensors[sensor_name] = sensors
            return sensors

        # doesn't exist in DB, use resolver to query for data
        sensor = self.missing_data_resolver.resolve_sensor(self, sensor_name)

        # sensor should contain (sensor_name, sensorType)
        # enough info to proceed and create entry
        _, sensor_type = sensor
        entry_id = self.add_to_entries(
            self.db_classes.Sensors.table_type_id, self.db_classes.Sensors.__tablename__
        )

        sensor_obj = self.db_classes.Sensors(
            sensor_id=entry_id,
            name=sensor_name,
            sensor_type_id=self.db_classes.map_uuid_type(sensor_type.sensor_type_id),
            platform_id=self.db_classes.map_uuid_type(platform.platform_id),
        )

        self.session.add(sensor_obj)
        self.session.flush()

        # add to cache and return created sensor
        self.sensors[sensor_name] = sensor_obj
        # should return DB type or something else decoupled from DB?
        return sensor_obj

    def add_state_to_states(self, state: State2, data_file, sensor):
        # No cache for entries, just add new one when called

        # don't know privacy, use resolver to query for data
        privacy = self.missing_data_resolver.resolve_privacy(
            self,
            self.db_classes.State.table_type_id,
            self.db_classes.State.__tablename__,
        )

        # privacy should contain (table_type, privacy_name)
        # enough info to proceed and create entry
        _, privacy = privacy
        entry_id = self.add_to_entries(
            self.db_classes.State.table_type_id, self.db_classes.State.__tablename__
        )

        state_obj = self.db_classes.State(
            state_id=entry_id,
            time=state.get_timestamp(),
            sensor_id=sensor.sensor_id,
            location=str(state.get_location()),
            heading=state.get_heading().to(unit_registry.radians).magnitude,
            speed=state.get_speed()
            .to(unit_registry.meter / unit_registry.second)
            .magnitude,
            datafile_id=data_file.datafile_id,
            privacy_id=privacy.privacy_id,
        )
        self.session.add(state_obj)
        self.session.flush()

        return state_obj

    def add_to_states_from_rep(
        self, timestamp, datafile, sensor, location, heading, speed
    ):
        # No cache for entries, just add new one when called

        # don't know privacy, use resolver to query for data
        privacy = self.missing_data_resolver.resolve_privacy(
            self,
            self.db_classes.States.table_type_id,
            self.db_classes.States.__tablename__,
        )

        # privacy should contain (table_type, privacy_name)
        # enough info to proceed and create entry
        _, privacy = privacy
        entry_id = self.add_to_entries(
            self.db_classes.States.table_type_id, self.db_classes.States.__tablename__
        )

        # heading is a quantity. Convert to radians
        heading_rads = heading.to(unit_registry.radians).magnitude

        # speed is a quantity. Convert to m/sec
        speed_m_sec = speed.to(unit_registry.meter / unit_registry.second).magnitude

        state_obj = self.db_classes.States(
            state_id=entry_id,
            time=timestamp,
            sensor_id=sensor.sensor_id,
            location=str(location),
            heading=heading_rads,
            speed=speed_m_sec,
            datafile_id=datafile.datafile_id,
            privacy_id=privacy.privacy_id,
        )
        self.session.add(state_obj)
        self.session.flush()

        return state_obj

    def add_to_states(
        self,
        time,
        sensor,
        datafile,
        location=None,
        heading=None,
        course=None,
        speed=None,
        privacy=None,
    ):
        time = datetime.strptime(time, "%Y-%m-%d %H:%M:%S")

        sensor = self.search_sensor(sensor)
        datafile = self.search_datafile(datafile)
        privacy = self.search_privacy(privacy)

        if sensor is None or datafile is None:
            print(f"There is missing value(s) in '{sensor}, {datafile}'!")
            return

        heading_rads = None
        if heading:
            # heading is a string, turn into quantity. Convert to radians
            heading_quantity = float(heading) * unit_registry.knot
            heading_rads = heading_quantity.to(unit_registry.radians).magnitude

        speed_m_sec = None
        if speed:
            # speed is a string, turn into quantity. Convert to m/sec
            speed_quantity = float(speed) * unit_registry.knot
            speed_m_sec = speed_quantity.to(
                unit_registry.meter / unit_registry.second
            ).magnitude

        entry_id = self.add_to_entries(
            self.db_classes.States.table_type_id, self.db_classes.States.__tablename__
        )
        state_obj = self.db_classes.States(
            state_id=entry_id,
            time=time,
            sensor_id=sensor.sensor_id,
            location=location,
            heading=heading_rads,
            # course=course,
            speed=speed_m_sec,
            source_id=datafile.datafile_id,
            privacy_id=privacy.privacy_id,
        )
        self.session.add(state_obj)
        self.session.flush()

        return state_obj

    def add_to_sensors(self, name, sensor_type, host):
        sensor_type = self.search_sensor_type(sensor_type)
        host = self.search_platform(host)

        if sensor_type is None or host is None:
            print(f"There is missing value(s) in '{sensor_type}, {host}'!")
            return

        entry_id = self.add_to_entries(
            self.db_classes.Sensors.table_type_id, self.db_classes.Sensors.__tablename__
        )

        sensor_obj = self.db_classes.Sensors(
            sensor_id=entry_id,
            name=name,
            sensor_type_id=sensor_type.sensor_type_id,
            platform_id=host.platform_id,
        )
        self.session.add(sensor_obj)
        self.session.flush()

        return sensor_obj

    def add_to_datafiles(self, simulated, privacy, file_type, reference=None, url=None):

        privacy = self.search_privacy(privacy)
        datafile_type = self.search_datafile_type(file_type)

        if privacy is None or datafile_type is None:
            print("There is missing value(s) in the data!")
            return

        entry_id = self.add_to_entries(
            self.db_classes.Datafiles.table_type_id,
            self.db_classes.Datafiles.__tablename__,
        )

        datafile_obj = self.db_classes.Datafiles(
            datafile_id=entry_id,
            simulated=bool(simulated),
            privacy_id=privacy.privacy_id,
            datafile_type_id=datafile_type.datafile_type_id,
            reference=reference,
            url=url,
        )

        self.session.add(datafile_obj)
        self.session.flush()

        return datafile_obj

    def add_to_platforms(self, name, nationality, platform_type, privacy):

        nationality = self.search_nationality(nationality)
        platform_type = self.search_platform_type(platform_type)
        privacy = self.search_privacy(privacy)

        if nationality is None or platform_type is None or privacy is None:
            print("There is missing value(s) in the data!")
            return

        entry_id = self.add_to_entries(
            self.db_classes.Platforms.table_type_id,
            self.db_classes.Platforms.__tablename__,
        )

        platform_obj = self.db_classes.Platforms(
            platform_id=entry_id,
            name=name,
            nationality_id=nationality.nationality_id,
            platform_type_id=platform_type.platform_type_id,
            privacy_id=privacy.privacy_id,
        )

        self.session.add(platform_obj)
        self.session.flush()

        # add to cache and return created platform
        self.platforms[name] = platform_obj
        # should return DB type or something else decoupled from DB?
        return platform_obj

    #############################################################
    # Search/lookup functions

    def search_datafile_type(self, name):
        # search for any datafile type with this name
        return (
            self.session.query(self.db_classes.DatafileTypes)
            .filter(self.db_classes.DatafileTypes.name == name)
            .first()
        )

    def search_datafile(self, name):
        # search for any datafile with this name
        return (
            self.session.query(self.db_classes.Datafiles)
            .filter(self.db_classes.Datafiles.reference == name)
            .first()
        )

    def search_datafile_by_id(self, id):
        # search for any datafile with this id
        return (
            self.session.query(self.db_classes.Datafile)
            .filter(self.db_classes.Datafile.datafile_id == str(id))
            .first()
        )

    def search_platform(self, name):
        # search for any platform with this name
        return (
            self.session.query(self.db_classes.Platforms)
            .filter(self.db_classes.Platforms.name == name)
            .first()
        )

    def search_platform_type(self, name):
        # search for any platform type with this name
        return (
            self.session.query(self.db_classes.PlatformTypes)
            .filter(self.db_classes.PlatformTypes.name == name)
            .first()
        )

    def search_nationality(self, name):
        # search for any nationality with this name
        return (
            self.session.query(self.db_classes.Nationalities)
            .filter(self.db_classes.Nationalities.name == name)
            .first()
        )

    def search_sensor(self, name):
        # search for any sensor type featuring this name
        return (
            self.session.query(self.db_classes.Sensors)
            .filter(self.db_classes.Sensors.name == name)
            .first()
        )

    def search_sensor_type(self, name):
        # search for any sensor type featuring this name
        return (
            self.session.query(self.db_classes.SensorTypes)
            .filter(self.db_classes.SensorTypes.name == name)
            .first()
        )

    def search_privacy(self, name):
        # search for any privacy with this name
        return (
            self.session.query(self.db_classes.Privacies)
            .filter(self.db_classes.Privacies.name == name)
            .first()
        )

    def search_table_type(self, table_type_id):
        # search for any table type with this id
        return (
            self.session.query(self.db_classes.TableType)
            .filter(self.db_classes.TableType.table_type_id == table_type_id)
            .first()
        )

    #############################################################
    # Get functions

    def get_nationalities(self):
        # get list of all nationalities in the DB
        return self.session.query(self.db_classes.Nationalities).all()

    def get_platform_types(self):
        # get list of all platform types in the DB
        return self.session.query(self.db_classes.PlatformTypes).all()

    def get_privacies(self):
        # get list of all privacies in the DB
        return self.session.query(self.db_classes.Privacies).all()

    def get_sensors(self):
        # get list of all sensors in the DB
        return self.session.query(self.db_classes.Sensors).all()

    def get_sensor_types(self):
        # get list of all sensors types in the DB
        return self.session.query(self.db_classes.SensorTypes).all()

    def get_sensors_by_platform_type(self, platform_type):
        # given platform type, return all Sensors contained on platforms of that type
        return (
            self.session.query(self.db_classes.Platforms, self.db_classes.Sensors)
            .join(
                self.db_classes.Sensors,
                self.db_classes.Sensors.platform_id
                == self.db_classes.Platforms.platform_id,
            )
            .filter(
                self.db_classes.Platforms.platform_type_id
                == platform_type.platform_type_id
            )
            .all()
        )

    def get_states(self):
        # get list of all states in the DB
        return self.session.query(self.db_classes.States).all()

    #############################################################
    # Validation/check functions

    # return True if provided nationality ok
    def check_nationality(self, nationality):
        if len(nationality) == 0:
            return False

        if next(
            (nat for nat in self.get_nationalities() if nat.name == nationality), None
        ):
            # A nationality already exists with that name
            return False

        return True

    # return True if provided privacy ok
    def check_privacy(self, privacy):
        if len(privacy) == 0:
            return False

        if next((priv for priv in self.get_privacies() if priv.name == privacy), None):
            # A privacy already exists with that name
            return False

        return True

    # return True if provided platform type ok
    def check_platform_type(self, platform_type):
        if len(platform_type) == 0:
            return False

        if next(
            (pt for pt in self.get_platform_types() if pt.name == platform_type), None
        ):
            # A platform type already exists with that name
            return False

        return True

    # return True if provided sensor ok
    def check_sensor(self, sensor):
        if len(sensor) == 0:
            return False

        if next((sen for sen in self.get_sensors() if sen.name == sensor), None):
            # A sensor already exists with that name
            return False

        return True

    # return True if provided sensor type ok
    def check_sensor_type(self, sensor_type):
        if len(sensor_type) == 0:
            return False

        if next((st for st in self.get_sensor_types() if st.name == sensor_type), None):
            # A sensor type already exists with that name
            return False

        return True

    #############################################################
    # Generic Metadata functions

    def get_table_type_data(self, table_types):
        data = dict()
        for table_type in table_types:
            for table in self.meta_classes[table_type]:
                data[table.__name__] = self.session.query(table).count()
        return data

    #############################################################
    # New methods

    # TODO: These methods use add_to_xxx methods from above. They should be changed to
    # internal functions.

    def get_datafile(self, datafile_name, datafile_type):
        """
        Adds an entry to the datafiles table of the specified name (path)
        and type if not already present.

        Args:
            datafile_name: {String} -- Name of Datafile
            datafile_type: {String} -- Name of Datafile Type

        Returns:
            A Datafile object that can used to add state.
        """

        # return True if provided datafile exists
        def check_datafile(datafile):
            if len(datafile) == 0:
                return False

            if next(
                (file for file in self.get_datafiles() if file.reference == datafile),
                None,
            ):
                # A datafile already exists with that name
                return False

            return True

        self.add_to_datafile_types(datafile_type)
        self.add_to_privacies("NEW")
        if check_datafile(datafile_name):
            return self.add_to_datafiles(
                simulated=True,
                privacy="NEW",
                file_type=datafile_type,
                reference=datafile_name,
            )
        else:
            return (
                self.session.query(self.db_classes.Datafiles)
                .filter(self.db_classes.Datafiles.reference == datafile_name)
                .first()
            )

    def get_platform(
        self, platform_name, nationality=None, platform_type=None, privacy=None
    ):
        """
        Adds an entry to the platforms table for the specified platform
        if not already present.

        Args:
            platform_name: {String} -- Name of Platform
            nationality: {String} -- Name of Nationality
            platform_type: {String} -- Name of Platform Type
            privacy: {String} -- Name of Privacy

        Returns:
            A Platform object that can be used to lookup/create Sensors.
        """

        # return True if provided platform exists
        def check_platform(name):
            if len(name) == 0:
                return False

            if next(
                (
                    platform
                    for platform in self.get_platforms()
                    if platform.name == name
                ),
                None,
            ):
                # A platform already exists with that name
                return False

            return True

        if check_platform(platform_name):
            return self.add_to_platforms(
                name=platform_name,
                nationality=nationality,
                platform_type=platform_type,
                privacy=privacy,
            )
        else:
            return (
                self.session.query(self.db_classes.Platforms)
                .filter(self.db_classes.Platforms.name == platform_name)
                .first()
            )

    def get_status(
        self,
        report_measurement: bool = False,
        report_metadata: bool = False,
        report_reference: bool = False,
    ):
        """
        Provides a summary of the contents of the DataStore.

        Args:
            report_measurement: {Boolean} -- Boolean flag indicates Measurement Tables
            report_metadata: {Boolean} -- Boolean flag indicates Metadata Tables
            report_reference: {Boolean} -- Boolean flag indicates Reference Tables

        Returns:
            A TableSummarySet.
        """

        reference_tables = {}
        metadata_tables = {}
        measurement_tables = {}
        headers = ["Table Name", "Number of rows"]
        if report_measurement:
            # Create measurement table list
            measurement_table_objects = self.meta_classes[TableTypes.MEASUREMENT]
            for table_object in list(measurement_table_objects):
                name = table_object.__tablename__
                measurement_tables[name] = table_summary(self.session, table_object)
            print("\nMEASUREMENT TABLES", "\n")
            print(
                tabulate(
                    [(k, v) for k, v in measurement_tables.items()],
                    headers=headers,
                    tablefmt="pretty",
                )
            )

        if report_metadata:
            # Create metadata table list
            metadata_table_objects = self.meta_classes[TableTypes.METADATA]
            for table_object in list(metadata_table_objects):
                name = table_object.__tablename__
                metadata_tables[name] = table_summary(self.session, table_object)
            print("\nMETADATA TABLES", "\n")
            print(
                tabulate(
                    [(k, v) for k, v in metadata_tables.items()],
                    headers=headers,
                    tablefmt="pretty",
                )
            )

        if report_reference:
            # Create reference table list
            reference_table_objects = self.meta_classes[TableTypes.REFERENCE]
            for table_object in list(reference_table_objects):
                name = table_object.__tablename__
                reference_tables[name] = table_summary(self.session, table_object)
            print("\nREFERENCE TABLES", "\n")
            print(
                tabulate(
                    [(k, v) for k, v in reference_tables.items()],
                    headers=headers,
                    tablefmt="pretty",
                )
            )

        return measurement_tables, metadata_tables, reference_tables

    def get_sensor(self, sensor_name, sensor_type=None, privacy=None):
        """
        Lookup or create a sensor of this name for this platform. Specified sensor
        will be added to the sensors table.
        Args:
            sensor_name: {String} -- Name of Sensor
            sensor_type: {String} -- Type of Sensor
            privacy: {String} -- Name of Privacy

        Returns:
            A Sensor object that can be passed to the add_state() function of Datafile.
        """

        # return True if provided sensor exists
        def check_sensor(name):
            if len(name) == 0:
                return False

            if next(
                (sensor for sensor in self.get_sensors() if sensor.name == name), None,
            ):
                # A platform already exists with that name
                return False

            return True

        if check_sensor(sensor_name):
            return self.add_to_sensors(
                name=sensor_name,
                sensor_type=sensor_type,
                # privacy=privacy,
            )
        else:
            return (
                self.session.query(self.db_classes.Sensors)
                .filter(self.db_classes.Sensors.name == sensor_name)
                .first()
            )

    #############################################################
    # Measurements

    def create_state(self, sensor, timestamp):
        """
        Creates an intermediate State object representing a row in the State table.

        Args:
            sensor: {String} -- Database object representing a Sensor
            timestamp: {Datetime} -- Timestamp the state was recorded

        Returns:
            A State object, to which other attributes can be added, prior to
            submission to the database.
        """
        pass

    def create_contact(self, sensor, timestamp):
        """
        Creates an intermediate Contact object representing a row in the Contact table.

        Args:
            sensor: {String} -- Database object representing a Sensor
            timestamp: {Datetime} -- Timestamp the state was recorded

        Returns:
            A Contact object, to which other attributes can be added, prior to
            submission to the database.
        """
        pass

    def create_comment(self, sensor, timestamp, comment, type):
        """
        Creates an intermediate Comment object representing a row in the Comment table.

        Args:
            sensor: {String} -- Database object representing a Sensor
            timestamp: {Datetime} -- Timestamp the state was recorded
            comment: {String} -- Textual comment
            type: {commentType} -- Type of comment being added

        Returns:
            A Comment object, to which other attributes can be added, prior to
            submission to the database.
        """
        pass

    # End of Measurements
    #############################################################
    # Reference Type Maintenance

    def add_to_table_types(self, table_type_id, table_name):
        """
        Adds the specified table type and name to the table types table if not already
        present.

        Args:
            table_type_id: {String} -- ID of Table Type
            table_name: {String} -- Name of Table Type

        Returns:
            Created table type entity
        """
        # check in cache for table type
        if table_type_id in self.table_types:
            return self.table_types[table_type_id]

        # doesn't exist in cache, try to lookup in DB
        table_types = self.search_table_type(table_type_id)
        if table_types:
            # add to cache and return
            self.table_types[table_type_id] = table_types
            return table_types

        # enough info to proceed and create entry
        table_type = self.db_classes.TableType(
            table_type_id=table_type_id, name=table_name
        )
        self.session.add(table_type)
        self.session.flush()

        # add to cache and return created table type
        self.table_types[table_type_id] = table_type
        # should return DB type or something else decoupled from DB?
        return table_type

    # TODO: add function to do common pattern of action in these functions
    def add_to_platform_types(self, platform_type_name):
        """
        Adds the specified platform type to the platformtypes table if not already
        present.

        Args:
            platform_type_name: {String} -- Name of Platform Type

        Returns:
            Created platform type entity
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

        entry_id = self.add_to_entries(
            self.db_classes.PlatformTypes.table_type_id,
            self.db_classes.PlatformTypes.__tablename__,
        )
        # enough info to proceed and create entry
        platform_type = self.db_classes.PlatformTypes(
            platform_type_id=entry_id, name=platform_type_name
        )
        self.session.add(platform_type)
        self.session.flush()

        # add to cache and return created platform type
        self.platform_types[platform_type_name] = platform_type
        # should return DB type or something else decoupled from DB?
        return platform_type

    def add_to_nationalities(self, nationality_name):
        """
        Adds the specified nationality to the nationalities table if not already present
        Args:
            nationality_name: {String} -- Name of Nationality

        Returns:
            Created Nationality entity
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

        entry_id = self.add_to_entries(
            self.db_classes.Nationalities.table_type_id,
            self.db_classes.Nationalities.__tablename__,
        )
        # enough info to proceed and create entry
        nationality = self.db_classes.Nationalities(
            nationality_id=entry_id, name=nationality_name
        )
        self.session.add(nationality)
        self.session.flush()

        # add to cache and return created platform
        self.nationalities[nationality_name] = nationality
        # should return DB type or something else decoupled from DB?
        return nationality

    def add_to_privacies(self, privacy_name):
        """
        Adds the specified privacy entry to the privacies table if not already present.

        Args:
            privacy_name: {String} -- Name of Privacy

        Returns:
            Created Privacy entity
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

        entry_id = self.add_to_entries(
            self.db_classes.Privacies.table_type_id,
            self.db_classes.Privacies.__tablename__,
        )
        # enough info to proceed and create entry
        privacy = self.db_classes.Privacies(privacy_id=entry_id, name=privacy_name)
        self.session.add(privacy)
        self.session.flush()

        # add to cache and return created platform
        self.privacies[privacy_name] = privacy
        # should return DB type or something else decoupled from DB?
        return privacy

    # TODO: it is possible to merge two methods taking a resolver=True/False argument
    def add_to_datafile_types(self, datafile_type):
        """
        Adds the specified datafile type to the datafiletypes table if not already
        present.

        Arguments:
            datafile_type {String} -- Name of Datafile Type

        Returns:
            DataFileType -- Wrapped database entity for DatafileType
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

        entry_id = self.add_to_entries(
            self.db_classes.DatafileTypes.table_type_id,
            self.db_classes.DatafileTypes.__tablename__,
        )
        # proceed and create entry
        datafile_type_obj = self.db_classes.DatafileTypes(
            datafile_type_id=entry_id, name=datafile_type
        )

        self.session.add(datafile_type_obj)
        self.session.flush()

        # add to cache and return created datafile type
        self.datafile_types[datafile_type] = datafile_type_obj
        # should return DB type or something else decoupled from DB?
        return datafile_type_obj

    def add_to_sensor_types(self, sensor_type_name):
        """
        Adds the specified sensor type to the sensor types table if not already present.

        Args:
            sensor_type_name {String} -- Name of Sensor Type

        Returns:
            Created Sensor Type entity
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
        sensor_type = self.db_classes.SensorTypes(name=sensor_type_name)
        self.session.add(sensor_type)
        self.session.flush()

        # add to cache and return created sensor type
        self.sensor_types[sensor_type_name] = sensor_type
        # should return DB type or something else decoupled from DB?
        return sensor_type

    # End of Reference Type Maintenance
    #############################################################
