from datetime import datetime
from itertools import chain, zip_longest

from prompt_toolkit.validation import Validator


def validate_float(s):
    try:
        _ = float(s)
    except ValueError:
        return False
    return True


def validate_int(s):
    try:
        _ = int(s)
    except ValueError:
        return False
    return True


def validate_datetime(s):
    try:
        datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return False
    return True


float_validator = Validator.from_callable(
    validate_float,
    error_message="This input is not a valid floating point value",
    move_cursor_to_end=True,
)

int_validator = Validator.from_callable(
    validate_int,
    error_message="This input is not a valid integer value",
    move_cursor_to_end=True,
)

datetime_validator = Validator.from_callable(
    validate_datetime,
    error_message="This input is not a valid datetime value",
    move_cursor_to_end=True,
)


def interleave_lists(l1, l2):
    return [x for x in chain(*zip_longest(l1, l2)) if x is not None]
