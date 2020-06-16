from importers.e_trac_importer import ETracImporter
from importers.nmea_importer import NMEAImporter


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
