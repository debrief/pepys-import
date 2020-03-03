def validate_longitude(longitude):
    if longitude and -90 <= longitude <= 90:
        return True
    return False


def validate_latitude(latitude):
    if latitude and -180 <= latitude <= 180:
        return True
    return False


def validate_heading(heading):
    if heading and 0 <= heading <= 360:
        return True
    return False


def validate_course(course):
    if course and 0 <= course <= 360:
        return True
    return False


def basic_validation(measurement_object):
    if measurement_object.location is not None:
        longitude, latitude = measurement_object.location[6:-1].split()
        return (
            validate_longitude(float(longitude))
            and validate_latitude(float(latitude))
            and validate_heading(measurement_object.heading)
            and validate_course(measurement_object.course)
        )
    return validate_heading(measurement_object.heading) and validate_course(
        measurement_object.course
    )


# basic_validation(-100, -20, 50, 50)
