import os
from datetime import datetime

import pytest

from pepys_import.file.highlighter.highlighter import HighlightedFile
from pepys_import.file.highlighter.support.combine import combine_tokens
from tests.benchmarks.benchmark_utils import running_on_ci

DIR_PATH = os.path.dirname(os.path.abspath(__file__))


def parse_timestamp(date, time):
    if len(date) == 6:
        format_str = "%y%m%d"
    else:
        format_str = "%Y%m%d"

    if len(time) == 6:
        format_str += "%H%M%S"
    else:
        format_str += "%H%M%S.%f"

    return datetime.strptime(date + time, format_str)


def parse_location(lat, lat_hem, lon, long_hem):
    lat_degs = float(lat[0:2])
    lat_mins = float(lat[2:4])
    lat_secs = float(lat[4:])
    lat_degs = lat_degs + lat_mins / 60 + lat_secs / 60 / 60

    lon_degs = float(lon[0:3])
    lon_mins = float(lon[3:5])
    lon_secs = float(lon[5:])
    lon_degs = lon_degs + lon_mins / 60 + lon_secs / 60 / 60

    if lat_hem == "S":
        lat_degs = -1 * lat_degs

    if lat_hem == "W":
        lon_degs = -1 * lon_degs

    return lat_degs, lon_degs


def run_highlighter_on_whole_file():
    data_file = HighlightedFile(os.path.join(DIR_PATH, "benchmark_data/NMEA_out.txt"))

    # get the set of self-describing lines
    lines = data_file.lines()

    nmea_delim = "([^,]+|(?<=,)(?=,)|^(?=,)|(?<=,)$)"

    lat_tok = None
    lat_hem_tok = None
    long_tok = None
    long_hem_tok = None
    date_tok = None
    time_tok = None
    hdg_tok = None
    spd_tok = None

    date_line = None
    loc_line = None
    hdg_line = None
    spd_line = None

    for line in lines:
        tokens = line.tokens(nmea_delim, ",")
        if len(tokens) > 0:

            msg_type = tokens[1].text

            if msg_type == "DZA":
                date_tok = tokens[2]
                time_tok = tokens[3]
                date_line = line
            elif msg_type == "VEL":
                spd_tok = tokens[6]
                spd_line = line
            elif msg_type == "HDG":
                hdg_tok = tokens[2]
                hdg_line = line
            elif msg_type == "POS":
                lat_tok = tokens[3]
                lat_hem_tok = tokens[4]
                long_tok = tokens[5]
                long_hem_tok = tokens[6]
                loc_line = line

            # do we have all we need?
            if date_tok and spd_tok and hdg_tok and lat_tok:

                date_time = parse_timestamp(date_tok.text, time_tok.text)

                loc = parse_location(
                    lat_tok.text,
                    lat_hem_tok.text,
                    long_tok.text,
                    long_hem_tok.text,
                )
                spd = float(spd_tok.text)
                hdg = float(hdg_tok.text)

                fStr = "{:8.2f}"

                msg = (
                    "Date:"
                    + str(date_time)
                    + ", Loc:()"
                    + fStr.format(loc[0])
                    + ", "
                    + fStr.format(loc[1])
                    + "), Spd:"
                    + fStr.format(spd)
                    + ", Hdg:"
                    + fStr.format(hdg)
                )

                line_composite = combine_tokens(date_line, loc_line, spd_line, hdg_line)

                line_composite.record("NMEA Import", "Date:" + str(date_time), msg, "N/A")

                date_tok = None
                spd_tok = None
                hdg_tok = None
                lat_tok = None

    data_file.export(os.path.join(DIR_PATH, "nmea_highlighted.html"))


@pytest.mark.benchmark(min_time=0.1, max_time=2.0, min_rounds=3, warmup=False)
def test_highlighter_on_whole_file_benchmark(benchmark):
    benchmark(run_highlighter_on_whole_file)

    TIME_THRESHOLD = 11

    if running_on_ci():
        if benchmark.stats.stats.mean > TIME_THRESHOLD:
            pytest.fail(
                f"Mean benchmark run time of {benchmark.stats.stats.mean}s exceeded maximum time of {TIME_THRESHOLD}s"
            )

    os.remove(os.path.join(DIR_PATH, "nmea_highlighted.html"))


def run_fill_char_array():
    hf = HighlightedFile(os.path.join(DIR_PATH, "benchmark_data/NMEA_out.txt"))

    hf.fill_char_array_if_needed()


@pytest.mark.benchmark(min_time=1, max_time=4.0, min_rounds=5, warmup=False)
def test_highlighter_fill_char_array_benchmark(benchmark):
    benchmark(run_fill_char_array)

    TIME_THRESHOLD = 7

    if running_on_ci():
        if benchmark.stats.stats.mean > TIME_THRESHOLD:
            pytest.fail(
                f"Mean benchmark run time of {benchmark.stats.stats.mean}s exceeded maximum time of {TIME_THRESHOLD}s"
            )
