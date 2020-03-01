from pepys_import.core.formats import unit_registry


def convert_absolute_angle(angle, line_number):
    """
    Converts given absolute angle value to degree and does sanity checks

    :param angle: Angle value in string format
    :type angle: String
    :param line_number: Line number
    :type line_number: String
    :return: returns the converted angle value
    """
    try:
        valid_angle = float(angle)
    except ValueError:
        print(
            f"Line {line_number}. Error in angle value {angle}. "
            f"Couldn't convert to a number"
        )
        return False
    if valid_angle < 0:
        valid_angle += 360
    if valid_angle > 360:
        valid_angle -= 360
    return valid_angle * unit_registry.degree


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
