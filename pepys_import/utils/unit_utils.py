from math import radians, cos, sin, asin, sqrt, atan2, degrees

from pepys_import.core.formats import unit_registry


def convert_absolute_angle(angle, line_number, errors, error_type):
    """
    Converts given absolute angle value to degree and does sanity checks

    :param angle: Angle value in string format
    :type angle: String
    :param line_number: Line number
    :type line_number: String
    :param errors: Error List to save value error if it raises
    :type errors: List
    :param error_type: Type of error
    :type error_type: String
    :return: returns the converted angle value
    """
    try:
        valid_angle = float(angle)
    except ValueError:
        errors.append(
            {
                error_type: f"Line {line_number}. Error in angle value {angle}. "
                f"Couldn't convert to a number"
            }
        )
        return False
    if valid_angle < 0:
        valid_angle += 360
    if valid_angle > 360:
        valid_angle -= 360
    return valid_angle * unit_registry.degree


def convert_speed(speed, line_number, errors, error_type):
    """
    Converts the given speed value in knots to meter/seconds format.
    :param speed: Speed value in string format
    :type speed: String
    :param line_number: Line number
    :type line_number: String
    :param errors: Error List to save value error if it raises
    :type errors: List
    :param error_type: Type of error
    :type error_type: String
    :return: return the converted speed value
    """
    try:
        valid_speed = float(speed)
    except ValueError:
        errors.append(
            {
                error_type: f"Line {line_number}. Error in speed value {speed}. "
                f"Couldn't convert to a number"
            }
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


def extract_points(location):
    # convert string point to float point
    if isinstance(location, str):
        location = convert_string_location_to_degrees(location)
    longitude, latitude = location
    # convert decimal degrees to radians and return
    return radians(longitude), radians(latitude)


def bearing_between_two_points(first_location, second_location):
    """
    Calculate the bearing(angle) between two points on the earth (specified in decimal degrees).

    :param first_location: First location point
    :param second_location: Second location point
    :return: angle between two points in degrees
    """
    longitude_1, latitude_1 = extract_points(first_location)
    longitude_2, latitude_2 = extract_points(second_location)
    diff_longitude = longitude_2 - longitude_1

    y = sin(diff_longitude) * cos(latitude_2)
    x = cos(latitude_1) * sin(latitude_2) - sin(latitude_1) * cos(latitude_2) * cos(
        diff_longitude
    )
    bearing = degrees((atan2(y, x)))
    bearing = 360 - ((bearing + 360) % 360)
    return bearing


def distance_between_two_points_haversine(first_location, second_location):
    """
    Calculate the great circle distance between two points on the earth (specified in decimal degrees).

    :param first_location: First location point
    :param second_location: Second location point
    :return: distance in kilometers
    """
    longitude_1, latitude_1 = extract_points(first_location)
    longitude_2, latitude_2 = extract_points(second_location)

    # haversine formula
    diff_longitude = longitude_2 - longitude_1
    diff_latitude = latitude_2 - latitude_1
    a = (
        sin(diff_latitude / 2) ** 2
        + cos(latitude_1) * cos(latitude_2) * sin(diff_longitude / 2) ** 2
    )
    c = 2 * asin(sqrt(a))
    radius = 6371  # Radius of earth in kilometers. Use 3956 for miles
    distance = c * radius
    return (
        (distance * unit_registry.kilometers / unit_registry.hour)
        .to(unit_registry.meter / unit_registry.second)
        .magnitude
    )
