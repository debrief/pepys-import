import pepys_import.file.smb_and_local_file_operations as smblocal

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

    output_strings = []

    html_header = """<html>
    <head>
    </head>
    <body style="font-family: Courier">
    """

    output_strings.append(html_header)

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
                    output_strings.append("</span>")

                    # start a new span
                    output_strings.append(
                        f"<span title='{this_message}' style=\"background-color:{hex_color}\">"
                    )
            else:
                output_strings.append(
                    f"<span title='{this_message}' style=\"background-color:{hex_color}\">"
                )
        elif last_hash != "":
            output_strings.append("</span>")

        # just check if it's newline
        if letter == "\n":
            output_strings.append("<br>")
        else:
            output_strings.append(letter)

        last_hash = this_hash

    if last_hash != "":
        output_strings.append("</span>")

    # also provide a key
    if include_key:
        output_strings.append("<hr/><h3>Color Key</h3><ul>")
        for key in dict_colors:
            color = dict_colors[key]
            hex_color = hex_color_for(color)
            output_strings.append(
                f'<li><span style="background-color:{hex_color}">{key}</span></li>'
            )
        output_strings.append("</ul>")

    html_footer = """</body>
    </html>"""

    output_strings.append(html_footer)

    with smblocal.open_file(filename, "w") as f:
        f.write("".join(output_strings))
