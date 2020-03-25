from math import asin, atan2, cos, degrees, radians, sin, sqrt

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


def convert_speed(speed, units, line_number, errors, error_type):
    """
    Parses the given speed value into a float and assigns the given units

    :param speed: Speed value in string format
    :type speed: String
    :param units: Units of the speed (as a pint unit instance)
    :type units: pint unit
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
    speed = valid_speed * units
    return speed


def extract_points(location):
    """Convert decimal degrees to radians and return

    :param location: A point of location
    :type location: Location
    """
    return radians(location.longitude), radians(location.latitude)


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
    x = cos(latitude_1) * sin(latitude_2) - sin(latitude_1) * cos(latitude_2) * cos(diff_longitude)
    bearing = degrees((atan2(y, x)))
    bearing = (bearing + 360) % 360
    return bearing


def distance_between_two_points_haversine(first_location, second_location):
    """
    Calculate the great circle distance between two points on the earth (specified in
    decimal degrees).

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
    return (distance * unit_registry.kilometer).to(unit_registry.meter)


def convert_frequency(frequency, units, line_number, errors, error_type):
    """
    Converts the given frequency string to a Quantity containing a float
    value and the given units

    :param frequency: frequency value in string format
    :type frequency: String
    :param units: units of frequency for supplied measurement
    :type units: String
    :param line_number: Line number
    :type line_number: String
    :param errors: Error List to save value error if it raises
    :type errors: List
    :param error_type: Type of error
    :type error_type: String
    :return: return the converted speed value
    """
    try:
        valid_frequency = float(frequency)
    except ValueError:
        errors.append(
            {
                error_type: f"Line {line_number}. Error in frequency value {frequency}. "
                f"Couldn't convert to a number"
            }
        )
        return False
    frequency = valid_frequency * units
    return frequency


def convert_distance(distance, units, line_number, errors, error_type):
    """
    Converts the given distance string to a Quantity consisting of a
    float value and the given units.

    :param distance: distance value in string format
    :type distance: String
    :param units: units of distance for supplied measurement
    :type units: String
    :param line_number: Line number
    :type line_number: String
    :param errors: Error List to save value error if it raises
    :type errors: List
    :param error_type: Type of error
    :type error_type: String
    :return: return the converted speed value
    """
    try:
        valid_distance = float(distance)
    except ValueError:
        errors.append(
            {
                error_type: f"Line {line_number}. Error in distance value {distance}. "
                f"Couldn't convert to a number"
            }
        )
        return False
    distance = valid_distance * units
    return distance


def acceptable_bearing_error(bearing1, bearing2, delta):
    """Determines if the two bearings are more than a set angle apart, allowing
    for angles that span zero (North)

    :param bearing1: The first bearing
    :type bearing1: number (degrees)
    :param bearing2: The second bearing
    :type bearing2: number (degrees)
    :param delta: The acceptable separation
    :type delta: number (degrees)
    """

    try:
        # Try treating it as a Quantity
        bearing1_mag = bearing1.magnitude
    except AttributeError:
        # Otherwise just a normal float
        bearing1_mag = float(bearing1)

    try:
        bearing2_mag = bearing2.magnitude
    except AttributeError:
        bearing2_mag = float(bearing2)

    # note: compact test algorithm came from here:
    #    https://gamedev.stackexchange.com/a/4472/8270
    diff = 180 - abs(abs(bearing1_mag - bearing2_mag) - 180)
    return diff <= delta
