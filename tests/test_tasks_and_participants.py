from datetime import datetime

from pepys_import.core.store.data_store import DataStore


def create_example_tasks(ds, create_participants=False):
    ds.initialise()
    with ds.session_scope():
        ds.populate_reference()
        ds.populate_metadata()

    with ds.session_scope():
        change_id = ds.add_to_changes("Test", datetime.utcnow(), "Test data").change_id
        jw = ds.add_to_tasks(
            "Joint Warrier",
            start=datetime(1900, 1, 1, 0, 0, 0),
            end=datetime(2100, 1, 1, 0, 0, 0),
            privacy="Private",
            change_id=change_id,
        )

        ae = ds.add_to_tasks(
            "Another Exercise",
            start=datetime(1900, 1, 1, 0, 0, 0),
            end=datetime(2100, 1, 1, 0, 0, 0),
            privacy="Private",
            change_id=change_id,
        )

        ds.add_to_tasks(
            "Another Exercise Child 1",
            start=datetime(2018, 1, 1, 0, 0, 0),
            end=datetime(2019, 1, 1, 0, 0, 0),
            privacy="Private",
            parent=ae,
            change_id=change_id,
        )

        ae = ds.add_to_tasks(
            "A Third Exercise",
            start=datetime(1900, 1, 1, 0, 0, 0),
            end=datetime(2100, 1, 1, 0, 0, 0),
            privacy="Private",
            change_id=change_id,
        )

        jw_20_02 = ds.add_to_tasks(
            "Joint Warrier 20/02",
            start=datetime(2020, 2, 1, 0, 0, 0),
            end=datetime(2020, 1, 28, 0, 0, 0),
            privacy="Very Private",
            change_id=change_id,
            parent=jw,
        )

        ds.add_to_tasks(
            "J05020 - NAVCOMEX",
            start=datetime(2020, 2, 3, 7, 0, 0),
            end=datetime(2020, 1, 4, 12, 0, 0),
            privacy="Private",
            change_id=change_id,
            parent=jw_20_02,
        )

        ds.add_to_tasks(
            "J05084 - ADEX 324",
            start=datetime(2020, 2, 6, 9, 0, 0),
            end=datetime(2020, 1, 8, 14, 0, 0),
            privacy="Private",
            change_id=change_id,
            parent=jw_20_02,
        )

        j_05110 = ds.add_to_tasks(
            "J05110 - CASEX E3",
            start=datetime(2020, 2, 23, 9, 0, 0),
            end=datetime(2020, 1, 25, 15, 0, 0),
            privacy="Private",
            change_id=change_id,
            parent=jw_20_02,
        )

        if create_participants:
            plat1 = ds.session.query(ds.db_classes.Platform).all()[0]
            plat2 = ds.session.query(ds.db_classes.Platform).all()[1]

            priv = ds.session.query(ds.db_classes.Privacy).all()[0]

            p1 = ds.db_classes.Participant(
                platform_id=plat1.platform_id, privacy_id=priv.privacy_id, force="Red"
            )
            p2 = ds.db_classes.Participant(
                platform_id=plat2.platform_id,
                privacy_id=priv.privacy_id,
                start=datetime(2021, 3, 21, 9, 0, 0),
                force="Blue",
            )

            j_05110.add_participant(p1)
            j_05110.add_participant(p2)


def test_create_tasks():
    ds = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    create_example_tasks(ds)

    with ds.session_scope():
        all_tasks = ds.session.query(ds.db_classes.Task).all()

        assert len(all_tasks) == 8

        # Check the tree structure for a task, going from bottom to top
        # including names and levels
        results = (
            ds.session.query(ds.db_classes.Task)
            .filter(ds.db_classes.Task.name == "J05110 - CASEX E3")
            .all()
        )

        assert len(results) == 1
        bottom_task = results[0]

        assert bottom_task.level == 2

        middle_task = bottom_task.parent
        assert middle_task.name == "Joint Warrier 20/02"
        assert bottom_task.parent_name == middle_task.name
        assert bottom_task.parent_id == middle_task.task_id
        assert middle_task.level == 1

        top_task = middle_task.parent
        assert top_task.name == "Joint Warrier"
        assert middle_task.parent_name == top_task.name
        assert middle_task.parent_id == top_task.task_id
        assert top_task.level == 0


def test_create_participants():
    ds = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    create_example_tasks(ds, create_participants=True)

    all_participants = ds.session.query(ds.db_classes.Participant).all()

    assert len(all_participants) == 2

    p1 = all_participants[0]

    assert p1.task.name == "J05110 - CASEX E3"
    assert p1.platform.name == "ADRI"


def test_delete_task_deletes_children_and_participants():
    ds = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    create_example_tasks(ds, create_participants=True)

    with ds.session_scope():
        task = (
            ds.session.query(ds.db_classes.Task)
            .filter(ds.db_classes.Task.name == "Joint Warrier 20/02")
            .all()[0]
        )

        ds.session.delete(task)

    with ds.session_scope():
        all_tasks = ds.session.query(ds.db_classes.Task).all()

        # Check that the task and it's children have been deleted
        assert len(all_tasks) == 4

        # Should still have parent
        parent_task = (
            ds.session.query(ds.db_classes.Task)
            .filter(ds.db_classes.Task.name == "Joint Warrier")
            .all()
        )
        assert len(parent_task) == 1

        # The only participants were those under one of the deleted tasks, so they should be deleted too
        all_participants = ds.session.query(ds.db_classes.Participant).all()
        assert len(all_participants) == 0

        # But the platforms the participants reference shouldn't be deleted
        all_platforms = ds.session.query(ds.db_classes.Platform).all()
        assert len(all_platforms) == 4
