from shapely import wkb


class Location:
    def __init__(self, errors=None, error_type=None):
        self._latitude = None
        self._longitude = None

        if errors is None:
            self.errors = list()
        else:
            self.errors = errors
        if error_type is None:
            self.error_type = "Location Parsing Error"
        else:
            self.error_type = error_type

    def __repr__(self):
        return f"Location(lon={self.longitude}, lat={self.latitude})"

    def __str__(self):
        return f"{self.longitude:.3f}, {self.latitude:.3f}"

    def __eq__(self, other):
        if not isinstance(other, Location):
            # don't attempt to compare against unrelated types
            return NotImplemented

        return self.latitude == other.latitude and self.longitude == other.longitude

    # Property to make a read-only .latitude property
    # that mirrors the hidden _latitude attribute
    @property
    def latitude(self):
        """Returns the latitude of the Location object, in decimal degrees

        :return: Latitude
        :rtype: float
        """
        return self._latitude

    @latitude.setter
    def latitude(self, value):
        raise AttributeError(
            "Cannot set latitude directly. Use set_latitude_decimal_degrees or set_latitude_dms"
        )

    # Property to make a read-only .longitude property
    # that mirrors the hidden _longitude attribute
    @property
    def longitude(self):
        """Returns the longitude of the Location object, in decimal degrees

        :return: Longitude
        :rtype: float
        """
        return self._longitude

    @longitude.setter
    def longitude(self, value):
        raise AttributeError(
            "Cannot set longitude directly. Use set_longitude_decimal_degrees or set_longitude_dms"
        )

    def _convert_and_check_degrees(self, degrees, lat_or_lon):
        try:
            degrees = float(degrees)
        except ValueError:
            self.errors.append(
                {
                    self.error_type: f"Error in {lat_or_lon} decimal degrees value {degrees}. "
                    f"Couldn't convert to a number"
                }
            )

            return None, False

        if lat_or_lon == "latitude":
            max_value = 90
            min_value = -90
        elif lat_or_lon == "longitude":
            max_value = 180
            min_value = -180
        if degrees < min_value or degrees > max_value:
            self.errors.append(
                {
                    self.error_type: f"Error in {lat_or_lon} degrees value {degrees}. "
                    f"Must be between {min_value} and {max_value}"
                }
            )

            return None, False

        return degrees, True

    def _convert_and_check_minutes(self, minutes, lat_or_lon):
        try:
            minutes = float(minutes)
        except ValueError:
            self.errors.append(
                {
                    self.error_type: f"Error in {lat_or_lon} minutes value {minutes}. "
                    f"Couldn't convert to a number"
                }
            )
            return None, False

        if minutes < 0 or minutes > 60:
            self.errors.append(
                {
                    self.error_type: f"Error in {lat_or_lon} minutes value {minutes}. "
                    f"Must be between 0 and 60"
                }
            )
            return None, False

        return minutes, True

    def _convert_and_check_seconds(self, seconds, lat_or_lon):
        try:
            seconds = float(seconds)
        except ValueError:

            self.errors.append(
                {
                    self.error_type: f"Error in {lat_or_lon} seconds value {seconds}. "
                    f"Couldn't convert to a number"
                }
            )
            return None, False

        if seconds < 0 or seconds > 60:

            self.errors.append(
                {
                    self.error_type: f"Error in {lat_or_lon} seconds value {seconds}. "
                    f"Must be between 0 and 60"
                }
            )
            return None, False

        return seconds, True

    def _convert_and_check_hemisphere(self, hemisphere, lat_or_lon):
        hemisphere = hemisphere.upper()

        if lat_or_lon == "latitude":
            valid_hemisphere_values = ("N", "S")
        elif lat_or_lon == "longitude":
            valid_hemisphere_values = ("E", "W")

        if hemisphere not in valid_hemisphere_values:
            self.errors.append(
                {
                    self.error_type: f"Error in {lat_or_lon} hemisphere value {hemisphere}. "
                    f"Must be {' or '.join(valid_hemisphere_values)}"
                }
            )
            return None, False

        return hemisphere, True

    def set_latitude_decimal_degrees(self, latitude):
        """Sets the latitude of the Location object to a latitude given in decimal degrees

        :param latitude: Latitude to set to, in decimal degrees (use +/- values for North/South)
        :type latitude: float
        :return: Whether latitude was set successfully
        :rtype: Boolean
        """
        latitude, is_valid = self._convert_and_check_degrees(latitude, "latitude")

        if not is_valid:
            return False
        else:
            self._latitude = latitude
            return True

    def set_longitude_decimal_degrees(self, longitude):
        """Sets the longitude value of the Location object to a longitude given in decimal degrees

        :param longitude: Longitude to set to, in decimal degrees (use +/- values for East/West)
        :type longitude: float
        :return: Whether longitude was set successfully
        :rtype: Boolean
        """
        longitude, is_valid = self._convert_and_check_degrees(longitude, "longitude")

        if not is_valid:
            return False
        else:
            self._longitude = longitude
            return True

    def set_latitude_dms(self, degrees, minutes, seconds, hemisphere):
        """Sets the latitude value of the Location object to a latitude given in degrees, minutes
        and seconds format.

        :param degrees: Degrees of latitude (must be positive float)
        :type degrees: float
        :param minutes: Minutes of latitude (must be positive float)
        :type minutes: float
        :param seconds: Seconds of latitude (must be positive float)
        :type seconds: float
        :param hemisphere: Hemisphere of latitude (must be "N" or "S")
        :type hemisphere: String
        :return: Whether latitude was set successfully
        :rtype: Boolean
        """
        degrees, is_valid = self._convert_and_check_degrees(degrees, "latitude")
        if not is_valid:
            return False

        minutes, is_valid = self._convert_and_check_minutes(minutes, "latitude")
        if not is_valid:
            return False

        seconds, is_valid = self._convert_and_check_seconds(seconds, "latitude")
        if not is_valid:
            return False

        hemisphere, is_valid = self._convert_and_check_hemisphere(hemisphere, "latitude")
        if not is_valid:
            return False

        decimal_degrees = degrees + (minutes / 60) + (seconds / 3600)

        if hemisphere == "S":
            decimal_degrees *= -1

        self._latitude = decimal_degrees
        return True

    def set_longitude_dms(self, degrees, minutes, seconds, hemisphere):
        """Sets the longitude value of the Location object to a longitude given in degrees, minutes
        and seconds format.

        :param degrees: Degrees of longitude (must be positive float)
        :type degrees: float
        :param minutes: Minutes of longitude (must be positive float)
        :type minutes: float
        :param seconds: Seconds of longitude (must be positive float)
        :type seconds: float
        :param hemisphere: Hemisphere of longitude (must be "E" or "W")
        :type hemisphere: String
        :return: Whether longitude was set successfully
        :rtype: Boolean
        """
        degrees, is_valid = self._convert_and_check_degrees(degrees, "longitude")
        if not is_valid:
            return False

        minutes, is_valid = self._convert_and_check_minutes(minutes, "longitude")
        if not is_valid:
            return False

        seconds, is_valid = self._convert_and_check_minutes(seconds, "longitude")
        if not is_valid:
            return False

        hemisphere, is_valid = self._convert_and_check_hemisphere(hemisphere, "longitude")
        if not is_valid:
            return False

        decimal_degrees = degrees + (minutes / 60) + (seconds / 3600)

        if hemisphere == "W":
            decimal_degrees *= -1

        self._longitude = decimal_degrees
        return True

    def to_wkt(self):
        """Returns the location stored in the Location object in Well-Known Text format,
        ready for assigning to the _location attribute of a SQLAlchemy/GeoAlchemy model

        :return: Well-Known Text of location
        :rtype: String
        """
        return f"SRID=4326;POINT({self.longitude} {self.latitude})"

    def set_from_wkb(self, wkb_string):
        """Sets the location from a Well-Known Binary blob

        :param wkb_string: String containing Well-Known Binary blog in hex format
        :type wkb_string: String
        """
        point = wkb.loads(wkb_string, hex=True)

        self._longitude = point.x
        self._latitude = point.y

    def set_from_wkt_string(self, wkt_string):
        """Sets the location from a Well-Known Text string

        :param wkt_string: Well-Known Text
        :type wkt_string: String
        """
        longitude, latitude = wkt_string[16:-1].split()

        self._latitude = float(latitude)
        self._longitude = float(longitude)

    def check_valid(self):
        """Checks whether the location is valid (ie. has both a latitude and a longitude)

        :return: Validity
        :rtype: Boolean
        """
        if self._latitude is None:
            return False

        if self._longitude is None:
            return False

        return True

    def decimal_degrees_to_degrees_minutes_seconds(self):
        """Converts decimal degrees of latitude and longitude values to
        degrees, minutes, and seconds"""

        if self.check_valid():
            latitude = abs(self.latitude)
            lat_minutes, lat_seconds = divmod(latitude * 3600, 60)
            lat_degrees, lat_minutes = divmod(lat_minutes, 60)

            longitude = abs(self.longitude)
            lon_minutes, lon_seconds = divmod(longitude * 3600, 60)
            lon_degrees, lon_minutes = divmod(lon_minutes, 60)
            return lat_degrees, lat_minutes, lat_seconds, lon_degrees, lon_minutes, lon_seconds

    def convert_point(self):
        """
        Returns formatted latitude and longitude values. The format is as follows:
            DD(D) MM SS.SS H (Degrees Minutes Seconds Hemisphere)
        """
        dms_values = self.decimal_degrees_to_degrees_minutes_seconds()
        latitude = f"{dms_values[0]:02g} {dms_values[1]:02g} {dms_values[2]:02g}"
        latitude_hemisphere = "N" if self.latitude >= 0 else "S"
        longitude = f"{dms_values[3]:03g} {dms_values[4]:02g} {dms_values[5]:02g}"
        longitude_hemisphere = "E" if self.longitude >= 0 else "W"
        return f"{latitude} {latitude_hemisphere}\t{longitude} {longitude_hemisphere}"

    @classmethod
    def from_geometry(cls, geom):
        if geom is not None:
            loc = Location()
            if isinstance(geom, str):
                loc.set_from_wkt_string(geom)
            else:
                loc.set_from_wkb(geom.desc)

            return loc
        else:
            return None
