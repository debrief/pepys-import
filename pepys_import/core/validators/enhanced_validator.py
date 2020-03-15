from math import degrees

from pepys_import.utils.unit_utils import (
    bearing_between_two_points,
    distance_between_two_points_haversine,
)

from pepys_import.core.formats import unit_registry


class EnhancedValidator:
    """Enhanced validator serve to verify the lat/long, in addition to the course/speed/heading"""

    def __init__(self, measurement_object, errors, parser_name):
        self.error_type = (
            parser_name + f"-Enhanced Validation Error on Timestamp:"
            f"{str(measurement_object.time)}, Sensor:"
            f"{measurement_object.sensor_name}, Platform:{measurement_object.platform_name}"
        )
        self.errors = errors

        if hasattr(measurement_object, "heading"):
            self.heading = measurement_object.heading
        else:
            self.heading = None
        if hasattr(measurement_object, "course"):
            self.course = measurement_object.course
        else:
            self.course = None
        if hasattr(measurement_object, "speed"):
            self.speed = measurement_object.speed
        else:
            self.speed = None

        if hasattr(measurement_object, "location"):
            self.location = measurement_object.location
        else:
            self.location = None

        if hasattr(measurement_object, "prev_location"):
            self.prev_location = measurement_object.prev_location
        else:
            self.prev_location = None

        if self.location and self.prev_location:
            self.course_heading_loose_match_with_location()
            self.speed_loose_match_with_location()

    @staticmethod
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

        bearing1 = bearing1.magnitude
        bearing2 = bearing2.magnitude

        # note: compact test algorithm came from here:
        #    https://gamedev.stackexchange.com/a/4472/8270
        diff = 180 - abs(abs(bearing1 - bearing2) - 180)
        return diff <= delta

    def course_heading_loose_match_with_location(self):
        number_of_errors = len(self.errors)
        bearing = bearing_between_two_points(self.prev_location, self.location)
        delta = 90
        if self.heading:
            heading_in_degrees = self.heading.to(unit_registry.degree)
            if not self.acceptable_bearing_error(heading_in_degrees, bearing, delta):
                self.errors.append(
                    {
                        self.error_type: f"Difference between Bearing ({bearing:.3f}) and "
                        f"Heading ({heading_in_degrees:.3f}) is more than {delta} degrees!"
                    }
                )
        if self.course:
            course_in_degrees = degrees(self.course)
            if not self.acceptable_bearing_error(course_in_degrees, bearing, delta):
                self.errors.append(
                    {
                        self.error_type: f"Difference between Bearing ({bearing:.3f}) and "
                        f"Course ({course_in_degrees:.3f}) is more than {delta} degrees!"
                    }
                )
        # if not an error appended to the list, its length will be the same
        if number_of_errors == len(self.errors):
            return True
        return False

    def speed_loose_match_with_location(self):
        calculated_speed = distance_between_two_points_haversine(
            self.prev_location, self.location
        )
        if self.speed is None or calculated_speed <= self.speed * 10:
            return True
        self.errors.append(
            {
                self.error_type: f"Calculated speed ({calculated_speed:.3f}) is more than "
                f"the measured speed * 10 ({self.speed * 10:.3f})!"
            }
        )
        return False
