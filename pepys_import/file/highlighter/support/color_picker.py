import colorsys
import itertools
import random

# Set of 30 distinct colours generated from https://mokole.com/palette.html
DISTINCT_COLORS_30 = [
    (128, 128, 128),
    (85, 107, 47),
    (139, 69, 19),
    (34, 139, 34),
    (72, 61, 139),
    (184, 134, 11),
    (0, 139, 139),
    (0, 0, 128),
    (154, 205, 50),
    (127, 0, 127),
    (143, 188, 143),
    (176, 48, 96),
    (255, 0, 0),
    (255, 140, 0),
    (255, 255, 0),
    (124, 252, 0),
    (138, 43, 226),
    (0, 255, 127),
    (233, 150, 122),
    (220, 20, 60),
    (0, 255, 255),
    (0, 0, 255),
    (255, 0, 255),
    (240, 230, 140),
    (100, 149, 237),
    (221, 160, 221),
    (144, 238, 144),
    (255, 20, 147),
    (123, 104, 238),
    (135, 206, 250),
]


def random_color():
    hue = random.random()
    sat = 0.9 + random.random() * 0.1
    rgb = colorsys.hsv_to_rgb(hue, sat, 0.9)
    r = int(rgb[0] * 255)
    g = int(rgb[1] * 255)
    b = int(rgb[2] * 255)
    new_col = (r, g, b)
    return new_col


# This creates an iterator which iterates over the list of distinct colours,
# looping around as necessary
COLORS = itertools.cycle(DISTINCT_COLORS_30)


def color_for(hash_code, color_dict):
    """
    Get a color for a specific 'hash code' by either taking one we've already recorded for
    this hash code, or generating a new random one.
    """
    # do we have it already?
    if hash_code in color_dict:
        # yes, job done
        return color_dict[hash_code]
    else:
        # no, get one from the list of distinct colours
        color = next(COLORS)

        color_dict[hash_code] = color
        return color


def html_color_for(rgb):
    """
    Convert a 3-element rgb structure to a HTML color definition
    """
    opacity_shade = 0.3
    return f"rgba({rgb[0]},{rgb[1]},{rgb[2]},{opacity_shade})"


def mean_color_for(color_arr):
    """
    find the mean of the provided colors

    Args:
        color_arr: three-element list of R, G and B components of color
    """
    if len(color_arr) == 1:
        return color_arr[0]

    r = 0
    g = 0
    b = 0
    for color in color_arr:
        r += color[0]
        g += color[1]
        b += color[2]

    arr_len = len(color_arr)
    return int(r / arr_len), int(g / arr_len), int(b / arr_len)
