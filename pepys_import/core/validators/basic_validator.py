MESSAGE = f"Basic Validation Error"


def validate_longitude(longitude, errors):
    if longitude and -90 <= longitude <= 90:
        return True
    errors.append({MESSAGE: "Longitude is not between -90 and 90 degrees!"})
    return False


def validate_latitude(latitude, errors):
    if latitude and -180 <= latitude <= 180:
        return True
    errors.append({MESSAGE: "Latitude is not between -180 and 180 degrees!"})
    return False


def validate_heading(heading, errors):
    if heading and 0 <= heading <= 360:
        return True
    errors.append({MESSAGE: "Heading is not between 0 and 360 degrees!"})
    return False


def validate_course(course, errors):
    if course and 0 <= course <= 360:
        return True
    errors.append({MESSAGE: "Course is not between 0 and 360 degrees!"})
    return False


def basic_validation(measurement_object, errors):
    if measurement_object.location is not None:
        longitude, latitude = measurement_object.location[6:-1].split()
        return (
            validate_longitude(float(longitude), errors)
            and validate_latitude(float(latitude), errors)
            and validate_heading(measurement_object.heading, errors)
            and validate_course(measurement_object.course, errors)
        )
    return validate_heading(measurement_object.heading, errors) and validate_course(
        measurement_object.course, errors
    )


# basic_validation(-100, -20, 50, 50)
