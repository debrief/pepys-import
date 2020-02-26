from pepys_import.core.formats import unit_registry


def convert_heading(heading, line_number):
    """
    Converts given heading value to degree.

    :param heading: Heading value in string format
    :type heading: String
    :param line_number: Line number
    :type line_number: String
    :return: returns the converted heading value
    """
    try:
        valid_heading = float(heading)
    except ValueError:
        print(
            f"Line {line_number}. Error in heading value {heading}. "
            f"Couldn't convert to a number"
        )
        return False
    if valid_heading < 0:
        valid_heading += 360
    if valid_heading > 360:
        valid_heading -= 360
    return valid_heading * unit_registry.degree


def convert_speed(speed, line_number):
    """
    Converts the given speed value in knots to meter/seconds format.
    :param speed: Speed value in string format
    :type speed: String
    :param line_number: Line number
    :type line_number: String
    :return: return the converted speed value
    """
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
