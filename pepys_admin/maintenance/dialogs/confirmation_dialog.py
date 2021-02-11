from asyncio import Future

from prompt_toolkit.layout.containers import HSplit
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.widgets import Button, Label
from prompt_toolkit.widgets.dialogs import Dialog


class ConfirmationDialog:
    def __init__(self, title, text):
        self.future = Future()

        def handle_yes():
            self.future.set_result(True)

        def handle_no():
            self.future.set_result(False)

        yes_button = Button(text="Yes", handler=(lambda: handle_yes()))
        no_button = Button(text="No", handler=(lambda: handle_no()))

        self.dialog = Dialog(
            title=title,
            body=HSplit([Label(text=text)]),
            buttons=[yes_button, no_button],
            width=D(preferred=80),
            modal=True,
        )

    def __pt_container__(self):
        return self.dialog
