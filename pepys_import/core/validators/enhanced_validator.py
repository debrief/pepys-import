"""
Enhanced tests actually serve to verify the lat/long, in addition to the course/speed/heading
"""

MESSAGE = f"Enhanced Validation Error"


def course_heading_loose_match_with_location(
    course, heading, prev_location, current_location, errors
):
    """
    :param course:
    :param heading:
    :param prev_location:
    :param current_location:
    :param errors:
    :return:
    """


def speed_loose_match_with_location(speed, prev_location, current_location, errors):
    """
    :param speed:
    :param prev_location:
    :param current_location:
    :param errors:
    :return:
    """


def enhanced_validation(measurement_object, prev_location, errors):
    return course_heading_loose_match_with_location(
        measurement_object.course,
        measurement_object.heading,
        prev_location,
        measurement_object.location,
        errors,
    ) and speed_loose_match_with_location(
        measurement_object.speed, prev_location, measurement_object.location, errors
    )
