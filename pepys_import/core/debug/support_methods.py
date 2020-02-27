from sqlalchemy.orm import Session
from tabulate import tabulate

from pepys_import.core.store.sqlite_db import (
    State,
    Platform,
    Sensor,
    Nationality,
    PlatformType,
    Datafile,
)


def count_states(data_store):
    """
    return the number of State records present in the database
    """
    session = Session(bind=data_store.engine)
    num_of_states = session.query(State).count()
    return num_of_states


def list_states(data_store):
    """
    return the number of State records present in the database
    """
    session = Session(bind=data_store.engine)
    result = session.query(State).all()

    headers = (
        "Id",
        "Time",
        "Sensor",
        "Location",
        "heading",
        "Speed",
        "datafile",
        "privacy",
    )

    rows = []
    for row in result:
        rows.append(
            [
                row.state_id,
                row.time,
                row.sensor_id,
                row.location,
                row.heading,
                row.speed,
                row.source_id,
                row.privacy_id,
            ]
        )
    res = tabulate(rows, headers=headers)

    return res


def list_platforms(data_store):
    """
    return the number of platform records present in the database
    """
    session = Session(bind=data_store.engine)
    result = session.query(Platform).all()

    headers = ["Id", "Name", "Platform-Type", "Nationality"]

    rows = []
    for row in result:
        rows.append(
            [row.platform_id, row.name, row.platform_type_id, row.nationality_id,]
        )
    res = tabulate(rows, headers=headers)

    return res


def list_sensors(data_store):
    """
    return the number of sensor records present in the database
    """
    session = Session(bind=data_store.engine)
    result = session.query(Sensor).all()

    headers = ["Id", "Name", "Sensor-Type", "Platform-id"]

    rows = []
    for row in result:
        rows.append([row.sensor_id, row.name, row.sensor_type_id, row.host])
    res = tabulate(rows, headers=headers)

    return res


def list_nationalities(data_store):
    """
    return the number of nationality records present in the database
    """
    session = Session(bind=data_store.engine)
    result = session.query(Nationality).all()

    headers = ["Id", "Name"]

    rows = []
    for row in result:
        rows.append([row.nationality_id, row.name])
    res = tabulate(rows, headers=headers)

    return res


def list_datafiles(data_store):
    """
    return the number of nationality records present in the database
    """
    session = Session(bind=data_store.engine)
    result = session.query(Datafile).all()

    headers = ["Id", "Reference"]

    rows = []
    for row in result:
        rows.append([row.datafile_id, row.reference])
    res = tabulate(rows, headers=headers)

    return res


def list_platform_types(data_store):
    """
    return the number of nationality records present in the database
    """
    session = Session(bind=data_store.engine)
    result = session.query(PlatformType).all()

    headers = ["Id", "Name"]

    rows = []
    for row in result:
        rows.append([row.platform_type_id, row.name])
    res = tabulate(rows, headers=headers)

    return res


def list_all(data_store):
    print("Datafiles")
    print(list_datafiles(data_store))
    print("")

    print("Nationalities")
    print(list_nationalities(data_store))
    print("")

    print("Platform-Types")
    print(list_platform_types(data_store))
    print("")

    print("Platforms")
    print(list_platforms(data_store))
    print("")

    print("Sensors")
    print(list_sensors(data_store))
    print("")

    print("States:")
    print(list_states(data_store))
    print("")
