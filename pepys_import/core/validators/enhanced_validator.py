"""
Enhanced tests actually serve to verify the lat/long, in addition to the course/speed/heading
"""


class EnhancedValidator:
    def __init__(self, measurement_object, errors, message, prev_location):
        self.error_message = message + f" - Enhanced Validation Error"
        self.errors = errors
        self.heading = measurement_object.heading
        self.course = measurement_object.course
        self.prev_location = measurement_object.prev_location

        self.course_heading_loose_match_with_location()
        self.speed_loose_match_with_location()

    def course_heading_loose_match_with_location(self):
        # TODO: calculate current location, put prev and curr location to ST_Distance,
        #  compare it with course and heading
        """"""

    def speed_loose_match_with_location(self):
        # TODO: calculate current location, put prev and curr location to ST_Distance,
        #  compare it with speed
        """"""
