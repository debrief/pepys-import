def format_datatime(datetime):
    microsecond_text = ""
    if datetime.microsecond:
        if datetime.microsecond > 9999:
            microsecond_text = ".9999"
        else:
            microsecond_text = "." + str(datetime.microsecond).zfill(4)

    return datetime.strftime("%Y%m%d %H%M%S") + microsecond_text


def break_point_dimention_to_sub_units(val):
    degree = int(val)

    minutesFloat = (val - degree) * 60
    minutes = int(minutesFloat)

    secondsFloat = (minutesFloat - minutes) * 60

    return [degree, minutes, secondsFloat]


def format_point_dimention(val, hemisphere_pair):
    [degree, minutes, seconds] = break_point_dimention_to_sub_units(abs(val))
    [positive, negative] = hemisphere_pair
    return " ".join(
        [str(degree), str(minutes), str(round(seconds, 3)), negative if val < 0 else positive]
    )


def format_point(x, y):
    return format_point_dimention(x, ["N", "S"]) + " " + format_point_dimention(y, ["E", "W"])
