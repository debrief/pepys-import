import pytest
from sqlalchemy import exc
from sqlalchemy.orm.session import sessionmaker

from pepys_import.core.store import constants
from pepys_import.core.store.data_store import DataStore

# All reference tables excluding GeometrySubType which can't be tested in this simple way
REFERENCE_TABLES = [
    "SensorType",
    "PlatformType",
    "Nationality",
    "GeometryType",
    "User",
    "UnitType",
    "Privacy",
    "DatafileType",
    "MediaType",
    "CommentType",
    "CommodityType",
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

        # Add sensor type Blah
        table = getattr(self.store.db_classes, table_name)
        sensor_type = table(name="Blah")
        session.add(sensor_type)
        session.flush()

        with pytest.raises(exc.IntegrityError):
            sensor_type = table(name="Blah")
            session.add(sensor_type)
            session.flush()
