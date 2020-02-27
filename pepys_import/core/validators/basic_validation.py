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


def validate_speed(speed):
    if 0 <= speed <= 360:
        return True
    return False
