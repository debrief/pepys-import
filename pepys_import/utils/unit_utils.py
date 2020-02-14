from pepys_import.core.formats import unit_registry


def convert_heading(heading, line_number):
    try:
        valid_heading = float(heading)
    except ValueError:
        print(
            f"Line {line_number}. Error in heading value {heading}. "
            f"Couldn't convert to a number"
        )
        return False
    if 0.0 > valid_heading or valid_heading >= 360.0:
        print(
            f"Line {line_number}. Error in heading value {heading}. "
            f"Should be be between 0 and 359.9 degrees"
        )
        return False
    return valid_heading * unit_registry.degree


def convert_speed(speed, line_number):
    try:
        valid_speed = float(speed)
    except ValueError:
        print(
            f"Line {line_number}. Error in speed value {speed}. "
            f"Couldn't convert to a number"
        )
        return False
    speed = (
        (valid_speed * unit_registry.knot)
        .to(unit_registry.meter / unit_registry.second)
        .magnitude
    )
    return speed
