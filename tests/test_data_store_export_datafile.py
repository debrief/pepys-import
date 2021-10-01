import os
import unittest
from uuid import uuid4

import pytest
from testing.postgresql import Postgresql

from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor

FILE_PATH = os.path.dirname(__file__)
CURRENT_DIR = os.getcwd()
DATA_PATH = os.path.join(FILE_PATH, "sample_data/track_files/rep_data/rep_test1.rep")


@pytest.mark.postgres
class DataStoreExportPostGISDBTestCase(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(CURRENT_DIR, "export_test.rep")
        self.store = None
        try:
            self.store = Postgresql(
                database="test",
                host="localhost",
                user="postgres",
                password="postgres",
                port=55527,
            )
        except RuntimeError:
            raise Exception("Creating database schema in testing Postgres database failed")

    def tearDown(self) -> None:
        if os.path.exists(self.path):
            os.remove(self.path)
        try:
            self.store.stop()
        except AttributeError:
            return

    def test_postgres_export_datafile(self):
        if self.store is None:
            self.skipTest("Postgres is not available. Test is skipping")

        data_store = DataStore(
            db_username="postgres",
            db_password="postgres",
            db_host="localhost",
            db_port=55527,
            db_name="test",
            db_type="postgres",
        )
        data_store.initialise()

        # Parse the file
        processor = FileProcessor(archive=False)
        processor.load_importers_dynamically()
        processor.process(DATA_PATH, data_store, False)

        with data_store.session_scope():
            datafiles = data_store.get_all_datafiles()
            selected_datafile_id = datafiles[0].datafile_id
            data_store.export_datafile(selected_datafile_id, self.path)

            # Fetch data from the exported file
            with open(self.path, "r") as file:
                data = file.read().split("\n")

            print("-" * 80)
            for line in data:
                print(line)
            print("-" * 80)
            print(data)
            print("-" * 80)

            assert (
                "100112 115800.000\tSUBJECT\tAA\t60 23 40.25 N\t000 01 25.86 E\t109.08\t6.00\t0.0"
                in data
            )
            assert (
                "100112 115800.000\tSEARCH_PLATFORM\tAA\t60 28 56.02 N\t000 35 59.68 E\t179.84\t8.00\t0.0"
                in data
            )
            assert ";NARRATIVE:\t100112 115800.000\tSENSOR\tContact detected on TA" in data
            assert (
                ";NARRATIVE2:\t100112 121200.000\tSEARCH_PLATFORM\tOBSERVATION\tSUBJECT lost on TA"
                in data
            )
            assert (
                ";SENSOR2:\t100112 115800.000\tSENSOR\t@@\tNULL\t252.85\t106.83\t123.40\t432.10\tTA\tN/A"
                in data
            )
            assert (
                ";SENSOR2:\t100112 120200.000\tSENSOR\t@@\tNULL\t251.58\t108.42\tNULL\tNULL\tTA\tN/A"
                in data
            )

            assert ";SENSOR:\t100112 120400.000\tSENSOR\t@@\tNULL\t251.99\t107.69\tTA\tN/A" in data


class DataStoreExportSpatiaLiteTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.path = os.path.join(CURRENT_DIR, "export_test.rep")
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

        # Parse the file
        processor = FileProcessor(archive=False)
        processor.load_importers_dynamically()
        processor.process(DATA_PATH, self.store, False)

    def tearDown(self) -> None:
        if os.path.exists(self.path):
            os.remove(self.path)

    def test_sqlite_export_datafile(self):
        with self.store.session_scope():
            datafiles = self.store.get_all_datafiles()
            selected_datafile_id = datafiles[0].datafile_id
            self.store.export_datafile(selected_datafile_id, self.path)

            # Fetch data from the exported file
            with open(self.path, "r") as file:
                data = file.read().split("\n")
                print(data)

            assert (
                "100112 115800.000\tSUBJECT\tAA\t60 23 40.25 N\t000 01 25.86 E\t109.08\t6.00\t0.0"
                in data
            )
            assert (
                "100112 115800.000\tSEARCH_PLATFORM\tAA\t60 28 56.02 N\t000 35 59.68 E\t179.84\t8.00\t0.0"
                in data
            )
            assert ";NARRATIVE:\t100112 115800.000\tSENSOR\tContact detected on TA" in data
            assert (
                ";NARRATIVE2:\t100112 121200.000\tSEARCH_PLATFORM\tOBSERVATION\tSUBJECT lost on TA"
                in data
            )
            assert (
                ";SENSOR2:\t100112 115800.000\tSENSOR\t@@\tNULL\t252.85\t106.83\t123.40\t432.10\tTA\tN/A"
                in data
            )
            assert (
                ";SENSOR2:\t100112 120200.000\tSENSOR\t@@\tNULL\t251.58\t108.42\tNULL\tNULL\tTA\tN/A"
                in data
            )
            assert ";SENSOR:\t100112 120400.000\tSENSOR\t@@\tNULL\t251.99\t107.69\tTA\tN/A" in data

    def test_sqlite_export_datafile_just_comments(self):
        with self.store.session_scope():
            datafiles = self.store.get_all_datafiles()
            selected_datafile_id = datafiles[0].datafile_id
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            selected_platform_id = platforms[0].platform_id
            self.store.export_datafile(
                selected_datafile_id, self.path, platform_id=selected_platform_id
            )

            # Fetch data from the exported file
            with open(self.path, "r") as file:
                data = file.read().split("\n")
                print(data)

            assert ";NARRATIVE:\t100112 115800.000\tSENSOR\tContact detected on TA" in data
            assert (
                ";NARRATIVE:\t100112 120000.000\tSENSOR\tContact identified as SUBJECT on TA"
                in data
            )
            assert (
                ";NARRATIVE:\t100112 120000.000\tSENSOR\tContact identified as SUBJECT on TA"
                in data
            )
            assert ";NARRATIVE:\t100112 120200.000\tSENSOR\tSUBJECT weakening on TA" in data
            assert ";NARRATIVE:\t100112 120400.000\tSENSOR\tSUBJECT lost on TA" in data
            assert ";NARRATIVE:\t100112 120600.000\tSENSOR\tSUBJECT regained on TA" in data


class CachePlatformAndSensorNamesTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.path = os.path.join(CURRENT_DIR, "export_test.rep")
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

        # Parse the file
        processor = FileProcessor(archive=False)
        processor.load_importers_dynamically()
        processor.process(DATA_PATH, self.store, False)

    def test_cached_comment_type_exception(self):
        with self.store.session_scope():
            with pytest.raises(Exception) as exception:
                uuid = uuid4()
                self.store.get_cached_comment_type_name(comment_type_id=uuid)
            assert f"No Comment Type found with Comment type id: {uuid}" in str(exception.value)

    def test_cached_sensor_name_exception(self):
        with self.store.session_scope():
            with pytest.raises(Exception) as exception:
                uuid = uuid4()
                self.store.get_cached_sensor_name(sensor_id=uuid)
            assert f"No Sensor found with sensor id: {uuid}" in str(exception.value)

    def test_cached_platform_name_exceptions(self):
        with self.store.session_scope():
            with pytest.raises(Exception) as exception:
                self.store.get_cached_platform_name()
            assert (
                "Either 'sensor_id' or 'platform_id' has to be provided to get 'platform name'"
                in str(exception.value)
            )
            with pytest.raises(Exception) as exception:
                uuid = uuid4()
                self.store.get_cached_platform_name(sensor_id=uuid)
            assert f"No Sensor found with sensor id: {uuid}" in str(exception.value)
            with pytest.raises(Exception) as exception:
                uuid = uuid4()
                self.store.get_cached_platform_name(platform_id=uuid)
            assert f"No Platform found with platform id: {uuid}" in str(exception.value)


class FindRelatedDatafileObjectsTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

        # Parse the file
        processor = FileProcessor(archive=False)
        processor.load_importers_dynamically()
        processor.process(DATA_PATH, self.store, False)

    def test_find_min_and_max_date_incorrect_table(self):
        Datafile = self.store.db_classes.Datafile
        with pytest.raises(ValueError):
            self.store.find_min_and_max_date(Datafile, Datafile.reference, "TEST")

    def test_find_min_and_max_date(self):
        State = self.store.db_classes.State
        Contact = self.store.db_classes.Contact
        Comment = self.store.db_classes.Comment

        with self.store.session_scope():
            platform = self.store.search_platform("SUBJECT", "UK", "123")
            sensor_id = self.store.search_sensor("SENSOR-1", platform.platform_id).sensor_id

            state_values = self.store.find_min_and_max_date(State, State.sensor_id, sensor_id)
            assert len(state_values) == 3
            assert str(state_values[0]) == "2010-01-12 11:58:00"
            assert str(state_values[1]) == "2010-01-12 12:14:00"

            platform = self.store.search_platform("SENSOR", "UK", "123")
            sensor_id = self.store.search_sensor("TA", platform.platform_id).sensor_id

            contact_values = self.store.find_min_and_max_date(Contact, Contact.sensor_id, sensor_id)
            print(contact_values)
            assert len(contact_values) == 3
            assert str(contact_values[0]) == "2010-01-12 11:58:00"
            assert str(contact_values[1]) == "2010-01-12 12:06:00"

            platform_id = self.store.search_platform("SEARCH_PLATFORM", "UK", "123").platform_id
            comment_values = self.store.find_min_and_max_date(
                Comment, Comment.platform_id, platform_id
            )

            assert len(comment_values) == 3
            assert str(comment_values[0]) == "2010-01-12 12:10:00"
            assert str(comment_values[1]) == "2010-01-12 12:12:00"

            assert state_values[2] == contact_values[2] == comment_values[2]

    def test_find_related_datafile_objects_of_comments(self):
        with self.store.session_scope():
            platform_id = self.store.search_platform("SEARCH_PLATFORM", "UK", "123").platform_id
            objects = self.store.find_related_datafile_objects(platform_id, sensors_dict={})
            assert len(objects) == 1
            assert objects[0]["name"] == "Comment"
            assert objects[0]["filename"] == "rep_test1.rep"
            assert str(objects[0]["min"]) == "2010-01-12 12:10:00"
            assert str(objects[0]["max"]) == "2010-01-12 12:12:00"

    def test_find_related_datafile_objects_of_states_and_contacts(self):
        with self.store.session_scope():
            platform1 = self.store.search_platform("SUBJECT", "UK", "123")
            platform2 = self.store.search_platform("SENSOR", "UK", "123")

            sensors_dict = {
                "SENSOR-1": self.store.search_sensor("SENSOR-1", platform1.platform_id).sensor_id,
                "TA": self.store.search_sensor("TA", platform2.platform_id).sensor_id,
            }
            objects = self.store.find_related_datafile_objects(uuid4(), sensors_dict=sensors_dict)
            print(objects)
            assert len(objects) == 2
            assert objects[0]["name"] == "SENSOR-1"
            assert objects[0]["filename"] == "rep_test1.rep"
            assert str(objects[0]["min"]) == "2010-01-12 11:58:00"
            assert str(objects[0]["max"]) == "2010-01-12 12:14:00"

            assert objects[1]["name"] == "TA"
            assert objects[1]["filename"] == "rep_test1.rep"
            assert str(objects[1]["min"]) == "2010-01-12 11:58:00"
            assert str(objects[1]["max"]) == "2010-01-12 12:06:00"


if __name__ == "__main__":
    unittest.main()
