import json

import pytest

from pepys_import.core.store.data_store import DataStore
from pepys_import.utils.sqlalchemy_utils import (
    get_lowest_privacy,
    get_primary_key_for_table,
    sqlalchemy_object_to_json,
)


def test_sqlalchemy_object_to_json():
    ds = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    ds.initialise()

    with ds.session_scope():
        ds.populate_reference()
        ds.populate_metadata()

        platform_obj = (
            ds.session.query(ds.db_classes.Platform)
            .filter(ds.db_classes.Platform.name == "ADRI")
            .one()
        )

        output_json = sqlalchemy_object_to_json(platform_obj)

        output_dict = json.loads(output_json)

        print(output_dict)

        assert output_dict["name"] == "ADRI"
        assert output_dict["identifier"] == "A643"
        assert output_dict["trigraph"] == "None"
        assert output_dict["quadgraph"] == "None"

        assert "platform_id" in output_dict
        assert "nationality_id" in output_dict
        assert "platform_type_id" in output_dict
        assert "privacy_id" in output_dict
        assert "created_date" in output_dict


def test_get_lowest_privacy():
    ds = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    ds.initialise()

    with ds.session_scope():
        ds.populate_reference()
        ds.populate_metadata()

    with ds.session_scope():
        lowest_priv = get_lowest_privacy(ds)

    assert lowest_priv == "Public"


@pytest.mark.parametrize(
    "table_name,pri_key_name",
    [
        ("Platform", "platform_id"),
        ("State", "state_id"),
        ("PlatformType", "platform_type_id"),
        ("SerialParticipant", "serial_participant_id"),
    ],
)
def test_get_primary_key_for_table(table_name, pri_key_name):
    ds = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    ds.initialise()

    table_obj = getattr(ds.db_classes, table_name)

    assert get_primary_key_for_table(table_obj) == pri_key_name
