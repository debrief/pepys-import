from datetime import datetime
from .location import Location
from . import unit_registry, quantity


class State2:
    def __init__(self, timestamp, datafile):

        self.timestamp = timestamp
        self.vessel = None
        self.symbology = None
        self.latitude = None
        self.longitude = None
        self.heading = None
        self.speed = None
        self.depth = None
        self.text_label = None

        # Initialize pint's unit registry object
        self.unit_registry = unit_registry

    def print(self):
        print(
            "State: Timestamp: {} Vessel: {} Symbology: {} Latitude: {} Longitude: {} Heading: {} Speed: {} Depth: {} TextLabel: {}".format(
                self.timestamp,
                self.vessel,
                self.symbology,
                self.latitude,
                self.longitude,
                self.heading,
                self.speed,
                self.depth,
                self.text_label,
            )
        )

    def set_speed(self, speed):
        self.speed = speed

    def set_heading(self, heading: quantity):
        self.heading = heading

    def set_latitude(self):
        pass

    def set_longitude(self):
        pass

    def get_timestamp(self):
        return self.timestamp

    def get_platform(self):
        return self.vessel

    def get_symbology(self):
        return self.symbology

    def get_latitude(self):
        return self.latitude

    def get_longitude(self):
        return self.longitude

    def get_heading(self):
        return self.heading

    def get_speed(self):
        return self.speed

    def get_depth(self):
        return self.depth

    def get_text_label(self):
        return self.text_label
