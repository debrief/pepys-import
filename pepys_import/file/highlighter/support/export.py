from .color_picker import color_for, hex_color_for, mean_color_for


def export_report(filename, chars, dict_colors, include_key=False):
    """
    Export a HTML report showing all the extraction usages for the file.

    :param filename: Output filename
    :param chars: Characters array (should be HighlightedFile.chars)
    :param dict_colors: Dictionary specifying colors to use (should be HighlightedFile.dict_colors)
    :param include_key: Whether to include a key at the bottom defining the usages of the colors

    This basically loops through all of the characters in the characters array, and then creates
    the relevant <span> tags for each character based on the usages stored for that character.
    """

    f_out = open(filename, "w")

    html_header = """<html>
    <head>
    </head>
    <body style="font-family: Courier">
    """

    f_out.write(html_header)

    last_hash = ""

    for char in chars:
        letter = char.letter
        this_hash = ""
        this_message = ""
        colors = []
        multi_usages = len(char.usages) > 1
        for usage in char.usages:
            this_hash += usage.tool_field
            needs_new_line = this_message != ""
            colors.append(color_for(usage.tool_field, dict_colors))
            if needs_new_line:
                this_message += "&#013;"
            if multi_usages:
                this_message += "-"
            this_message += usage.tool_field + ", " + usage.message

        # do we have anything to shade?
        if this_hash != "":
            # generate/retrieve a color for this hash
            new_color = mean_color_for(colors)
            hex_color = hex_color_for(new_color)

            # are we already in hash?
            if last_hash != "":
                # is it the different to this one?
                if last_hash != this_hash:
                    # ok, close the span
                    f_out.write("</span>")

                    # start a new span
                    f_out.write(
                        "<span title='"
                        + this_message
                        + "' style=\"background-color:"
                        + hex_color
                        + '"a>'
                    )
            else:
                f_out.write(
                    "<span title='"
                    + this_message
                    + "' style=\"background-color:"
                    + hex_color
                    + '">'
                )
        elif last_hash != "":
            f_out.write("</span>")

        # just check if it's newline
        if letter == "\n":
            f_out.write("<br>")
        else:
            f_out.write(letter)

        last_hash = this_hash

    if last_hash != "":
        f_out.write("</span>")

    # also provide a key
    if include_key:
        f_out.write("<hr/><h3>Color Key</h3><ul>")
        for key in dict_colors:
            color = dict_colors[key]
            hex_color = hex_color_for(color)
            f_out.write(
                '<li><span style="background-color:' + hex_color + '">' + key + "</span></li>"
            )
        f_out.write("</ul>")

    html_footer = """</body>
    </html>"""

    f_out.write(html_footer)

    f_out.close()
