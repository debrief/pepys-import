import os

from pepys_admin.admin_cli import AdminShell

DIR_PATH = os.path.dirname(os.path.abspath(__file__))


class ViewerShell(AdminShell):
    """The ViewerShell is a limited version of the AdminShell. It inherits from AdminShell so we don't
    have to re-implement each function."""

    choices = """(1) Status
(2) View Data
(3) View Docs
(4) View dashboard
(.) Exit
"""
    prompt = "(pepys-viewer) "

    def __init__(self, data_store, csv_path=DIR_PATH):
        super(ViewerShell, self).__init__(data_store, csv_path)
        self.viewer = True
        self.data_store = data_store
        self.csv_path = csv_path
        self.aliases = {
            ".": self.do_exit,
            "1": self.do_status,
            "2": self.do_view_data,
            "3": self.do_view_docs,
            "4": self.do_view_dashboard,
        }
