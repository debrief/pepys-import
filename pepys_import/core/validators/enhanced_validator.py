"""
Enhanced tests actually serve to verify the lat/long, in addition to the course/speed/heading
"""
from geoalchemy2 import func, WKTElement
from sqlalchemy import select


class EnhancedValidator:
    def __init__(self, measurement_object, errors, message, prev_location, engine):
        self.error_message = message + f" - Enhanced Validation Error"
        self.errors = errors
        self.location = measurement_object.location
        self.heading = measurement_object.heading
        self.course = measurement_object.course
        self.prev_location = prev_location
        self.engine = engine

        self.course_heading_loose_match_with_location()
        self.speed_loose_match_with_location()

    def course_heading_loose_match_with_location(self):
        # TODO: calculate current location, put prev and curr location to ST_Distance,
        #  compare it with course and heading
        with self.engine.connect() as conn:
            query = select(
                [func.ST_Distance(self.location, WKTElement(self.prev_location))]
            )
            result = conn.execute(query)
            distance = result.fetchone()

        print(distance)

    def speed_loose_match_with_location(self):
        # TODO: calculate current location, put prev and curr location to ST_Distance,
        #  compare it with speed
        with self.engine.connect() as conn:
            query = select(
                [func.ST_Distance(self.location, WKTElement(self.prev_location))]
            )
            result = conn.execute(query)
            distance = result.fetchone()

        print(distance)
