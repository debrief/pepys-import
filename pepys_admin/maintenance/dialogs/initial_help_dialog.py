import os

from prompt_toolkit.application.current import get_app
from prompt_toolkit.filters.base import Condition
from prompt_toolkit.layout.containers import ConditionalContainer

from pepys_admin.maintenance.dialogs.help_dialog import HelpDialog


class InitialHelpDialog(HelpDialog):
    def __init__(self, title, text, position=0):
        self.visible = True

        super().__init__(title, text, position)

        self.container = ConditionalContainer(
            self.dialog,
            Condition(lambda: self.visible),
        )

    def set_done(self):
        self.visible = False

        # Write file, so this isn't shown again
        file_path = os.path.expanduser(os.path.join("~", ".pepys_maintenance_help.txt"))
        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                f.write(
                    "This file is used as a flag to indicate that the user has seen the Pepys Maintenance Help.\n"
                    "The guidance is only displayed the first time it is used."
                )

        app = get_app()
        app.layout.focus(app.layout.container.content)
        self.future.set_result(None)

    def __pt_container__(self):
        return self.container
