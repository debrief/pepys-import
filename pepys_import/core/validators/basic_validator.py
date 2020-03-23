from pepys_import.core.formats import unit_registry


class BasicValidator:
    def __init__(self, measurement_object, errors, parser_name):
        self.error_type = parser_name + f" - Basic Validation Error"
        self.errors = errors
        self.longitude = None
        self.latitude = None
        if hasattr(measurement_object, "heading"):
            self.heading = measurement_object.heading
        else:
            self.heading = None
        if hasattr(measurement_object, "course"):
            self.course = measurement_object.course
        else:
            self.course = None

        if hasattr(measurement_object, "location"):
            if measurement_object.location is not None:
                self.longitude = measurement_object.location.longitude
                self.latitude = measurement_object.location.latitude

        self.validate_longitude()
        self.validate_latitude()
        self.validate_heading()
        self.validate_course()

    def validate_longitude(self):
        # if longitude is none, there is nothing to validate, return True
        if self.longitude is None or -180 <= self.longitude <= 180:
            return True

        self.errors.append(
            {self.error_type: "Longitude is not between -180 and 180 degrees!"}
        )
        return False

    def validate_latitude(self):
        # if latitude is none, there is nothing to validate, return True
        if self.latitude is None or -90 <= self.latitude <= 90:
            return True
        self.errors.append(
            {self.error_type: "Latitude is not between -90 and 90 degrees!"}
        )
        return False

    def validate_heading(self):
        # if heading is none, there is nothing to validate, return True
        # if heading exists, convert it from radians to degrees and check if it's between 0 and 360.
        if (
            self.heading is None
            or 0 <= self.heading.to(unit_registry.degree).magnitude <= 360
        ):
            return True
        self.errors.append(
            {self.error_type: "Heading is not between 0 and 360 degrees!"}
        )
        return False

    def validate_course(self):
        # if course is none, there is nothing to validate, return True
        # if course exists, convert it from radians to degrees and check if it's between 0 and 360.
        if (
            self.course is None
            or 0 <= self.course.to(unit_registry.degree).magnitude <= 360
        ):
            return True
        self.errors.append(
            {self.error_type: "Course is not between 0 and 360 degrees!"}
        )
        return False
