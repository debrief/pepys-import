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

        self.basic_validation()

    def validate_longitude(self):
        if self.longitude and -90 <= float(self.longitude) <= 90:
            return True
        self.errors.append(
            {self.error_message: "Longitude is not between -90 and 90 degrees!"}
        )
        return False

    def validate_latitude(self):
        if self.latitude and -180 <= float(self.latitude) <= 180:
            return True
        self.errors.append(
            {self.error_message: "Latitude is not between -180 and 180 degrees!"}
        )
        return False

    def validate_heading(self):
        if self.heading and 0 <= self.heading <= 360:
            return True
        self.errors.append(
            {self.error_message: "Heading is not between 0 and 360 degrees!"}
        )
        return False

    def validate_course(self):
        if self.course and 0 <= self.course <= 360:
            return True
        self.errors.append(
            {self.error_message: "Course is not between 0 and 360 degrees!"}
        )
        return False

    def basic_validation(self):
        return (
            self.validate_longitude()
            and self.validate_latitude()
            and self.validate_heading()
            and self.validate_course()
        )
