from math import degrees

from pepys_import.utils.unit_utils import (
    bearing_between_two_points,
    distance_between_two_points_haversine,
)


class EnhancedValidator:
    """Enhanced validator serve to verify the lat/long, in addition to the course/speed/heading"""

    def __init__(self, measurement_object, errors, parser_name):
        self.error_type = parser_name + f" - Enhanced Validation Error"
        self.errors = errors
        self.location = measurement_object.location
        self.speed = measurement_object.speed
        self.heading = measurement_object.heading
        self.course = measurement_object.course
        self.prev_location = measurement_object.prev_location

        if self.location and self.prev_location:
            self.course_heading_loose_match_with_location()
            self.speed_loose_match_with_location()

    def course_heading_loose_match_with_location(self):
        number_of_errors = len(self.errors)
        bearing = bearing_between_two_points(self.location, self.prev_location)
        if self.heading:
            heading_in_degrees = degrees(self.heading)
            if not -90 <= heading_in_degrees - bearing <= 90:
                self.errors.append(
                    {
                        self.error_type: f"Difference between Bearing ({bearing:.3f}) and "
                        f"Heading ({heading_in_degrees:.3f}) is more than 90 degrees!"
                    }
                )
        if self.course:
            course_in_degrees = degrees(self.course)
            if not -90 <= course_in_degrees - bearing <= 90:
                self.errors.append(
                    {
                        self.error_type: f"Difference between Bearing ({bearing:.3f}) and "
                        f"Course ({course_in_degrees:.3f}) is more than 90 degrees!"
                    }
                )
        # if not an error appended to the list, its length will be the same
        if number_of_errors == len(self.errors):
            return True
        return False

    def speed_loose_match_with_location(self):
        calculated_speed = distance_between_two_points_haversine(
            self.location, self.prev_location
        )
        if calculated_speed <= self.speed * 10:
            return True
        self.errors.append(
            {
                self.error_type: f"Calculate speed ({calculated_speed:.3f} m/s) is more than "
                f"the measured speed * 10 ({self.speed * 10:.3f} m/s)!"
            }
        )
        return False
