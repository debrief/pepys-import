def validate_longitude(longitude):
    if -90 <= longitude <= 90:
        return True
    return False


def validate_latitude(latitude):
    if -180 <= latitude <= 180:
        return True
    return False


def validate_heading(heading):
    if 0 <= heading <= 360:
        return True
    return False


def validate_course(course):
    if 0 <= course <= 360:
        return True
    return False


def basic_validation(longitude, latitude, heading, course):
    return (
        validate_longitude(longitude)
        and validate_latitude(latitude)
        and validate_heading(heading)
        and validate_course(course)
    )


# basic_validation(-100, -20, 50, 50)
