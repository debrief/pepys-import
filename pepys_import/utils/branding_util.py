from pyfiglet import Figlet


def render_text(font, text):
    figlet = Figlet(font=font)
    print(figlet.renderText(text))


def show_welcome_banner(banner_text):
    font = "doom"
    text = banner_text
    render_text(font, text)


def show_software_meta_info(version, db_type, db_name, db_host):
    print("Software Version : ", version, "\n\n")
    print("Database Type : ", db_type)
    print("Database Name : ", db_name)
    print("Database Host : ", db_host)
