import os
from pathlib import Path

from datetime import datetime
from sqlalchemy import create_engine, event
from sqlalchemy.schema import CreateSchema
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from importlib import import_module
from contextlib import contextmanager

from pepys_import.resolvers.default_resolver import DefaultResolver
from pepys_import.utils.data_store_utils import import_from_csv
from .db_base import base_postgres, base_sqlite
from .db_status import TableTypes
from pepys_import.core.formats import unit_registry

from pepys_import import __version__
from pepys_import.utils.branding_util import (
    show_welcome_banner,
    show_software_meta_info,
)

MAIN_DIRECTORY_PATH = Path(__file__).parent.parent.parent  # pepys_import/pepys_import
DEFAULT_DATA_PATH = os.path.join(MAIN_DIRECTORY_PATH, "database", "default_data")

# TODO: add foreign key refs
# TODO: add proper uuid funcs that interact with entries table

# TODO: probably move this module to the top level as it's the main one


class DataStore:

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
        """Create schemas for the database"""

        if self.db_type == "sqlite":
            try:
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
    # Add functions

    def add_to_table_types(self, table_type_id, table_name):
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

    def add_to_entries(self, table_type_id, tableName):
        # ensure table type exists to satisfy foreign key constraint
        self.add_to_table_types(table_type_id, tableName)

        # No cache for entries, just add new one when called
        entry_obj = self.db_classes.Entry(
            table_type_id=table_type_id, created_user=self.default_user_id
        )

        self.session.add(entry_obj)
        self.session.flush()

        return entry_obj.entry_id

    # TODO: add function to do common pattern of action in these functions
    def add_to_platform_types(self, platform_type_name):
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
        # should return DB type or something else decoupled from DB?
        return platform_type

    def add_to_nationalities(self, nationality_name):
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
        # should return DB type or something else decoupled from DB?
        return nationality

    def add_to_privacies(self, privacy_name):
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
        # should return DB type or something else decoupled from DB?
        return privacy

    # TODO: it is possible to merge two methods taking a resolver=True/False argument
    def add_to_datafile_types(self, datafile_type):
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
        # should return DB type or something else decoupled from DB?
        return datafile_type_obj

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

        datafile_type_obj = self.add_to_datafile_types(datafile_type)

        # don't know privacy, use resolver to query for data
        privacy = self.missing_data_resolver.resolve_privacy(
            self,
            self.db_classes.Datafile.table_type_id,
            self.db_classes.Datafile.__tablename__,
        )

        # privacy should contain (tabletype, privacy_name)
        # enough info to proceed and create entry
        table_type, privacy = privacy
        entry_id = self.add_to_entries(
            self.db_classes.Datafile.table_type_id,
            self.db_classes.Datafile.__tablename__,
        )

        datafile_obj = self.db_classes.Datafile(
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
        if platform_name in self.platforms:
            return self.platforms[platform_name]

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
            self.db_classes.Platform.table_type_id,
            self.db_classes.Platform.__tablename__,
        )

        platform_obj = self.db_classes.Platform(
            platform_id=entry_id,
            name=platform_name,
            platform_type_id=platform_type.platform_type_id,
            host_platform_id=None,
            nationality_id=nationality.nationality_id,
            privacy_id=privacy.privacy_id,
        )

        self.session.add(platform_obj)
        self.session.flush()

        # add to cache and return created platform
        self.platforms[platform_name] = platform_obj
        # should return DB type or something else decoupled from DB?
        return platform_obj

    def add_to_sensor_types(self, sensor_type_name):
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
        # should return DB type or something else decoupled from DB?
        return sensor_type

    def add_to_sensors_from_rep(self, sensor_name, platform):
        # check in cache for sensor
        if sensor_name in self.sensors:
            return self.sensors[sensor_name]

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
            self.db_classes.Sensor.table_type_id, self.db_classes.Sensor.__tablename__
        )

        sensor_obj = self.db_classes.Sensor(
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

    def add_to_states_from_rep(
        self, timestamp, datafile, sensor, lat, long, heading, speed
    ):
        # No cache for entries, just add new one when called

        # don't know privacy, use resolver to query for data
        privacy = self.missing_data_resolver.resolve_privacy(
            self,
            self.db_classes.State.table_type_id,
            self.db_classes.State.__tablename__,
        )

        # privacy should contain (table_type, privacy_name)
        # enough info to proceed and create entry
        table_type, privacy = privacy
        entry_id = self.add_to_entries(
            self.db_classes.State.table_type_id, self.db_classes.State.__tablename__
        )

        # heading is a quantity. Convert to radians
        heading_rads = heading.to(unit_registry.radians).magnitude

        # speed is a quantity. Convert to m/sec
        speed_m_sec = speed.to(unit_registry.meter / unit_registry.second).magnitude

        state_obj = self.db_classes.State(
            state_id=entry_id,
            time=timestamp,
            sensor_id=sensor.sensor_id,
            location="(" + str(long.degrees) + "," + str(lat.degrees) + ")",
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
            self.db_classes.State.table_type_id, self.db_classes.State.__tablename__
        )
        state_obj = self.db_classes.State(
            state_id=entry_id,
            time=time,
            sensor_id=sensor.sensor_id,
            location=location,
            heading=heading_rads,
            # course=course,
            speed=speed_m_sec,
            datafile_id=datafile.datafile_id,
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
            self.db_classes.Sensor.table_type_id, self.db_classes.Sensor.__tablename__
        )

        sensor_obj = self.db_classes.Sensor(
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
            self.db_classes.Datafile.table_type_id,
            self.db_classes.Datafile.__tablename__,
        )

        datafile_obj = self.db_classes.Datafile(
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
            self.db_classes.Platform.table_type_id,
            self.db_classes.Platform.__tablename__,
        )

        platform_obj = self.db_classes.Platform(
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
            self.session.query(self.db_classes.DatafileType)
            .filter(self.db_classes.DatafileType.name == name)
            .first()
        )

    def search_datafile(self, name):
        # search for any datafile with this name
        return (
            self.session.query(self.db_classes.Datafile)
            .filter(self.db_classes.Datafile.reference == name)
            .first()
        )

    def search_platform(self, name):
        # search for any platform with this name
        return (
            self.session.query(self.db_classes.Platform)
            .filter(self.db_classes.Platform.name == name)
            .first()
        )

    def search_platform_type(self, name):
        # search for any platform type with this name
        return (
            self.session.query(self.db_classes.PlatformType)
            .filter(self.db_classes.PlatformType.name == name)
            .first()
        )

    def search_nationality(self, name):
        # search for any nationality with this name
        return (
            self.session.query(self.db_classes.Nationality)
            .filter(self.db_classes.Nationality.name == name)
            .first()
        )

    def search_sensor(self, name):
        # search for any sensor type featuring this name
        return (
            self.session.query(self.db_classes.Sensor)
            .filter(self.db_classes.Sensor.name == name)
            .first()
        )

    def search_sensor_type(self, name):
        # search for any sensor type featuring this name
        return (
            self.session.query(self.db_classes.SensorType)
            .filter(self.db_classes.SensorType.name == name)
            .first()
        )

    def search_privacy(self, name):
        # search for any privacy with this name
        return (
            self.session.query(self.db_classes.Privacy)
            .filter(self.db_classes.Privacy.name == name)
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

    def get_datafiles(self):
        # get list of all datafiles in the DB
        return self.session.query(self.db_classes.Datafile).all()

    def get_nationalities(self):
        # get list of all nationalities in the DB
        return self.session.query(self.db_classes.Nationality).all()

    def get_platforms(self):
        # get list of all platforms in the DB
        return self.session.query(self.db_classes.Platform).all()

    def get_platform_types(self):
        # get list of all platform types in the DB
        return self.session.query(self.db_classes.PlatformType).all()

    def get_privacies(self):
        # get list of all privacies in the DB
        return self.session.query(self.db_classes.Privacy).all()

    def get_sensors(self):
        # get list of all sensors in the DB
        return self.session.query(self.db_classes.Sensor).all()

    def get_sensor_types(self):
        # get list of all sensors types in the DB
        return self.session.query(self.db_classes.SensorType).all()

    def get_sensors_by_platform_type(self, platform_type):
        # given platform type, return all Sensors contained on platforms of that type
        return (
            self.session.query(self.db_classes.Platform, self.db_classes.Sensor)
            .join(
                self.db_classes.Sensor,
                self.db_classes.Sensor.platform_id
                == self.db_classes.Platform.platform_id,
            )
            .filter(
                self.db_classes.Platform.platform_type_id
                == platform_type.platform_type_id
            )
            .all()
        )

    def get_states(self):
        # get list of all states in the DB
        return self.session.query(self.db_classes.State).all()

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

    def get_table_type_data(self, table_types):
        data = dict()
        for table_type in table_types:
            for table in self.meta_classes[table_type]:
                data[table.__name__] = self.session.query(table).count()
        return data

    #############################################################
    # Populate methods in order to import CSV files

    def populate_reference(self, reference_data_folder=None):
        """Import given CSV file to the given reference table"""
        if reference_data_folder is None:
            reference_data_folder = DEFAULT_DATA_PATH

        files = os.listdir(reference_data_folder)

        reference_tables = []
        # Create reference table list
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
        if sample_data_folder is None:
            sample_data_folder = DEFAULT_DATA_PATH

        files = os.listdir(sample_data_folder)

        metadata_tables = []
        # Create metadata table list
        metadata_table_objects = self.meta_classes[TableTypes.METADATA]
        for table_object in list(metadata_table_objects):
            metadata_tables.append(table_object.__tablename__)

        metadata_files = [
            file for file in files if os.path.splitext(file)[0] in metadata_tables
        ]
        import_from_csv(self, sample_data_folder, metadata_files)

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
