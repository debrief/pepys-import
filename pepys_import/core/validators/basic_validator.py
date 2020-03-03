class BasicValidator:
    def __init__(self, measurement_object, errors, message):
        self.error_message = message + f" - Basic Validation Error"
        self.errors = errors
        self.longitude = None
        self.latitude = None
        self.heading = measurement_object.heading
        self.course = measurement_object.course

        if measurement_object.location is not None:
            self.longitude, self.latitude = measurement_object.location[6:-1].split()

        self.validate_longitude()
        self.validate_latitude()
        self.validate_heading()
        self.validate_course()

    def validate_longitude(self):
        # if longitude is none, there is nothing to validate, return True
        if self.longitude is None or -90 <= float(self.longitude) <= 90:
            return True

        self.errors.append(
            {self.error_message: "Longitude is not between -90 and 90 degrees!"}
        )
        return False

    def validate_latitude(self):
        # if latitude is none, there is nothing to validate, return True
        if self.latitude is None or -180 <= float(self.latitude) <= 180:
            return True
        self.errors.append(
            {self.error_message: "Latitude is not between -180 and 180 degrees!"}
        )
        return False

    def validate_heading(self):
        # if heading is none, there is nothing to validate, return True
        if self.heading is None or 0 <= self.heading <= 360:
            return True
        self.errors.append(
            {self.error_message: "Heading is not between 0 and 360 degrees!"}
        )
        return False

    def validate_course(self):
        # if course is none, there is nothing to validate, return True
        if self.course is None or 0 <= self.course <= 360:
            return True
        self.errors.append(
            {self.error_message: "Course is not between 0 and 360 degrees!"}
        )
        return False
