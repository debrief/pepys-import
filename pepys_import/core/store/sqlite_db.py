from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DATE, DateTime
from sqlalchemy.dialects.sqlite import DATETIME, TIMESTAMP, REAL

from geoalchemy2 import Geography, Geometry
from sqlalchemy.ext.hybrid import hybrid_property

from .db_base import BaseSpatiaLite
from .db_status import TableTypes
from pepys_import.core.formats import quantity


class Entry(BaseSpatiaLite):
    __tablename__ = "Entry"
    table_type = TableTypes.METADATA
    table_name = "Entry"

    entry_id = Column(Integer, primary_key=True)
    table_type_id = Column(Integer, nullable=False)
    created_user = Column(Integer)
    created_date = Column(DateTime, default=datetime.utcnow)

    @classmethod
    def add_to_entries(cls, session, table_type_id, table_name):
        # ensure table type exists to satisfy foreign key constraint
        TableType().add_to_table_types(session, table_type_id, table_name)

        # No cache for entries, just add new one when called
        entry_obj = Entry(table_type_id=table_type_id, created_user=1)

        session.add(entry_obj)
        session.flush()

        return entry_obj.entry_id


class TableType(BaseSpatiaLite):
    __tablename__ = "TableTypes"
    table_type = TableTypes.METADATA
    table_name = "TableType"

    table_type_id = Column(Integer, nullable=False, primary_key=True)
    name = Column(String(150))
    created_date = Column(DateTime, default=datetime.utcnow)

    @classmethod
    def search_table_type(cls, session, table_type_id):
        # search for any table type with this id
        return (
            session.query(TableType)
            .filter(TableType.table_type_id == table_type_id)
            .first()
        )

    @classmethod
    def add_to_table_types(cls, session, table_type_id, table_name):
        table_type = cls.search_table_type(session, table_type_id)
        if table_type is None:
            # enough info to proceed and create entry
            table_type = TableType(table_type_id=table_type_id, name=table_name)
            session.add(table_type)
            session.flush()

        return table_type


# Metadata Tables
class HostedBy(BaseSpatiaLite):
    __tablename__ = "HostedBy"
    table_type = TableTypes.METADATA
    table_type_id = 1
    table_name = "HostedBy"

    hosted_by_id = Column(Integer, primary_key=True)
    subject_id = Column(Integer, nullable=False)
    host_id = Column(Integer, nullable=False)
    hosted_from = Column(DATE, nullable=False)
    host_to = Column(DATE, nullable=False)
    privacy_id = Column(Integer, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Sensors(BaseSpatiaLite):
    __tablename__ = "Sensors"
    table_type = TableTypes.METADATA
    table_type_id = 2
    table_name = "Sensors"

    sensor_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    sensor_type_id = Column(Integer, nullable=False)
    platform_id = Column(Integer, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)

    @classmethod
    def add_to_sensors(cls, session, name, sensor_type, host):
        sensor_type = SensorTypes().search_sensor_type(session, sensor_type)
        host = Platforms().search_platform(session, host)

        if sensor_type is None or host is None:
            text = f"There is missing value(s) in '{sensor_type}, {host}'!"
            raise Exception(text)

        entry_id = Entry().add_to_entries(
            session, Sensors.table_type_id, Sensors.__tablename__
        )

        sensor_obj = Sensors(
            sensor_id=entry_id,
            name=name,
            sensor_type_id=sensor_type.sensor_type_id,
            platform_id=host.platform_id,
        )
        session.add(sensor_obj)
        session.flush()

        return sensor_obj


class Platforms(BaseSpatiaLite):
    __tablename__ = "Platforms"
    table_type = TableTypes.METADATA
    table_type_id = 3
    table_name = "Platforms"

    platform_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    nationality_id = Column(Integer, nullable=False)
    platform_type_id = Column(Integer, nullable=False)
    privacy_id = Column(Integer, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)

    @classmethod
    def search_platform(cls, session, name):
        # search for any platform with this name
        return session.query(Platforms).filter(Platforms.name == name).first()

    @staticmethod
    def get_sensor(session, all_sensors, sensor_name, sensor_type=None, privacy=None):
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
            if next((sensor for sensor in all_sensors if sensor.name == name), None):
                # A sensor already exists with that name
                return False

            return True

        if len(sensor_name) == 0:
            raise Exception("Please enter sensor name!")
        elif check_sensor(sensor_name):
            platform = session.query(Platforms).first()
            return Sensors().add_to_sensors(
                session=session,
                name=sensor_name,
                sensor_type=sensor_type,
                host=platform.name
                # privacy=privacy,
            )
        else:
            return session.query(Sensors).filter(Sensors.name == sensor_name).first()


class Tasks(BaseSpatiaLite):
    __tablename__ = "Tasks"
    table_type = TableTypes.METADATA
    table_type_id = 4
    table_name = "Tasks"

    task_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    parent_id = Column(Integer, nullable=False)
    start = Column(TIMESTAMP, nullable=False)
    end = Column(TIMESTAMP, nullable=False)
    environment = Column(String(150))
    location = Column(String(150))
    privacy_id = Column(Integer, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Participants(BaseSpatiaLite):
    __tablename__ = "Participants"
    table_type = TableTypes.METADATA
    table_type_id = 5
    table_name = "Participants"

    participant_id = Column(Integer, primary_key=True)
    platform_id = Column(Integer, nullable=False)
    task_id = Column(Integer, nullable=False)
    start = Column(TIMESTAMP)
    end = Column(TIMESTAMP)
    force = Column(String(150))
    privacy_id = Column(Integer, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Datafiles(BaseSpatiaLite):
    __tablename__ = "Datafiles"
    table_type = TableTypes.METADATA
    table_type_id = 6
    table_name = "Datafiles"

    datafile_id = Column(Integer, primary_key=True)
    simulated = Column(Boolean, nullable=False)
    privacy_id = Column(Integer, nullable=False)
    datafile_type_id = Column(Integer, nullable=False)
    reference = Column(String(150))
    url = Column(String(150))
    created_date = Column(DateTime, default=datetime.utcnow)

    def create_state(self, sensor, timestamp):
        state = States(
            sensor_id=sensor.sensor_id, time=timestamp, source_id=self.datafile_id
        )
        return state

    def create_contact(self, sensor, timestamp):
        contact = Contacts(
            sensor_id=sensor.sensor_id, time=timestamp, source_id=self.datafile_id
        )
        return contact

    def create_comment(self, sensor, timestamp, comment, comment_type):
        comment = Comments(
            time=timestamp,
            content=comment,
            comment_type_id=comment_type.comment_type_id,
            source_id=self.datafile_id,
        )
        return comment

    def validate(self):
        return True

    # def verify(self):
    #     pass


class Synonyms(BaseSpatiaLite):
    __tablename__ = "Synonyms"
    table_type = TableTypes.METADATA
    table_type_id = 7
    table_name = "Synonyms"

    synonym_id = Column(Integer, primary_key=True)
    table = Column(String(150), nullable=False)
    synonym = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Changes(BaseSpatiaLite):
    __tablename__ = "Changes"
    table_type = TableTypes.METADATA
    table_type_id = 8
    table_name = "Changes"

    change_id = Column(Integer, primary_key=True)
    user = Column(String(150), nullable=False)
    modified = Column(DATE, nullable=False)
    reason = Column(String(500), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Logs(BaseSpatiaLite):
    __tablename__ = "Logs"
    table_type = TableTypes.METADATA
    table_type_id = 9
    table_name = "Log"

    log_id = Column(Integer, primary_key=True)
    table = Column(String(150), nullable=False)
    id = Column(Integer, nullable=False)
    field = Column(String(150), nullable=False)
    new_value = Column(String(150), nullable=False)
    change_id = Column(Integer, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Extractions(BaseSpatiaLite):
    __tablename__ = "Extractions"
    table_type = TableTypes.METADATA
    table_type_id = 10
    table_name = "Extractions"

    extraction_id = Column(Integer, primary_key=True)
    table = Column(String(150), nullable=False)
    field = Column(String(150), nullable=False)
    chars = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Tags(BaseSpatiaLite):
    __tablename__ = "Tags"
    table_type = TableTypes.METADATA
    table_type_id = 11
    table_name = "Tags"

    tag_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class TaggedItems(BaseSpatiaLite):
    __tablename__ = "TaggedItems"
    table_type = TableTypes.METADATA
    table_type_id = 12
    table_name = "TaggedItems"

    tagged_item_id = Column(Integer, primary_key=True)
    tag_id = Column(Integer, nullable=False)
    item_id = Column(Integer, nullable=False)
    tagged_by_id = Column(Integer, nullable=False)
    private = Column(Boolean, nullable=False)
    tagged_on = Column(DATE, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


# Reference Tables
class PlatformTypes(BaseSpatiaLite):
    __tablename__ = "PlatformTypes"
    table_type = TableTypes.REFERENCE
    table_name = "PlatformTypes"
    table_type_id = 13

    platform_type_id = Column(Integer, primary_key=True)
    name = Column(String(150))
    created_date = Column(DateTime, default=datetime.utcnow)


class Nationalities(BaseSpatiaLite):
    __tablename__ = "Nationalities"
    table_type = TableTypes.REFERENCE
    table_name = "Nationalities"
    table_type_id = 14

    nationality_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class GeometryTypes(BaseSpatiaLite):
    __tablename__ = "GeometryTypes"
    table_type = TableTypes.REFERENCE
    table_name = "GeometryTypes"
    table_type_id = 15

    geo_type_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class GeometrySubTypes(BaseSpatiaLite):
    __tablename__ = "GeometrySubTypes"
    table_type = TableTypes.REFERENCE
    table_name = "GeometrySubTypes"
    table_type_id = 16

    geo_sub_type_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    parent = Column(Integer, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class Users(BaseSpatiaLite):
    __tablename__ = "Users"
    table_type = TableTypes.REFERENCE
    table_name = "Users"
    table_type_id = 17

    user_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class UnitTypes(BaseSpatiaLite):
    __tablename__ = "UnitTypes"
    table_type = TableTypes.REFERENCE
    table_name = "UnitTypes"
    table_type_id = 18

    unit_type_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class ClassificationTypes(BaseSpatiaLite):
    __tablename__ = "ClassificationTypes"
    table_type = TableTypes.REFERENCE
    table_name = "ClassificationTypes"
    table_type_id = 19

    class_type_id = Column(Integer, primary_key=True)
    class_type = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class ContactTypes(BaseSpatiaLite):
    __tablename__ = "ContactTypes"
    table_type = TableTypes.REFERENCE
    table_name = "ContactTypes"
    table_type_id = 20

    contact_type_id = Column(Integer, primary_key=True)
    contact_type = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class SensorTypes(BaseSpatiaLite):
    __tablename__ = "SensorTypes"
    table_type = TableTypes.REFERENCE
    table_name = "SensorTypes"
    table_type_id = 21

    sensor_type_id = Column(Integer, primary_key=True)
    name = Column(String(150))
    created_date = Column(DateTime, default=datetime.utcnow)

    @classmethod
    def search_sensor_type(cls, session, name):
        # search for any sensor type featuring this name
        return session.query(SensorTypes).filter(SensorTypes.name == name).first()


class Privacies(BaseSpatiaLite):
    __tablename__ = "Privacies"
    table_type = TableTypes.REFERENCE
    table_name = "Privacies"
    table_type_id = 22

    privacy_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class DatafileTypes(BaseSpatiaLite):
    __tablename__ = "DatafileTypes"
    table_type = TableTypes.REFERENCE
    table_name = "DatafileTypes"
    table_type_id = 23

    datafile_type_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class MediaTypes(BaseSpatiaLite):
    __tablename__ = "MediaTypes"
    table_type = TableTypes.REFERENCE
    table_name = "MediaTypes"
    table_type_id = 24

    media_type_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class CommentTypes(BaseSpatiaLite):
    __tablename__ = "CommentTypes"
    table_type = TableTypes.REFERENCE
    table_name = "CommentTypes"
    table_type_id = 25

    comment_type_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class CommodityTypes(BaseSpatiaLite):
    __tablename__ = "CommodityTypes"
    table_type = TableTypes.REFERENCE
    table_name = "CommodityTypes"
    table_type_id = 26

    commodity_type_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


class ConfidenceLevels(BaseSpatiaLite):
    __tablename__ = "ConfidenceLevels"
    table_type = TableTypes.REFERENCE
    table_name = "ConfidenceLevels"
    table_type_id = 27

    confidence_level_id = Column(Integer, primary_key=True)
    level = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)


# Measurements Tables
class States(BaseSpatiaLite):
    __tablename__ = "States"
    table_type = TableTypes.MEASUREMENT
    table_type_id = 28
    table_name = "States"

    state_id = Column(Integer, primary_key=True)
    time = Column(TIMESTAMP, nullable=False)
    sensor_id = Column(Integer, nullable=False)
    location = Column(Geometry(geometry_type="POINT", management=True))
    heading = Column(REAL)
    course = Column(REAL)
    speed = Column(REAL)
    source_id = Column(Integer, nullable=False)
    privacy_id = Column(Integer)
    created_date = Column(DateTime, default=datetime.utcnow)

    # def set_location(self, lat_val: float, long_val: float):
    #     self.location = (lat_val, long_val)
    #
    # def set_location_obj(self, location):
    #     self.location = location
    #
    # def set_heading(self, heading: quantity):
    #     self.heading = heading
    #
    # def set_course(self, course: quantity):
    #     self.course = course
    #
    # def set_speed(self, speed: quantity):
    #     self.speed = speed
    #
    # def set_privacy(self, privacy_type):
    #     self.privacy_id = privacy_type.privacy_id

    def submit(self, session):
        """Submit intermediate object to the DB"""
        session.add(self)
        session.flush()

        return self


class Contacts(BaseSpatiaLite):
    __tablename__ = "Contacts"
    table_type = TableTypes.MEASUREMENT
    table_type_id = 29
    table_name = "Contacts"

    contact_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    sensor_id = Column(Integer, nullable=False)
    time = Column(TIMESTAMP, nullable=False)
    bearing = Column(REAL)
    rel_bearing = Column(REAL)
    freq = Column(REAL)
    location = Column(Geometry(geometry_type="POINT", management=True))
    major = Column(REAL)
    minor = Column(REAL)
    orientation = Column(REAL)
    classification = Column(String(150))
    confidence = Column(String(150))
    contact_type = Column(String(150))
    mla = Column(REAL)
    sla = Column(REAL)
    subject_id = Column(Integer)
    source_id = Column(Integer, nullable=False)
    privacy_id = Column(Integer)
    created_date = Column(DateTime, default=datetime.utcnow)

    def set_name(self, name):
        self.name = name

    def set_subject(self, platform):
        self.subject_id = platform.platform_id

    # def set_bearing(self, bearing):
    #     self.bearing = bearing
    #
    # def set_rel_bearing(self, rel_bearing):
    #     self.rel_bearing = rel_bearing
    #
    # def set_frequency(self, frequency):
    #     self.freq = frequency
    #
    # def set_privacy(self, privacy_type):
    #     self.privacy_id = privacy_type.privacy_id

    def submit(self, session):
        """Submit intermediate object to the DB"""
        session.add(self)
        session.flush()

        return self


class Activations(BaseSpatiaLite):
    __tablename__ = "Activations"
    table_type = TableTypes.MEASUREMENT
    table_type_id = 30
    table_name = "Activations"

    activation_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    sensor_id = Column(Integer, nullable=False)
    start = Column(TIMESTAMP, nullable=False)
    end = Column(TIMESTAMP, nullable=False)
    min_range = Column(REAL)
    max_range = Column(REAL)
    left_arc = Column(REAL)
    right_arc = Column(REAL)
    source_id = Column(Integer, nullable=False)
    privacy_id = Column(Integer)
    created_date = Column(DateTime, default=datetime.utcnow)


class LogsHoldings(BaseSpatiaLite):
    __tablename__ = "LogsHoldings"
    table_type = TableTypes.MEASUREMENT
    table_type_id = 31
    table_name = "LogsHoldings"

    logs_holding_id = Column(Integer, primary_key=True)
    time = Column(TIMESTAMP, nullable=False)
    commodity_id = Column(Integer, nullable=False)
    quantity = Column(REAL, nullable=False)
    unit_type_id = Column(Integer, nullable=False)
    platform_id = Column(Integer, nullable=False)
    comment = Column(String(150), nullable=False)
    source_id = Column(Integer, nullable=False)
    privacy_id = Column(Integer)
    created_date = Column(DateTime, default=datetime.utcnow)


class Comments(BaseSpatiaLite):
    __tablename__ = "Comments"
    table_type = TableTypes.MEASUREMENT
    table_type_id = 32
    table_name = "Comments"

    comment_id = Column(Integer, primary_key=True)
    platform_id = Column(Integer)
    time = Column(TIMESTAMP, nullable=False)
    comment_type_id = Column(Integer, nullable=False)
    content = Column(String(150), nullable=False)
    source_id = Column(Integer, nullable=False)
    privacy_id = Column(Integer)
    created_date = Column(DateTime, default=datetime.utcnow)

    def set_platform(self, platform):
        self.platform_id = platform.platform_id

    # def set_privacy(self, privacy_type):
    #     self.privacy_id = privacy_type.privacy_id

    def submit(self, session):
        """Submit intermediate object to the DB"""
        session.add(self)
        session.flush()

        return self


class Geometries(BaseSpatiaLite):
    __tablename__ = "Geometries"
    table_type = TableTypes.MEASUREMENT
    table_type_id = 33
    table_name = "Geometries"

    geometry_id = Column(Integer, primary_key=True)
    geometry = Column(
        Geometry(geometry_type="GEOMETRY", management=True), nullable=False
    )
    name = Column(String(150), nullable=False)
    geo_type_id = Column(Integer, nullable=False)
    geo_sub_type_id = Column(Integer, nullable=False)
    start = Column(TIMESTAMP)
    end = Column(TIMESTAMP)
    task_id = Column(Integer)
    subject_platform_id = Column(Integer)
    sensor_platform_id = Column(Integer)
    source_id = Column(Integer, nullable=False)
    privacy_id = Column(Integer)
    created_date = Column(DateTime, default=datetime.utcnow)


class Media(BaseSpatiaLite):
    __tablename__ = "Media"
    table_type = TableTypes.MEASUREMENT
    table_type_id = 34
    table_name = "Media"

    media_id = Column(Integer, primary_key=True)
    platform_id = Column(Integer)
    subject_id = Column(Integer)
    sensor_id = Column(Integer)
    location = Column(Geometry(geometry_type="POINT", management=True))
    time = Column(TIMESTAMP)
    media_type_id = Column(Integer, nullable=False)
    url = Column(String(150), nullable=False)
    source_id = Column(Integer, nullable=False)
    privacy_id = Column(Integer)
    created_date = Column(DateTime, default=datetime.utcnow)
