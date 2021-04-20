from asyncio import Future

from prompt_toolkit.layout.containers import HSplit
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.widgets import Button, Label
from prompt_toolkit.widgets.dialogs import Dialog


class MessageDialog:
    def __init__(self, title, text=None):
        self.future = Future()

        if text is None:
            text = title

        def set_done():
            self.future.set_result(None)

        ok_button = Button(text="OK", handler=(lambda: set_done()))

        self.dialog = Dialog(
            title=title,
            body=HSplit([Label(text=text)]),
            buttons=[ok_button],
            width=D(preferred=80),
            modal=True,
        )

        # Get the keybindings for the dialog and add a binding for Esc
        # to close the dialog
        dialog_kb = self.dialog.container.container.content.key_bindings

        @dialog_kb.add("escape")
        def _(event) -> None:
            set_done()

    def __pt_container__(self):
        return self.dialog
