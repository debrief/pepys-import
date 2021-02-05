from datetime import datetime

import pytest

from importers.word_narrative_importer import WordNarrativeImporter


@pytest.mark.parametrize(
    "input, last_day, last_month, last_year, timestamp",
    [
        pytest.param(
            "141030",
            14,
            7,
            2019,
            datetime(2019, 7, 14, 10, 30),
            id="valid timestamp with days matching",
        ),
        pytest.param(
            "151030",
            14,
            7,
            2019,
            datetime(2019, 7, 15, 10, 30),
            id="valid timestamp with day one more",
        ),
        pytest.param(
            "011030", 30, 7, 2019, datetime(2019, 8, 1, 10, 30), id="end of month rollover"
        ),
        pytest.param(
            "011030", 28, 12, 2019, datetime(2020, 1, 1, 10, 30), id="end of year rollover"
        ),
        pytest.param("1030", 28, 12, 2019, datetime(2019, 12, 28, 10, 30), id="four digit"),
    ],
)
def test_singlepart_datetime_parsing_valid(input, last_day, last_month, last_year, timestamp):
    imp = WordNarrativeImporter()
    imp.errors = []

    imp.last_day = last_day
    imp.last_month = last_month
    imp.last_year = last_year

    output_timestamp = imp.parse_singlepart_datetime(input)

    assert output_timestamp == timestamp


@pytest.mark.parametrize(
    "input, last_day, last_month, last_year",
    [
        pytest.param("141030", None, 7, 2019, id="missing last_day"),
        pytest.param("151030", 14, None, 2019, id="missing last_month"),
        pytest.param("011030", 30, 7, None, id="missing last_year"),
        pytest.param("991030", 28, 12, 2019, id="invalid day"),
        pytest.param("019930", 28, 12, 2019, id="invalid hour"),
        pytest.param("011099", 28, 12, 2019, id="invalid min"),
        pytest.param("9930", 28, 12, 2019, id="four digit invalid hour"),
        pytest.param("1099", 28, 12, 2019, id="four digit invalid min"),
        pytest.param("", 28, 12, 2019, id="empty"),
        pytest.param("123456789", 28, 12, 2019, id="too long"),
    ],
)
def test_singlepart_datetime_parsing_invalid(input, last_day, last_month, last_year):
    imp = WordNarrativeImporter()
    imp.errors = []

    imp.last_day = last_day
    imp.last_month = last_month
    imp.last_year = last_year

    with pytest.raises(ValueError):
        _ = imp.parse_singlepart_datetime(input)


@pytest.mark.parametrize(
    "input,timestamp",
    [
        pytest.param(
            ["041014", "04", "07", "2020"], datetime(2020, 7, 4, 10, 14), id="valid timestamp"
        ),
        pytest.param(["041014", "4", "7", "2020"], datetime(2020, 7, 4, 10, 14), id="single chars"),
        pytest.param(
            ["041014", "4", "7", "20"], datetime(2020, 7, 4, 10, 14), id="two digit year 20"
        ),
        pytest.param(
            ["041014", "4", "7", "85"], datetime(1985, 7, 4, 10, 14), id="two digit year 85"
        ),
        pytest.param(
            ["042314", "05", "07", "2020"],
            datetime(2020, 7, 4, 23, 14),
            id="near midnight mismatch",
        ),
    ],
)
def test_multipart_datetime_parsing_valid_sixfig(input, timestamp):
    imp = WordNarrativeImporter()
    imp.errors = []

    output_timestamp, error = imp.parse_multipart_datetime(input, four_fig=False)

    assert not error
    assert output_timestamp == timestamp


@pytest.mark.parametrize(
    "input,timestamp",
    [
        pytest.param(
            ["1014", "04", "07", "2020"], datetime(2020, 7, 4, 10, 14), id="valid timestamp"
        ),
        pytest.param(["1014", "4", "7", "2020"], datetime(2020, 7, 4, 10, 14), id="single chars"),
        pytest.param(
            ["1014", "4", "7", "20"], datetime(2020, 7, 4, 10, 14), id="two digit year 20"
        ),
        pytest.param(
            ["1014", "4", "7", "85"], datetime(1985, 7, 4, 10, 14), id="two digit year 85"
        ),
    ],
)
def test_multipart_datetime_parsing_valid_fourfig(input, timestamp):
    imp = WordNarrativeImporter()
    imp.errors = []

    output_timestamp, error = imp.parse_multipart_datetime(input, four_fig=True)

    assert not error
    assert output_timestamp == timestamp


@pytest.mark.parametrize(
    "input,timestamp",
    [
        pytest.param(
            ["041014", "08", "07", "2020"], datetime(2020, 7, 4, 10, 14), id="mismatch day"
        ),
        pytest.param(["991014", "99", "7", "2020"], datetime(2020, 7, 4, 10, 14), id="invalid day"),
        pytest.param(["041014", "4", "99", "20"], datetime(2020, 7, 4, 10, 14), id="invalid month"),
        pytest.param(
            ["041014", "4", "7", "-1234"], datetime(1985, 7, 4, 10, 14), id="invalid year"
        ),
        pytest.param(
            ["049914", "04", "07", "2020"], datetime(2020, 7, 4, 23, 14), id="invalid hour"
        ),
        pytest.param(
            ["041099", "04", "07", "2020"], datetime(2020, 7, 4, 23, 14), id="invalid minute"
        ),
    ],
)
def test_multipart_datetime_parsing_invalid_sixfig(input, timestamp):
    imp = WordNarrativeImporter()
    imp.errors = []

    output_timestamp, error = imp.parse_multipart_datetime(input, four_fig=False)

    assert error


@pytest.mark.parametrize(
    "input,timestamp",
    [
        pytest.param(["1014", "99", "7", "2020"], datetime(2020, 7, 4, 10, 14), id="invalid day"),
        pytest.param(["1014", "4", "99", "20"], datetime(2020, 7, 4, 10, 14), id="invalid month"),
        pytest.param(["1014", "4", "7", "-1234"], datetime(1985, 7, 4, 10, 14), id="invalid year"),
        pytest.param(["9914", "04", "07", "2020"], datetime(2020, 7, 4, 23, 14), id="invalid hour"),
        pytest.param(
            ["1099", "04", "07", "2020"], datetime(2020, 7, 4, 23, 14), id="invalid minute"
        ),
    ],
)
def test_multipart_datetime_parsing_invalid_fourfig(input, timestamp):
    imp = WordNarrativeImporter()
    imp.errors = []

    output_timestamp, error = imp.parse_multipart_datetime(input, four_fig=True)

    assert error
