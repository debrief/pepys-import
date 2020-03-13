class Location:
    def __init__(
        self, degrees, minutes, seconds, hemisphere, errors=None, error_type=None
    ):
        self.degrees = degrees
        self.minutes = minutes
        self.seconds = seconds
        self.hemisphere = hemisphere

        if errors is None:
            self.errors = list()
        else:
            self.errors = errors
        if error_type is None:
            self.error_type = "Location Parsing Error"
        else:
            self.error_type = error_type

    def __repr__(self):
        return (
            "("
            + str(self.degrees)
            + ", "
            + str(self.minutes)
            + ", "
            + str(self.seconds)
            + ", "
            + self.hemisphere
            + ")"
        )

    def __eq__(self, other):
        if not isinstance(other, Location):
            # don't attempt to compare against unrelated types
            return NotImplemented

        return (
            self.degrees == other.degrees
            and self.minutes == other.minutes
            and self.seconds == other.seconds
            and self.hemisphere == other.hemisphere
        )

    # provide representation of this location element in whole degrees
    def as_degrees(self):
        degs = self.degrees + self.minutes / 60 + self.seconds / 3600
        if self.hemisphere.upper() in ("S", "W"):
            degs *= -1
        return degs

    def parse(self):
        try:
            self.degrees = float(self.degrees)
        except ValueError:
            self.errors.append(
                {
                    self.error_type: f"Error in degrees value {self.degrees}. Couldn't convert to a number"
                }
            )
            return False

        try:
            self.minutes = float(self.minutes)
        except ValueError:
            self.errors.append(
                {
                    self.error_type: f"Error in minutes value {self.minutes}. Couldn't convert to a number"
                }
            )
            return False

        try:
            self.seconds = float(self.seconds)
        except ValueError:
            self.errors.append(
                {
                    self.error_type: f"Error in seconds value {self.seconds}. Couldn't convert to a number"
                }
            )
            return False

        if self.hemisphere not in ("N", "S", "E", "W"):
            self.errors.append(
                {
                    self.error_type: f"Error in hemisphere value {self.hemisphere}. "
                    f"Should be one of N, S, E or W"
                }
            )
            return False

        return True
