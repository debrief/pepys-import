from asyncio import Future

from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.widgets import Button
from prompt_toolkit.widgets.dialogs import Dialog


class HelpDialog:
    # This is different from a simple MessageDialog because
    # the text is scrollable, which may be important for longer bits
    # of help
    def __init__(self, title, text):
        self.future = Future()

        def set_done():
            self.future.set_result(None)

        close_button = Button(text="Close", handler=(lambda: set_done()))
        doc = Document(text, 0)
        buffer = Buffer(read_only=True, document=doc, multiline=True)
        buffer_control = BufferControl(buffer)

        self.dialog = Dialog(
            title=title,
            body=HSplit([Window(buffer_control, wrap_lines=True)]),
            buttons=[close_button],
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
