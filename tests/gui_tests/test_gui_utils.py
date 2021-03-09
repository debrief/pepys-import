import unittest
from datetime import date, datetime

from freezegun import freeze_time

from pepys_admin.maintenance.utils import (
    convert_relative_time_filter_to_query,
    create_time_filter_dict,
    get_display_names,
    get_system_name_mappings,
    remove_duplicates_and_nones,
    table_has_any_timestamp_fields,
)
from pepys_import.core.store.data_store import DataStore


def test_get_display_names():
    fields = ["nationality_name", "name", "platform_type_name", "other"]

    titles = get_display_names(fields, capitalized=True)

    assert titles == ["Nationality", "Name", "Platform type", "Other"]


def test_get_system_name_mappings():
    column_data = {
        "disp_name_1": {"system_name": "sys_name_1"},
        "disp_name_2": {"values": [1, 2, 3], "system_name": "sys_name_2"},
        "disp_name_3": {"type": "string"},
    }

    system_name_to_display_name, display_name_to_system_name = get_system_name_mappings(column_data)

    assert len(system_name_to_display_name) == len(display_name_to_system_name)

    assert system_name_to_display_name["sys_name_1"] == "disp_name_1"
    assert system_name_to_display_name["sys_name_2"] == "disp_name_2"
    assert system_name_to_display_name["disp_name_3"] == "disp_name_3"

    assert display_name_to_system_name["disp_name_1"] == "sys_name_1"
    assert display_name_to_system_name["disp_name_2"] == "sys_name_2"
    assert display_name_to_system_name["disp_name_3"] == "disp_name_3"


def test_remove_duplicates_and_nones():
    input_list = ["a", "b", None, "c", "a", None]

    assert sorted(remove_duplicates_and_nones(input_list)) == ["a", "b", "c"]

    input_list_2 = [None, None, None, None, None]

    assert remove_duplicates_and_nones(input_list_2) == []

    input_list_3 = [1, 1, 1, 1, 1, 1, 1, None]

    assert remove_duplicates_and_nones(input_list_3) == [1]


@freeze_time("2021-03-09 12:00:00")
def test_create_time_filter_dict():
    filter_dict = create_time_filter_dict()
    assert filter_dict["In past 24 hours"] == (
        datetime(2021, 3, 8, hour=12, minute=0),
        datetime(2021, 3, 9, hour=12, minute=0),
    )
    assert filter_dict["In next 24 hours"] == (
        datetime(2021, 3, 9, hour=12, minute=0),
        datetime(2021, 3, 10, hour=12, minute=0),
    )
    assert filter_dict["Yesterday"] == (date(2021, 3, 8), date(2021, 3, 9))
    assert filter_dict["Day before yesterday"] == (date(2021, 3, 7), date(2021, 3, 8))
    assert filter_dict["Today"] == (date(2021, 3, 9), date(2021, 3, 10))
    assert filter_dict["Tomorrow"] == (date(2021, 3, 10), date(2021, 3, 11))


def test_table_has_any_timestamp_fields():
    data_store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    data_store.initialise()
    assert table_has_any_timestamp_fields(data_store.db_classes.Task) is True
    assert table_has_any_timestamp_fields(data_store.db_classes.State) is True

    assert table_has_any_timestamp_fields(data_store.db_classes.Platform) is False
    assert table_has_any_timestamp_fields(data_store.db_classes.Sensor) is False


@freeze_time("2021-03-09 12:00:00")
class RelativeTimeFilterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()
        # Create objects
        with self.store.session_scope():
            change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id
            nationality = self.store.add_to_nationalities("test_nationality", change_id).name
            platform_type = self.store.add_to_platform_types("test_platform_type", change_id).name
            sensor_type = self.store.add_to_sensor_types("test_sensor_type", change_id).name
            privacy = self.store.add_to_privacies("test_privacy", 0, change_id)
            privacy = privacy.name
            self.file = self.store.get_datafile("test_file", "csv", 0, "HASHED", change_id, privacy)
            self.platform = self.store.get_platform(
                platform_name="Test Platform",
                nationality=nationality,
                platform_type=platform_type,
                privacy=privacy,
                change_id=change_id,
            )
            self.sensor = self.platform.get_sensor(
                self.store, "gps", sensor_type, change_id=change_id, privacy=privacy
            )
            self.store.session.expunge(self.platform)
            self.store.session.expunge(self.sensor)
            self.store.session.expunge(self.file)

    def test_convert_relative_time_filter_to_query(self):
        State = self.store.db_classes.State
        with self.store.session_scope():
            state_day_before_yesterday = State(
                sensor_id=self.sensor.sensor_id,
                source_id=self.file.datafile_id,
                sensor=self.sensor,
                platform=self.platform,
                time=datetime(2021, 3, 7, hour=20, minute=0),
            )
            state_yesterday = State(
                sensor_id=self.sensor.sensor_id,
                source_id=self.file.datafile_id,
                sensor=self.sensor,
                platform=self.platform,
                time=datetime(2021, 3, 8, hour=10, minute=0),
            )
            state_in_past_24_hours = State(
                sensor_id=self.sensor.sensor_id,
                source_id=self.file.datafile_id,
                sensor=self.sensor,
                platform=self.platform,
                time=datetime(2021, 3, 9, hour=3, minute=0),
            )
            self.store.session.add_all(
                [
                    state_day_before_yesterday,
                    state_yesterday,
                    state_in_past_24_hours,
                ]
            )
            self.store.session.flush()

            assert convert_relative_time_filter_to_query(
                "Day before yesterday", "States", self.store
            ) == [state_day_before_yesterday]
            assert convert_relative_time_filter_to_query("Yesterday", "States", self.store) == [
                state_yesterday
            ]
            assert convert_relative_time_filter_to_query(
                "In past 24 hours", "States", self.store
            ) == [state_in_past_24_hours]

    def test_convert_relative_time_filter_to_query_2(self):
        State = self.store.db_classes.State
        with self.store.session_scope():
            state_today = State(
                sensor_id=self.sensor.sensor_id,
                source_id=self.file.datafile_id,
                sensor=self.sensor,
                platform=self.platform,
                time=datetime(2021, 3, 9, hour=10, minute=0),
            )
            state_in_next_24_hours = State(
                sensor_id=self.sensor.sensor_id,
                source_id=self.file.datafile_id,
                sensor=self.sensor,
                platform=self.platform,
                time=datetime(2021, 3, 10, hour=10, minute=0),
            )
            state_tomorrow = State(
                sensor_id=self.sensor.sensor_id,
                source_id=self.file.datafile_id,
                sensor=self.sensor,
                platform=self.platform,
                time=datetime(2021, 3, 10, hour=20, minute=0),
            )
            self.store.session.add_all(
                [
                    state_today,
                    state_in_next_24_hours,
                    state_tomorrow,
                ]
            )
            self.store.session.flush()

            assert convert_relative_time_filter_to_query("Today", "States", self.store) == [
                state_today
            ]
            assert convert_relative_time_filter_to_query(
                "In next 24 hours", "States", self.store
            ) == [state_in_next_24_hours]
            # state_tomorrow is not included "in the next 24 hours", but it should when filtering by "tomorrow"
            assert set(convert_relative_time_filter_to_query("Tomorrow", "States", self.store)) == {
                state_tomorrow,
                state_in_next_24_hours,
            }
