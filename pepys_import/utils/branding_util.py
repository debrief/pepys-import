from pyfiglet import Figlet

PEPYS_PORTRAIT = [
    # portrait 1
    "   @@@@ @@@@@       ",
    " @@@@@ @@..@@@@     ",
    "  @@@     @@@@@@    ",
    "  @@@     @@@@@@@@  ",
    " @@@@.     @@@@@@@  ",
    " @@ #@@ @   ...@@@@@",
    " @@   &        @@@@@  ",
    # portrait 2
    # " `yMmysymMMN+`     ",
    # ".NMM+:`//.NMMm.    ",
    # ".MMM -. -.MMMMMd`   ",
    # ".NMMo '-  mMMMMMs   ",
    # "-NMMh -o- mMMMMMs  ",
    # "mMMMM:....-dMMMNy.",
    # "dMy` --/`  ...sMMMM:",
    # portrait 3
    # "    `:ssoo+`      ",
    # "   /mdsohmMN+`    ",
    # "  .MM+-.-:MMMd`   ",
    # "  .NMs..`/NMMMy`  ",
    # "  +Mm/--../hNMMy. ",
    # "  yM:`::-.-/-NMMh ",
    # "  /o`....`.` :ooo`",
]


def render_text(font, text):
    figlet = Figlet(font=font)
    rendered_text = figlet.renderText(text)
    text = list()
    for index, line in enumerate(rendered_text.splitlines()):
        if index < len(PEPYS_PORTRAIT):
            text.append(f"{PEPYS_PORTRAIT[index]} {line}")
    print("\n".join(text))


def show_welcome_banner(banner_text):
    font = "doom"
    text = banner_text
    render_text(font, text)


def show_software_meta_info(version, db_type, db_name, db_host, training_mode):
    print("Software Version : ", version, "\n\n")
    print("Database Type : ", db_type)
    print("Database Name : ", db_name)
    print("Database Host : ", db_host)
    if training_mode:
        print("\nRunning in Training Mode")
