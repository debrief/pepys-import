from datetime import datetime

from pepys_admin.utils import (
    check_sqlalchemy_results_are_equal,
    make_query_for_all_data_columns,
    make_query_for_cols,
    make_query_for_unique_cols_or_all,
    sqlalchemy_obj_to_dict,
)
from pepys_import.core.store.data_store import DataStore


def test_sqlalchemy_obj_to_dict():
    store = DataStore("", "", "", 0, db_name=":memory:", db_type="sqlite")
    store.initialise()

    with store.session_scope():
        change_id = store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id
        obj = store.add_to_sensor_types("TestSensorType", change_id)

        result = sqlalchemy_obj_to_dict(obj)

    assert "name" in result
    assert "sensor_type_id" in result
    assert result["name"] == "TestSensorType"

    assert "created_date" not in result


def test_check_sqlalchemy_results_are_equal():
    store = DataStore("", "", "", 0, db_name=":memory:", db_type="sqlite")
    store.initialise()

    with store.session_scope():
        change_id = store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id
        store.add_to_platform_types("PlatformType1", change_id)
        store.add_to_nationalities("UK", change_id)
        store.add_to_privacies("Private", 0, change_id)
        store.add_to_platforms(
            "Platform1", "123", "UK", "PlatformType1", "Private", change_id=change_id
        )
        store.add_to_platforms(
            "Platform2", "234", "UK", "PlatformType1", "Private", change_id=change_id
        )

        # Same query, same results
        result1 = store.session.query(store.db_classes.Platform).all()
        result2 = store.session.query(store.db_classes.Platform).all()
        assert check_sqlalchemy_results_are_equal(result1, result2)

        # Only part of one result set - so shouldn't be equal
        assert check_sqlalchemy_results_are_equal(result1[0:1], result2) is False

        # Different table, so different col names etc
        result3 = store.session.query(store.db_classes.PlatformType).all()
        assert check_sqlalchemy_results_are_equal(result1, result3) is False

        # Empty table, so empty results
        result4 = store.session.query(store.db_classes.Sensor).all()
        assert check_sqlalchemy_results_are_equal(result1, result4) is False


def remove_dashes(obj):
    return str(obj).replace("-", "")


def test_make_query_for_unique_cols_or_all_platform():
    store = DataStore("", "", "", 0, db_name=":memory:", db_type="sqlite")
    store.initialise()

    with store.session_scope():
        change_id = store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id
        store.add_to_platform_types("PlatformType1", change_id)
        store.add_to_nationalities("UK", change_id)
        store.add_to_privacies("Private", 0, change_id)
        store.add_to_platforms(
            "Platform1", "123", "UK", "PlatformType1", "Private", change_id=change_id
        )
        store.add_to_platforms(
            "Platform2", "123", "UK", "PlatformType1", "Private", change_id=change_id
        )

        platform_obj = (
            store.session.query(store.db_classes.Platform)
            .filter(store.db_classes.Platform.name == "Platform1")
            .all()[0]
        )

        query = make_query_for_unique_cols_or_all(
            store.db_classes.Platform, platform_obj, store.session
        )

        query_str = str(query.statement.compile(compile_kwargs={"literal_binds": True}))

        # Name, nationality_id and identifier are the unique fields that should be searched for Platform
        assert "\"Platforms\".name = 'Platform1'" in query_str
        assert "\"Platforms\".identifier = '123'" in query_str
        assert (
            f"\"Platforms\".nationality_id = '{remove_dashes(platform_obj.nationality_id)}'"
            in query_str
        )

        # Trigraph shouldn't be searched
        assert "trigraph =" not in query_str

        # PlatformType shouldn't be searched
        assert (
            f"\"Platforms\".platform_type_id = '{remove_dashes(platform_obj.platform_type_id)}'"
            not in query_str
        )


def test_make_query_for_unique_cols_or_all_synonym():
    store = DataStore("", "", "", 0, db_name=":memory:", db_type="sqlite")
    store.initialise()

    with store.session_scope():
        change_id = store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id
        pt = store.add_to_platform_types("PlatformType1", change_id)
        store.add_to_synonyms("TestTable", "TestName", pt.platform_type_id, change_id)
        store.add_to_synonyms("TestTable2", "TestName2", pt.platform_type_id, change_id)

        synonym_obj = (
            store.session.query(store.db_classes.Synonym)
            .filter(store.db_classes.Synonym.synonym == "TestName")
            .all()[0]
        )

        query = make_query_for_unique_cols_or_all(
            store.db_classes.Synonym, synonym_obj, store.session
        )

        query_str = str(query.statement.compile(compile_kwargs={"literal_binds": True}))

        print(query_str)

        # All cols should be searched
        assert "\"Synonyms\".synonym = 'TestName'" in query_str
        assert '"Synonyms"."table" = \'TestTable\'' in query_str
        assert f"\"Synonyms\".entity = '{remove_dashes(synonym_obj.entity)}'" in query_str

        assert "synonym_id =" not in query_str
        assert "created_date =" not in query_str


def test_make_query_for_cols():
    store = DataStore("", "", "", 0, db_name=":memory:", db_type="sqlite")
    store.initialise()

    with store.session_scope():
        change_id = store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id
        store.add_to_platform_types("PlatformType1", change_id)
        store.add_to_nationalities("UK", change_id)
        store.add_to_privacies("Private", 0, change_id)
        store.add_to_platforms(
            "Platform1", "123", "UK", "PlatformType1", "Private", change_id=change_id
        )
        store.add_to_platforms(
            "Platform2", "123", "UK", "PlatformType1", "Private", change_id=change_id
        )

        platform_obj = (
            store.session.query(store.db_classes.Platform)
            .filter(store.db_classes.Platform.name == "Platform1")
            .all()[0]
        )

        query = make_query_for_cols(
            store.db_classes.Platform, platform_obj, ["identifier", "name"], store.session
        )

        query_str = str(query.statement.compile(compile_kwargs={"literal_binds": True}))

        # Name field was specified, so should be in a WHERE clause
        assert "\"Platforms\".name = 'Platform1'" in query_str

        # Identifier field was specified, so should be there too
        assert "\"Platforms\".identifier = '123'" in query_str

        # Shouldn't be searching for nationality as it's not in the list
        assert (
            f"\"Platforms\".nationality_id = '{remove_dashes(platform_obj.nationality_id)}'"
            not in query_str
        )


def test_make_query_for_all_data_columns():
    store = DataStore("", "", "", 0, db_name=":memory:", db_type="sqlite")
    store.initialise()

    with store.session_scope():
        change_id = store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id
        store.add_to_platform_types("PlatformType1", change_id)
        store.add_to_nationalities("UK", change_id)
        store.add_to_privacies("Private", 0, change_id)
        store.add_to_platforms(
            "Platform1", "123", "UK", "PlatformType1", "Private", change_id=change_id
        )
        store.add_to_platforms(
            "Platform2", "123", "UK", "PlatformType1", "Private", change_id=change_id
        )

        platform_obj = (
            store.session.query(store.db_classes.Platform)
            .filter(store.db_classes.Platform.name == "Platform1")
            .all()[0]
        )

        query = make_query_for_all_data_columns(
            store.db_classes.Platform, platform_obj, store.session
        )

        query_str = str(query.statement.compile(compile_kwargs={"literal_binds": True}))

        # Check the right WHERE clauses are added
        assert "\"Platforms\".name = 'Platform1'" in query_str
        assert (
            f"\"Platforms\".nationality_id = '{remove_dashes(platform_obj.nationality_id)}'"
            in query_str
        )
        assert (
            f"\"Platforms\".platform_type_id = '{remove_dashes(platform_obj.platform_type_id)}'"
            in query_str
        )

        # Check NULL fields are ignored
        assert '"Platforms".identifier IS NULL' not in query_str

        # Check created_date isn't present in a WHERE clause
        assert "created_date =" not in query_str

        # Check we're not searching for a privacy id
        assert (
            f"\"Platforms\".privacy_id = '{remove_dashes(platform_obj.privacy_id)}'"
            not in query_str
        )
