from datetime import datetime
from .location import Location
from . import unit_registry, quantity


class State:

    def __init__(self, linenumber, line):
        self.lineNum = linenumber
        self.line = line

        self.timestamp = None
        self.vessel = None
        self.symbology = None
        self.latitude = None
        self.longitude = None
        self.heading = None
        self.speed = None
        self.depth = None
        self.textLabel = None

        # Initialize pint's unit registry object
        self.unit_registry = unit_registry

    def print(self):
        print("REP Line {} - Timestamp: {} Vessel: {} Symbology: {} Latitude: {} Longitude: {} Heading: {} Speed: {} Depth: {} TextLabel: {}"
              .format(self.lineNum, self.timestamp, self.vessel, self.symbology,
                      self.latitude, self.longitude, self.heading, self.speed, self.depth, self.textLabel))

    def parse(self):

        tokens = self.line.split()

        if len(tokens) < 15:
            print("Error on line {} not enough tokens: {}".format(self.lineNum, self.line))
            return False


        # separate token strings
        dateToken = tokens[0]
        timeToken = tokens[1]
        vesselNameToken = tokens[2]
        symbologyToken = tokens[3]
        latDegreesToken = tokens[4]
        latMinsToken = tokens[5]
        latSecsToken = tokens[6]
        latHemiToken = tokens[7]
        longDegreesToken = tokens[8]
        longMinsToken = tokens[9]
        longSecsToken = tokens[10]
        longHemiToken = tokens[11]
        headingToken = tokens[12]
        speedToken = tokens[13]
        depthToken = tokens[14]
        textLabelToken = ""




        if len(tokens) >= 16:
            # TODO: join back into single string, or extract full substring
            self.textLabelToken = tokens[15:]


        if len(dateToken) != 6 and len(dateToken) != 8:
            print("Line {}. Error in Date format {}. Should be either 2 of 4 figure date, followed by month then date".format(self.lineNum, dateToken))
            return False

        # Times always in Zulu/GMT
        if len(timeToken) != 6 and  len(timeToken) != 10:
            print("Line {}. Error in Time format {}. Should be HHMMSS[.SSS]".format(self.lineNum, timeToken))
            return False

        self.timestamp = self.parseTimestamp(dateToken, timeToken)

        self.vessel = vesselNameToken.strip('"')

        symVals = symbologyToken.split("[")
        if len(symVals) >= 1:
            if len(symVals[0]) != 2 and len(symVals[0]) != 5:
                print("Line {}. Error in Symbology format {}. Should be 2 or 5 chars".format(self.lineNum, symbologyToken))
                return False
        if len(symVals) != 1 and len(symVals) != 2:
            print("Line {}. Error in Symbology format {}".format(self.lineNum, symbologyToken))
            return False

        self.symbology = symbologyToken

        self.latitude = Location(latDegreesToken, latMinsToken, latSecsToken, latHemiToken)
        if not self.latitude.parse():
            print("Line {}. Error in latitude parsing".format(self.lineNum))
            return False

        self.longitude = Location(longDegreesToken, longMinsToken, longSecsToken, longHemiToken)
        if not self.latitude.parse():
            print("Line {}. Error in longitude parsing".format(self.lineNum))
            return False

        try:
            valid_heading = float(headingToken)
        except ValueError:
            print("Line {}. Error in heading value {}. Couldn't convert to a number".format(self.lineNum, headingToken))
            return False
        if 0.0 > valid_heading >= 360.0:
            print("Line {}. Error in heading value {}. Should be be between 0 and 359.9 degrees".format(self.lineNum, headingToken))
            return False

        # Set heading as degree(quantity-with-unit) object
        self.setHeading(valid_heading * self.unitreg.degree)

        try:
            valid_speed = float(speedToken)
        except ValueError:
            print("Line {}. Error in speed value {}. Couldn't convert to a number".format(self.lineNum, speedToken))
            return False
        
        # Set speed as knots(quantity-with-unit) object
        self.setSpeed(valid_speed * self.unitreg.knot)

        try:
            if depthToken == 'NaN':
                self.depth = 0.0
            else:
                self.depth = float(depthToken)
        except ValueError:
            print("Line {}. Error in depth value {}. Couldn't convert to a number".format(self.lineNum, depthToken))
            return False

        return True

    def parseTimestamp(self, date, time):
        if len(date) == 6:
            formatStr = '%y%m%d'
        else:
            formatStr = '%Y%m%d'

        if len(time) == 6:
            formatStr += '%H%M%S'
        else:
            formatStr += '%H%M%S.%f'

        return datetime.strptime(date + time, formatStr)

    def setSpeed(self, speed):
        self.speed = speed

    def setHeading(self, heading : quantity):
        self.heading = heading

    def setLatitude(self):
        pass
    
    def setLongitude(self):
        pass

    def getLineNum(self):
        return self.lineNum

    def getTimestamp(self):
        return self.timestamp

    def getPlatform(self):
        return self.vessel

    def getSymbology(self):
        return self.symbology

    def getLatitude(self):
        return self.latitude

    def getLongitude(self):
        return self.longitude

    def getHeading(self):
        return self.heading

    def getSpeed(self):
        return self.speed

    def getDepth(self):
        return self.depth

    def getTextLabel(self):
        return self.textLabel