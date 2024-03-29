from datetime import datetime

from importers.e_trac_importer import ETracImporter
from importers.nmea_importer import NMEAImporter
from pepys_import.core.formats import rep_line


def test_nmea_timestamp_parsing():
    parse_timestamp = NMEAImporter.parse_timestamp

    # Invalid day in date
    result = parse_timestamp("20201045", "111456")
    assert not result

    # Invalid hour in time
    result = parse_timestamp("20201006", "340738")
    assert not result


def test_etrac_timestamp_parsing():
    parse_timestamp = ETracImporter.parse_timestamp

    # Invalid day in date
    result = parse_timestamp("2020/04/57", "11:46:23")
    assert not result

    # Invalid hour in time
    result = parse_timestamp("2020/04/07", "34:07:38")
    assert not result


def test_rep_timestamp_parsing():
    parse_timestamp = rep_line.parse_timestamp
    date = "20201001"

    time = "12010"  # missing minute in time
    result = parse_timestamp(date, time)
    assert not result

    time = "340100"  # invalid hour in time
    result = parse_timestamp(date, time)
    assert not result

    time = "120105"
    result = parse_timestamp(date, time)
    assert result == datetime(2020, 10, 1, 12, 1, 5)

    time = "120105.1"
    result = parse_timestamp(date, time)
    assert result == datetime(2020, 10, 1, 12, 1, 5, 100000)

    time = "120105.11"
    result = parse_timestamp(date, time)
    assert result == datetime(2020, 10, 1, 12, 1, 5, 110000)

    time = "120105.111"
    result = parse_timestamp(date, time)
    assert result == datetime(2020, 10, 1, 12, 1, 5, 111000)

    time = "120105.1111"
    result = parse_timestamp(date, time)
    assert result == datetime(2020, 10, 1, 12, 1, 5, 111100)

    time = "120105.11111"
    result = parse_timestamp(date, time)
    assert result == datetime(2020, 10, 1, 12, 1, 5, 111110)

    time = "120105.111111"
    result = parse_timestamp(date, time)
    assert result == datetime(2020, 10, 1, 12, 1, 5, 111111)

    time = "120101.1234567"  # invalid decimals in time
    result = parse_timestamp(date, time)
    assert not result
