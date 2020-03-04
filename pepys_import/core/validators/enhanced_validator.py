from pepys_import.utils.unit_utils import (
    bearing_between_two_points,
    distance_between_two_points_haversine,
)


class EnhancedValidator:
    """Enhanced validator serve to verify the lat/long, in addition to the course/speed/heading"""

    def __init__(self, measurement_object, errors, message, prev_location):
        self.error_message = message + f" - Enhanced Validation Error"
        self.errors = errors
        self.location = measurement_object.location
        self.speed = measurement_object.speed
        self.heading = measurement_object.heading
        self.course = measurement_object.course
        self.prev_location = prev_location

        self.course_heading_loose_match_with_location()
        self.speed_loose_match_with_location()

    def course_heading_loose_match_with_location(self):
        bearing = bearing_between_two_points(self.location, self.prev_location)
        print(bearing)
        if bearing <= 90:
            return True
        self.errors.append(
            {self.error_message: f"Bearing ({bearing}) is more than 90 degrees!"}
        )

    def speed_loose_match_with_location(self):
        distance = distance_between_two_points_haversine(
            self.location, self.prev_location
        )
        print(distance, self.speed * 10)
        if distance <= self.speed * 10:
            return True
        self.errors.append(
            {
                self.error_message: f"Distance ({distance} km) is more than speed * 10 ("
                f"{self.speed * 10})!"
            }
        )
        return False
