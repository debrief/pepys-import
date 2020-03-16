import unittest
import pytest

from pepys_import.core.formats.location import Location


def test_initial_value_none():
    loc = Location()

    assert loc.latitude is None
    assert loc.longitude is None


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


def test_setting_latitude_valid_float():
    loc = Location()

    assert loc.set_latitude_decimal_degrees(50.23)
    assert loc.latitude == 50.23


def test_setting_latitude_invalid_float():
    loc = Location()

    # Assert false
    assert not loc.set_latitude_decimal_degrees(5673.563)
    assert len(loc.errors) == 1


def test_setting_latitude_valid_string():
    loc = Location()

    assert loc.set_latitude_decimal_degrees("23.67")
    assert loc.latitude == 23.67


def test_setting_latitude_invalid_string():
    loc = Location()

    assert not loc.set_latitude_decimal_degrees("Blah")
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
    pytest.param(50, 32, 80, "R", id="invalid hemisphere"),
]


@pytest.mark.parametrize(
    "degrees,minutes,seconds,hemisphere", dms_latitude_invalid_tests
)
def test_setting_dms_latitude_invalid(degrees, minutes, seconds, hemisphere):
    loc = Location()

    assert not loc.set_latitude_dms(degrees, minutes, seconds, hemisphere)
    assert len(loc.errors) == 1
