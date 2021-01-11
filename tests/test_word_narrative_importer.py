from datetime import datetime

import pytest

from importers.word_narrative_importer import WordNarrativeImporter


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
def test_datetime_parsing_valid_sixfig(input, timestamp):
    imp = WordNarrativeImporter()
    imp.errors = []

    output_timestamp, error = imp.parse_datetime(input, four_fig=False)

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
def test_datetime_parsing_valid_fourfig(input, timestamp):
    imp = WordNarrativeImporter()
    imp.errors = []

    output_timestamp, error = imp.parse_datetime(input, four_fig=True)

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
def test_datetime_parsing_invalid_sixfig(input, timestamp):
    imp = WordNarrativeImporter()
    imp.errors = []

    output_timestamp, error = imp.parse_datetime(input, four_fig=False)

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
def test_datetime_parsing_invalid_fourfig(input, timestamp):
    imp = WordNarrativeImporter()
    imp.errors = []

    output_timestamp, error = imp.parse_datetime(input, four_fig=True)

    assert error
