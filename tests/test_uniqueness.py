import pytest
from sqlalchemy import exc
from sqlalchemy.orm.session import sessionmaker

from pepys_import.core.store import constants
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
    def setup_class(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    @pytest.mark.parametrize(
        "table_name", REFERENCE_TABLES,
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
