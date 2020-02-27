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


def validate_speed(speed):
    if 0 <= speed <= 360:
        return True
    return False


def basic_validation(longitude, latitude, heading, course, speed):
    return (
        validate_longitude(longitude)
        and validate_latitude(latitude)
        and validate_heading(heading)
        and validate_course(course)
        and validate_speed(speed)
    )
