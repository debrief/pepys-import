from pyfiglet import Figlet


def render_text(font, text):
    f = Figlet(font=font)
    print(f.renderText(text))


def show_welcome_banner():
    font = "doom"
    text = "Pepys_import"
    render_text(font, text)


def show_software_meta_info(version, db_type, db_name, db_host):
    print("Software Version : ", version, "\n\n")
    print("Database Type : ", db_type)
    print("Database Name : ", db_name)
    print("Database Host : ", db_host)
