from pepys_admin.maintenance.utils import (
    get_system_name_mappings,
    get_table_titles,
    remove_duplicates_and_nones,
)


def test_get_table_titles():
    fields = ["nationality_name", "name", "platform_type_name", "other"]

    titles = get_table_titles(fields)

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

    assert remove_duplicates_and_nones(input_list) == ["a", "b", "c"]

    input_list_2 = [None, None, None, None, None]

    assert remove_duplicates_and_nones(input_list_2) == []

    input_list_3 = [1, 1, 1, 1, 1, 1, 1, None]

    assert remove_duplicates_and_nones(input_list_3) == [1]
