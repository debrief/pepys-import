import os


def get_default_export_folder():
    current_folder_name = os.path.basename(os.path.normpath(os.getcwd()))
    if current_folder_name == "bin":
        return os.path.expanduser("~")
    else:
        return os.getcwd()
