import unittest
import pytest

from pepys_import.core.formats.location import Location


def test_initial_value_none():
    loc = Location()

    assert loc.latitude is None
    assert loc.longitude is None

    assert loc.check_valid() == False


# Read-only attribute tests


def test_setting_latitude_fails():
    loc = Location()

    with pytest.raises(AttributeError):
        loc.latitude = 50


def test_setting_longitude_fails():
    loc = Location()

    with pytest.raises(AttributeError):
        loc.longitude = 50


# Decimal latitude tests


@pytest.mark.parametrize(
    "latitude",
    [pytest.param(50.23, id="valid float"), pytest.param("23.07", id="valid string")],
)
def test_setting_latitude_valid(latitude):
    loc = Location()

    assert loc.set_latitude_decimal_degrees(latitude)
    assert loc.latitude == float(latitude)


@pytest.mark.parametrize(
    "latitude",
    [
        pytest.param("Blah", id="invalid string"),
        pytest.param(5323.21, id="invalid float"),
    ],
)
def test_setting_latitude_invalid(latitude):
    loc = Location()

    assert not loc.set_latitude_decimal_degrees(latitude)
    assert len(loc.errors) == 1


@pytest.mark.parametrize(
    "longitude",
    [pytest.param(50.23, id="valid float"), pytest.param("23.67", id="valid string")],
)
def test_setting_longitude_valid(longitude):
    loc = Location()

    assert loc.set_longitude_decimal_degrees(longitude)
    assert loc.longitude == float(longitude)


@pytest.mark.parametrize(
    "longitude",
    [
        pytest.param(50543.23, id="invalid float"),
        pytest.param("blah", id="invalid string"),
    ],
)
def test_setting_longitude_invalid(longitude):
    loc = Location()

    # Assert false
    assert not loc.set_longitude_decimal_degrees(longitude)
    assert len(loc.errors) == 1
    assert loc.check_valid() == False


# DMS latitude tests
def test_setting_dms_latitude_valid():
    loc = Location()

    assert loc.set_latitude_dms(50, 32, 14, "N")
    assert loc.latitude == 50.53722222222222


dms_latitude_invalid_tests = [
    pytest.param("Blah", 32, 14, "N", id="invalid string degrees"),
    pytest.param(100, 32, 14, "N", id="invalid numeric degrees"),
    pytest.param(50, "Blah", 14, "N", id="invalid string minutes"),
    pytest.param(50, 80, 14, "N", id="invalid numeric minutes"),
    pytest.param(50, 32, "Blah", "N", id="invalid string seconds"),
    pytest.param(50, 32, 80, "N", id="invalid numeric seconds"),
    pytest.param(50, 32, 80, "R", id="invalid hemisphere - R"),
    pytest.param(50, 32, 80, "E", id="invalid hemisphere - E"),
]


@pytest.mark.parametrize(
    "degrees,minutes,seconds,hemisphere", dms_latitude_invalid_tests
)
def test_setting_dms_latitude_invalid(degrees, minutes, seconds, hemisphere):
    loc = Location()

    assert not loc.set_latitude_dms(degrees, minutes, seconds, hemisphere)
    assert len(loc.errors) == 1
    assert loc.check_valid() == False


# DMS longitude tests
def test_setting_dms_longitude_valid():
    loc = Location()

    assert loc.set_longitude_dms(132, 43, 19, "W")
    assert loc.longitude == -132.72194444444446


dms_longitude_invalid_tests = [
    pytest.param("Blah", 32, 14, "E", id="invalid string degrees"),
    pytest.param(400, 32, 14, "E", id="invalid numeric degrees"),
    pytest.param(50, "Blah", 14, "E", id="invalid string minutes"),
    pytest.param(50, 400, 14, "E", id="invalid numeric minutes"),
    pytest.param(50, 32, "Blah", "E", id="invalid string seconds"),
    pytest.param(50, 32, 400, "E", id="invalid numeric seconds"),
    pytest.param(50, 32, 80, "R", id="invalid hemisphere - R"),
    pytest.param(50, 32, 80, "N", id="invalid hemisphere - N"),
]


@pytest.mark.parametrize(
    "degrees,minutes,seconds,hemisphere", dms_longitude_invalid_tests
)
def test_setting_dms_longitude_invalid(degrees, minutes, seconds, hemisphere):
    loc = Location()

    assert not loc.set_longitude_dms(degrees, minutes, seconds, hemisphere)
    assert len(loc.errors) == 1

    assert loc.check_valid() == False


def test_as_wkt():
    loc = Location()

    loc.set_latitude_decimal_degrees(50.2)
    loc.set_longitude_decimal_degrees(-1.34)

    assert loc.to_wkt() == "SRID=4326;POINT(-1.34 50.2)"


def test_set_from_wkb():
    loc = Location()
    loc.set_from_wkb("0101000020E61000009A9999999999F5BF3D0AD7A3701D4940")

    assert loc.latitude == 50.23
    assert loc.longitude == -1.35
