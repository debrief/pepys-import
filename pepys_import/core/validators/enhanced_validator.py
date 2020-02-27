"""
Enhanced tests actually serve to verify the lat/long, in addition to the course/speed/heading
"""


def course_heading_loose_match_with_location(
    course, heading, prev_location, current_location
):
    """
    :param course:
    :param heading:
    :param prev_location:
    :param current_location:
    :return:
    """


def speed_loose_match_with_location(speed, prev_location, current_location):
    """
    :param speed:
    :param prev_location:
    :param current_location:
    :return:
    """


def enhance_validation(course, heading, speed, prev_location, current_location):
    return course_heading_loose_match_with_location(
        course, heading, prev_location, current_location
    ) and speed_loose_match_with_location(speed, prev_location, current_location)
