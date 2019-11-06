class Location:
    def __init__(self, degrees, minutes, seconds, hemisphere):
        self.degrees = degrees
        self.minutes = minutes
        self.seconds = seconds
        self.hemisphere = hemisphere

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

    def parse(self):
        try:
            self.degrees = float(self.degrees)
        except ValueError:
            print(
                f"Error in degrees value {self.degrees}. Couldn't convert to a number"
            )
            return False

        try:
            self.minutes = float(self.minutes)
        except ValueError:
            print(
                f"Error in minutes value {self.minutes}. Couldn't convert to a number"
            )
            return False

        try:
            self.seconds = float(self.seconds)
        except ValueError:
            print(
                f"Error in seconds value {self.seconds}. Couldn't convert to a number"
            )
            return False

        if self.hemisphere not in ("N", "S", "E", "W"):
            print(
                f"Error in hemisphere value {self.hemisphere}. "
                f"Should be one of N, S, E or W"
            )
            return False

        return True
