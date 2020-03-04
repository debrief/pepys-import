from math import radians, cos, sin, asin, sqrt

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


def convert_string_location_to_degrees(first_location):
    longitude, latitude = first_location[6:-1].split()
    return float(longitude), float(latitude)


def distance_between_two_points_haversine(first_location, second_location):
    """
    Calculate the great circle distance between two points on the earth (specified in decimal degrees).

    :param first_location: First location point
    :param second_location: Second location point
    :return: distance in kilometers
    """
    # convert string point to float point
    if isinstance(first_location, str):
        first_location = convert_string_location_to_degrees(first_location)
    if isinstance(second_location, str):
        second_location = convert_string_location_to_degrees(second_location)
    longitude_1, latitude_1 = first_location
    longitude_2, latitude_2 = second_location
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(
        radians, [longitude_1, latitude_1, longitude_2, latitude_2]
    )

    # haversine formula
    diff_longitude = lon2 - lon1
    diff_latitude = lat2 - lat1
    a = (
        sin(diff_latitude / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(diff_longitude / 2) ** 2
    )
    c = 2 * asin(sqrt(a))
    radius = 6371  # Radius of earth in kilometers. Use 3956 for miles
    return c * radius
