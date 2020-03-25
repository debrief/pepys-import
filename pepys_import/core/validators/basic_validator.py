class BasicValidator:
    def __init__(self, object_, errors, parser_name):
        error_type = parser_name + f" - Basic Validation Error"
        longitude = None
        latitude = None

        heading = object_.heading if hasattr(object_, "heading") else None
        course = object_.course if hasattr(object_, "course") else None
        if hasattr(object_, "location"):
            if object_.location is not None:
                longitude = object_.location.longitude
                latitude = object_.location.latitude

        self.validate_longitude(longitude, errors, error_type)
        self.validate_latitude(latitude, errors, error_type)
        self.validate_heading(heading, errors, error_type)
        self.validate_course(course, errors, error_type)

    @staticmethod
    def validate_longitude(longitude, errors, error_type):
        """Validates the given longitude. It's logic is as follows:
        If longitude is none, there is nothing to validate, return True
        If longitude is not none, check whether it is between -180 and 180. If yes, return True

        :param longitude: Longitude of the measurement object
        :type longitude:
        :param errors: Error List to save value error if it raises
        :type errors: List
        :param error_type: Type of error
        :type error_type: String
        :return: True if there is no error, False otherwise
        :rtype: bool
        """
        if longitude is None or -180 <= longitude <= 180:
            return True

        errors.append({error_type: "Longitude is not between -180 and 180 degrees!"})
        return False

    @staticmethod
    def validate_latitude(latitude, errors, error_type):
        """Validates the given latitude. It's logic is as follows:
        If latitude is none, there is nothing to validate, return True
        If latitude is not none, check whether it is between -90 and 90. If yes, return True

        :param latitude: Latitude of the measurement object
        :type latitude:
        :param errors: Error List to save value error if it raises
        :type errors: List
        :param error_type: Type of error
        :type error_type: String
        :return: True if there is no error, False otherwise
        :rtype: bool
        """
        if latitude is None or -90 <= latitude <= 90:
            return True
        errors.append({error_type: "Latitude is not between -90 and 90 degrees!"})
        return False

    @staticmethod
    def validate_heading(heading, errors, error_type):
        """Validates the given heading. It's logic is as follows:
        If heading is none, there is nothing to validate, return True
        If heading exists, check if it's between 0 and 360. If yes, return True

        :param heading: Heading of the object (In degrees)
        :type heading: Quantity
        :param errors: Error List to save value error if it raises
        :type errors: List
        :param error_type: Type of error
        :type error_type: String
        :return: True if there is no error, False otherwise
        :rtype: bool
        """

        if heading is None or 0 <= heading.magnitude <= 360:
            return True
        errors.append({error_type: "Heading is not between 0 and 360 degrees!"})
        return False

    @staticmethod
    def validate_course(course, errors, error_type):
        """Validates the given course. It's logic is as follows:
        If course is none, there is nothing to validate, return True
        If course exists,check if it's between 0 and 360. If yes, return True

        :param course: Course of the object (In degrees)
        :type course: Quantity
        :param errors: Error List to save value error if it raises
        :type errors: List
        :param error_type: Type of error
        :type error_type: String
        :return: True if there is no error, False otherwise
        :rtype: bool
        """
        if course is None or 0 <= course.magnitude <= 360:
            return True
        errors.append({error_type: "Course is not between 0 and 360 degrees!"})
        return False
