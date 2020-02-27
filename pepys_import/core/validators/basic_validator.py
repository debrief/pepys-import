import logging
import os

file_name = os.path.basename(__file__)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s: - %(message)s", level=logging.DEBUG
)
log = logging.getLogger(file_name)
log.setLevel(logging.DEBUG)


def validate_longitude(longitude):
    if -90 <= longitude <= 90:
        return True
    log.warning("(%s) longitude error! It should be between -90 and 90.", longitude)
    return False


def validate_latitude(latitude):
    if -180 <= latitude <= 180:
        return True
    log.warning("(%s) latitude error! It should be between -180 and 180.", latitude)
    return False


def validate_heading(heading):
    if 0 <= heading <= 360:
        return True
    log.warning("(%s) heading error! It should be between 0 and 360 degrees.", heading)
    return False


def validate_course(course):
    if 0 <= course <= 360:
        return True
    log.warning("(%s) course error! It should be between 0 and 360 degrees.", course)
    return False


def basic_validation(longitude, latitude, heading, course):
    return (
        validate_longitude(longitude)
        and validate_latitude(latitude)
        and validate_heading(heading)
        and validate_course(course)
    )


# basic_validation(-100, -20, 50, 50)
