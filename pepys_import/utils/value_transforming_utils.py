def format_datetime(datetime):
    """Converts datetime to an appropriate format. The format is as follows:
        YYMMDD HHMMSS.SSS (Date, either 2 of 4 figure date, followed by month then date, and Time)

    :param datetime: Datetime of the object
    :type datetime: Datetime.Datetime
    :return: Converted datetime
    :rtype: str
    """
    return datetime.strftime("%y%m%d %H%M%S") + "." + str(datetime.microsecond).zfill(3)
