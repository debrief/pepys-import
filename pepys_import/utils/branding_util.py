from pyfiglet import Figlet

PEPYS_PORTRAIT = [
    "    `:ssoo+`      ",
    "   /mdsohmMN+`    ",
    "  .MM+-.-:MMMd`   ",
    "  .NMs..`/NMMMy`  ",
    "  +Mm/--../hNMMy. ",
    "  yM:`::-.-/-NMMh ",
    "  /o`....`.` :ooo`",
]


def render_text(font, text):
    figlet = Figlet(font=font)
    rendered_text = figlet.renderText(text)
    text = list()
    for index, line in enumerate(rendered_text.splitlines()):
        if index < len(PEPYS_PORTRAIT):
            text.append(f"{PEPYS_PORTRAIT[index]}\t\t{line}")
    print("\n".join(text))


def show_welcome_banner(banner_text):
    font = "doom"
    text = banner_text
    render_text(font, text)


def show_software_meta_info(version, db_type, db_name, db_host):
    print("Software Version : ", version, "\n\n")
    print("Database Type : ", db_type)
    print("Database Name : ", db_name)
    print("Database Host : ", db_host)
