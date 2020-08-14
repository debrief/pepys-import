from pepys_import.core.formats import unit_registry
from pepys_import.utils.unit_utils import (
    acceptable_bearing_error,
    bearing_between_two_points,
    distance_between_two_points_haversine,
)


class EnhancedValidator:
    """Enhanced validator serve to verify the lat/long, in addition to the course/speed/heading"""

    def __init__(self):
        self.name = "Enhanced Validator"

    def validate(self, current_object, errors, parser_name, prev_object=None):
        orig_errors_length = len(errors)

        error_type = (
            f"{parser_name} - {self.name} Error on Timestamp:"
            f"{str(current_object.time)}, Sensor:"
            f"{current_object.sensor_name}, Platform:{current_object.platform_name}"
        )
        try:
            heading = current_object.heading
        except AttributeError:
            heading = None

        try:
            course = current_object.course
        except AttributeError:
            course = None

        try:
            speed = current_object.speed
        except AttributeError:
            speed = None

        try:
            location = current_object.location
        except AttributeError:
            location = None

        if (
            speed == 0.0 * (unit_registry.metre / unit_registry.second)
            and course == 0.0 * unit_registry.radian
        ):
            print("Both course and speed are exactly zero. Skipping the enhanced validator...")
            return True

        # Doesn't need a try-catch as time is a compulsory field, created
        # when a state is initialised
        time = current_object.time

        if prev_object:
            try:
                prev_location = prev_object.location
            except AttributeError:
                prev_location = None

            # Doesn't need a try-catch as time is a compulsory field, created
            # when a state is initialised
            prev_time = prev_object.time

            if location and prev_location:
                self.course_heading_loose_match_with_location(
                    location, prev_location, heading, course, errors, error_type
                )
                calculated_time = self.calculate_time(time, prev_time)
                if calculated_time != 0:
                    self.speed_loose_match_with_location(
                        location, prev_location, speed, calculated_time, errors, error_type,
                    )

        if len(errors) > orig_errors_length:
            return False
        else:
            return True

    @staticmethod
    def course_heading_loose_match_with_location(
        curr_location, prev_location, heading, course, errors, error_type
    ):
        """Loosely matches the course and heading values with the bearing between two location
        points.

        :param curr_location: Point of the current location of the object
        :type curr_location: Location
        :param prev_location: Point o the previous location of the object
        :type prev_location: Location
        :param heading: Heading of the object (In degrees)
        :type heading: Quantity
        :param course: Course of the object (In degrees)
        :type course: Quantity
        :param errors: Error List to save value error if it raises
        :type errors: List
        :param error_type: Type of error
        :type error_type: String
        :return: True if there is no error, False otherwise
        :rtype: bool
        """
        number_of_errors = len(errors)
        bearing = bearing_between_two_points(prev_location, curr_location)
        delta = 90
        if heading:
            heading_in_degrees = heading.to(unit_registry.degree)
            if not acceptable_bearing_error(heading_in_degrees, bearing, delta):
                errors.append(
                    {
                        error_type: f"Difference between Bearing ({bearing:.3f}) and "
                        f"Heading ({heading_in_degrees:.3f}) is more than {delta} degrees!"
                    }
                )
        if course:
            course_in_degrees = course.to(unit_registry.degree)
            if not acceptable_bearing_error(course_in_degrees, bearing, delta):
                errors.append(
                    {
                        error_type: f"Difference between Bearing ({bearing:.3f}) and "
                        f"Course ({course_in_degrees:.3f}) is more than {delta} degrees!"
                    }
                )
        # if not an error appended to the list, its length will be the same
        if number_of_errors == len(errors):
            return True
        return False

    @staticmethod
    def calculate_time(curr_time, prev_time):
        """Finds the difference between two Datetime objects, converts it to Quantity seconds

        :param curr_time: Timestamp of the current measurement object
        :type curr_time: Datetime
        :param prev_time: Timestamp of the previous measurement object
        :type prev_time: Datetime
        :return: Time difference (In seconds)
        :rtype: Quantity
        """
        diff = curr_time - prev_time
        return diff.seconds * unit_registry.seconds

    @staticmethod
    def speed_loose_match_with_location(
        curr_location, prev_location, speed, time, errors, error_type
    ):
        """Loosely matches the recorded speed with the calculated speed.

        :param curr_location: Point of the current location of the object
        :type curr_location: Location
        :param prev_location: Point of the previous location of the object
        :type prev_location: Location
        :param speed: Speed the object
        :type speed: Quantity
        :param time: Timestamp of the object
        :type time: Datetime
        :param errors: Error List to save value error if it raises
        :type errors: List
        :param error_type: Type of error
        :type error_type: String
        :return: True if there is no error, False otherwise
        :rtype: bool
        """
        distance = distance_between_two_points_haversine(prev_location, curr_location)
        calculated_speed = distance / time
        if speed is None or calculated_speed <= speed * 10:
            return True
        errors.append(
            {
                error_type: f"Calculated speed ({calculated_speed:.3f}) is more than "
                f"the measured speed * 10 ({speed * 10:.3f})!"
            }
        )
        return False
