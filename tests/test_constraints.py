import unittest
from datetime import datetime

import pytest
from sqlalchemy import exc
from sqlalchemy.orm.session import sessionmaker
from testing.postgresql import Postgresql

from pepys_import.core.store.data_store import DataStore

# All reference tables excluding GeometrySubType and Privacy which can't be tested in this simple way
REFERENCE_TABLES = [
    "SensorType",
    "PlatformType",
    "Nationality",
    "GeometryType",
    "User",
    "UnitType",
    "DatafileType",
    "MediaType",
    "CommentType",
    "CommodityType",
    "ConfidenceLevel",
    "ClassificationType",
    "ContactType",
    "ConfidenceLevel",
]


class TestUniqueness:
    """Test the uniqueness constraints by trying to force adding duplicate objects.

    We can't do this with the normal self.store.add_to_x methods as they check
    for existing entries first - so we have to do it with the raw classes and a raw session.
    """

    def setup_class(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    @pytest.mark.parametrize(
        "table_name",
        REFERENCE_TABLES,
    )
    def test_reference_table_uniqueness(self, table_name):
        db_session = sessionmaker(bind=self.store.engine)
        session = db_session()

        # Add object of given type
        table = getattr(self.store.db_classes, table_name)
        obj = table(name="Blah")
        session.add(obj)
        session.flush()

        with pytest.raises(exc.IntegrityError):
            obj = table(name="Blah")
            session.add(obj)
            session.flush()

    def test_privacy_uniqueness(self):
        db_session = sessionmaker(bind=self.store.engine)
        session = db_session()

        # Add privacy
        obj = self.store.db_classes.Privacy(name="Blah", level=0)
        session.add(obj)
        session.flush()

        # Try adding with same name but different level - should still fail
        with pytest.raises(exc.IntegrityError):
            obj = self.store.db_classes.Privacy(name="Blah", level=20)
            session.add(obj)
            session.flush()

    def test_platform_uniqueness(self):
        with self.store.session_scope():
            change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id
            pt_id = self.store.add_to_platform_types(
                "PlatformType1", change_id=change_id
            ).platform_type_id
            nat_id = self.store.add_to_nationalities("UK", change_id=change_id).nationality_id
            priv_id = self.store.add_to_privacies("Private", 0, change_id=change_id).privacy_id

        db_session = sessionmaker(bind=self.store.engine)
        session = db_session()

        # Add privacy
        obj = self.store.db_classes.Platform(
            name="Platform1",
            identifier="P123",
            nationality_id=nat_id,
            platform_type_id=pt_id,
            privacy_id=priv_id,
        )
        session.add(obj)
        session.flush()

        # Try adding with same name but different level - should still fail
        with pytest.raises(exc.IntegrityError):
            obj = self.store.db_classes.Platform(
                name="Platform1",
                identifier="P123",
                nationality_id=nat_id,
                platform_type_id=pt_id,
                privacy_id=priv_id,
            )
            session.add(obj)
            session.flush()

    def test_sensor_uniqueness(self):
        with self.store.session_scope():
            change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id
            self.store.add_to_platform_types("PlatformType1", change_id=change_id).platform_type_id
            self.store.add_to_nationalities("UK", change_id=change_id).nationality_id
            priv_id = self.store.add_to_privacies("Private", 0, change_id=change_id).privacy_id
            st_id = self.store.add_to_sensor_types(
                "SensorType1", change_id=change_id
            ).sensor_type_id
            plat_id = self.store.add_to_platforms(
                "Platform1", "P123", "UK", "PlatformType1", "Private", change_id=change_id
            ).platform_id
        db_session = sessionmaker(bind=self.store.engine)
        session = db_session()

        obj = self.store.db_classes.Sensor(
            name="Sensor1", sensor_type_id=st_id, host=plat_id, privacy_id=priv_id
        )
        session.add(obj)
        session.flush()

        # Try adding with same name but different level - should still fail
        with pytest.raises(exc.IntegrityError):
            obj = self.store.db_classes.Sensor(
                name="Sensor1", sensor_type_id=st_id, host=plat_id, privacy_id=priv_id
            )
            session.add(obj)
            session.flush()

    def test_datafile_uniqueness(self):
        with self.store.session_scope():
            change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id
            priv_id = self.store.add_to_privacies("Private", 0, change_id=change_id).privacy_id
            dft_id = self.store.add_to_datafile_types(
                "DatafileType1", change_id=change_id
            ).datafile_type_id
        db_session = sessionmaker(bind=self.store.engine)
        session = db_session()

        obj = self.store.db_classes.Datafile(
            simulated=True,
            privacy_id=priv_id,
            datafile_type_id=dft_id,
            reference="Test",
            size=1234,
            hash="TestHash",
            url="TestURL",
        )
        session.add(obj)
        session.flush()

        # Try adding with same name but different level - should still fail
        with pytest.raises(exc.IntegrityError):
            obj = self.store.db_classes.Datafile(
                simulated=True,
                privacy_id=priv_id,
                datafile_type_id=dft_id,
                reference="Test",
                size=1234,
                hash="TestHash",
                url="TestURL",
            )
            session.add(obj)
            session.flush()


class TestNotEmptyStringSQLite(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def test_platform_name_empty(self):
        with self.store.session_scope():
            change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id
            pt_id = self.store.add_to_platform_types(
                "PlatformType1", change_id=change_id
            ).platform_type_id
            nat_id = self.store.add_to_nationalities("UK", change_id=change_id).nationality_id
            priv_id = self.store.add_to_privacies("Private", 0, change_id=change_id).privacy_id

        db_session = sessionmaker(bind=self.store.engine)
        session = db_session()

        with pytest.raises(exc.IntegrityError):
            obj = self.store.db_classes.Platform(
                name="",
                identifier="P123",
                nationality_id=nat_id,
                platform_type_id=pt_id,
                privacy_id=priv_id,
            )
            session.add(obj)
            session.flush()

    def test_platform_identifier_empty(self):
        with self.store.session_scope():
            change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id
            pt_id = self.store.add_to_platform_types(
                "PlatformType1", change_id=change_id
            ).platform_type_id
            nat_id = self.store.add_to_nationalities("UK", change_id=change_id).nationality_id
            priv_id = self.store.add_to_privacies("Private", 0, change_id=change_id).privacy_id

        db_session = sessionmaker(bind=self.store.engine)
        session = db_session()

        with pytest.raises(exc.IntegrityError):
            obj = self.store.db_classes.Platform(
                name="TestPlatform",
                identifier="",
                nationality_id=nat_id,
                platform_type_id=pt_id,
                privacy_id=priv_id,
            )
            session.add(obj)
            session.flush()

    def test_sensor_name_empty(self):
        with self.store.session_scope():
            change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id
            self.store.add_to_platform_types("PlatformType1", change_id=change_id).platform_type_id
            self.store.add_to_nationalities("UK", change_id=change_id).nationality_id
            priv_id = self.store.add_to_privacies("Private", 0, change_id=change_id).privacy_id
            st_id = self.store.add_to_sensor_types(
                "SensorType1", change_id=change_id
            ).sensor_type_id
            plat_id = self.store.add_to_platforms(
                "Platform1", "P123", "UK", "PlatformType1", "Private", change_id=change_id
            ).platform_id
        db_session = sessionmaker(bind=self.store.engine)
        session = db_session()

        with pytest.raises(exc.IntegrityError):
            obj = self.store.db_classes.Sensor(
                name="", sensor_type_id=st_id, host=plat_id, privacy_id=priv_id
            )
            session.add(obj)
            session.flush()

    def test_datafile_hash_empty(self):
        with self.store.session_scope():
            change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id
            priv_id = self.store.add_to_privacies("Private", 0, change_id=change_id).privacy_id
            dft_id = self.store.add_to_datafile_types(
                "DatafileType1", change_id=change_id
            ).datafile_type_id
        db_session = sessionmaker(bind=self.store.engine)
        session = db_session()

        with pytest.raises(exc.IntegrityError):
            obj = self.store.db_classes.Datafile(
                simulated=True,
                privacy_id=priv_id,
                datafile_type_id=dft_id,
                reference="Test",
                size=1234,
                hash="",
                url="TestURL",
            )
            session.add(obj)
            session.flush()


@pytest.mark.postgres
class TestNotEmptyStringPostgres(unittest.TestCase):
    def setUp(self):
        self.postgres = None

        try:
            self.postgres = Postgresql(
                database="test",
                host="localhost",
                user="postgres",
                password="postgres",
                port=55527,
            )
        except RuntimeError:
            raise Exception("Testing Postgres server could not be started/accessed")

        self.store = DataStore(
            db_name="test",
            db_host="localhost",
            db_username="postgres",
            db_password="postgres",
            db_port=55527,
            db_type="postgres",
        )
        self.store.initialise()

    def tearDown(self):
        try:
            self.postgres.stop()
        except AttributeError:
            return

    def test_platform_name_empty(self):
        with self.store.session_scope():
            change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id
            pt_id = self.store.add_to_platform_types(
                "PlatformType1", change_id=change_id
            ).platform_type_id
            nat_id = self.store.add_to_nationalities("UK", change_id=change_id).nationality_id
            priv_id = self.store.add_to_privacies("Private", 0, change_id=change_id).privacy_id

        db_session = sessionmaker(bind=self.store.engine)
        session = db_session()

        with pytest.raises(exc.IntegrityError):
            obj = self.store.db_classes.Platform(
                name="",
                identifier="P123",
                nationality_id=nat_id,
                platform_type_id=pt_id,
                privacy_id=priv_id,
            )
            session.add(obj)
            session.flush()

    def test_platform_identifier_empty(self):
        with self.store.session_scope():
            change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id
            pt_id = self.store.add_to_platform_types(
                "PlatformType1", change_id=change_id
            ).platform_type_id
            nat_id = self.store.add_to_nationalities("UK", change_id=change_id).nationality_id
            priv_id = self.store.add_to_privacies("Private", 0, change_id=change_id).privacy_id

        db_session = sessionmaker(bind=self.store.engine)
        session = db_session()

        with pytest.raises(exc.IntegrityError):
            obj = self.store.db_classes.Platform(
                name="TestPlatform",
                identifier="",
                nationality_id=nat_id,
                platform_type_id=pt_id,
                privacy_id=priv_id,
            )
            session.add(obj)
            session.flush()

    def test_sensor_name_empty(self):
        with self.store.session_scope():
            change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id
            self.store.add_to_platform_types("PlatformType1", change_id=change_id).platform_type_id
            self.store.add_to_nationalities("UK", change_id=change_id).nationality_id
            priv_id = self.store.add_to_privacies("Private", 0, change_id=change_id).privacy_id
            st_id = self.store.add_to_sensor_types(
                "SensorType1", change_id=change_id
            ).sensor_type_id
            plat_id = self.store.add_to_platforms(
                "Platform1", "P123", "UK", "PlatformType1", "Private", change_id=change_id
            ).platform_id
        db_session = sessionmaker(bind=self.store.engine)
        session = db_session()

        with pytest.raises(exc.IntegrityError):
            obj = self.store.db_classes.Sensor(
                name="", sensor_type_id=st_id, host=plat_id, privacy_id=priv_id
            )
            session.add(obj)
            session.flush()

    def test_datafile_hash_empty(self):
        with self.store.session_scope():
            change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id
            priv_id = self.store.add_to_privacies("Private", 0, change_id=change_id).privacy_id
            dft_id = self.store.add_to_datafile_types(
                "DatafileType1", change_id=change_id
            ).datafile_type_id
        db_session = sessionmaker(bind=self.store.engine)
        session = db_session()

        with pytest.raises(exc.IntegrityError):
            obj = self.store.db_classes.Datafile(
                simulated=True,
                privacy_id=priv_id,
                datafile_type_id=dft_id,
                reference="Test",
                size=1234,
                hash="",
                url="TestURL",
            )
            session.add(obj)
            session.flush()
