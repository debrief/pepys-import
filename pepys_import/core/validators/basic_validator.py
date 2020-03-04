from math import degrees

from pepys_import.utils.unit_utils import convert_string_location_to_degrees


class BasicValidator:
    def __init__(self, measurement_object, errors, parser_name):
        self.error_message = parser_name + f" - Basic Validation Error"
        self.errors = errors
        self.longitude = None
        self.latitude = None
        self.heading = measurement_object.heading
        self.course = measurement_object.course

        if measurement_object.location is not None:
            self.longitude, self.latitude = convert_string_location_to_degrees(
                measurement_object.location
            )

        self.validate_longitude()
        self.validate_latitude()
        self.validate_heading()
        self.validate_course()

    def validate_longitude(self):
        # if longitude is none, there is nothing to validate, return True
        if self.longitude is None or -90 <= self.longitude <= 90:
            return True

        self.errors.append(
            {self.error_message: "Longitude is not between -90 and 90 degrees!"}
        )
        return False

    def validate_latitude(self):
        # if latitude is none, there is nothing to validate, return True
        if self.latitude is None or -180 <= self.latitude <= 180:
            return True
        self.errors.append(
            {self.error_message: "Latitude is not between -180 and 180 degrees!"}
        )
        return False

    def validate_heading(self):
        # if heading is none, there is nothing to validate, return True
        # if heading exists, convert it from radians to degrees and check if it's between 0 and 360.
        if self.heading is None or 0 <= degrees(self.heading) <= 360:
            return True
        self.errors.append(
            {self.error_message: "Heading is not between 0 and 360 degrees!"}
        )
        return False

    def validate_course(self):
        # if course is none, there is nothing to validate, return True
        # if course exists, convert it from radians to degrees and check if it's between 0 and 360.
        if self.course is None or 0 <= degrees(self.course) <= 360:
            return True
        self.errors.append(
            {self.error_message: "Course is not between 0 and 360 degrees!"}
        )
        return False
