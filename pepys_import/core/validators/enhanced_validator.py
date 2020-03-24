from math import degrees

from pepys_import.utils.unit_utils import (
    bearing_between_two_points,
    distance_between_two_points_haversine,
)

from pepys_import.core.formats import unit_registry


class EnhancedValidator:
    """Enhanced validator serve to verify the lat/long, in addition to the course/speed/heading"""

    def __init__(self, current_object, errors, parser_name, prev_object=None):
        self.error_type = (
            parser_name + f"-Enhanced Validation Error on Timestamp:"
            f"{str(current_object.time)}, Sensor:"
            f"{current_object.sensor_name}, Platform:{current_object.platform_name}"
        )
        self.errors = errors

        self.heading = (
            current_object.heading if hasattr(current_object, "heading") else None
        )
        self.course = (
            current_object.course if hasattr(current_object, "course") else None
        )
        self.speed = current_object.speed if hasattr(current_object, "speed") else None
        self.location = (
            current_object.location if hasattr(current_object, "location") else None
        )
        self.time = current_object.time if hasattr(current_object, "time") else None

        if prev_object:
            self.prev_location = (
                prev_object.location if hasattr(prev_object, "location") else None
            )
            self.prev_time = prev_object.time if hasattr(prev_object, "time") else None

            self.course_heading_loose_match_with_location()
            self.calculated_time = self.calculate_time()
            if self.calculated_time != 0:
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
            course_in_degrees = self.course.to(unit_registry.degree)
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

    def calculate_time(self):
        diff = self.time - self.prev_time
        return diff.seconds

    def speed_loose_match_with_location(self):
        distance = distance_between_two_points_haversine(
            self.prev_location, self.location
        )
        calculated_speed = distance.magnitude / self.calculated_time
        if self.speed is None or calculated_speed <= self.speed.magnitude * 10:
            return True
        self.errors.append(
            {
                self.error_type: f"Calculated speed ({calculated_speed:.3f} meter / second) is more than "
                f"the measured speed * 10 ({self.speed * 10:.3f})!"
            }
        )
        return False
