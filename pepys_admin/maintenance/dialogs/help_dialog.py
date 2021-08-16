from asyncio import Future

from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.widgets import Button, Label
from prompt_toolkit.widgets.dialogs import Dialog


class HelpDialog:
    # This is different from a simple MessageDialog because
    # the text is scrollable, which may be important for longer bits
    # of help
    def __init__(self, title, text, position=0):
        self.future = Future()

        from pygments.lexers.markup import MarkdownLexer

        lexer = PygmentsLexer(MarkdownLexer)

        self.close_button = Button(text="Close", handler=self.set_done)
        doc = Document(text, position)
        buffer = Buffer(read_only=True, document=doc, multiline=True)
        buffer_control = BufferControl(buffer, lexer=lexer)

        self.dialog = Dialog(
            title=title,
            body=HSplit(
                [
                    Label(
                        "Use up/down to scroll, and Esc to exit",
                        style="class:instruction-text-dark",
                    ),
                    Window(buffer_control, wrap_lines=True),
                ],
                padding=1,
            ),
            buttons=[self.close_button],
            width=D(preferred=80),
            modal=True,
        )

        # Get the keybindings for the dialog and add a binding for Esc
        # to close the dialog
        dialog_kb = self.dialog.container.container.content.key_bindings

        @dialog_kb.add("escape")
        def _(event) -> None:
            self.set_done()

    def set_done(self):
        self.future.set_result(None)

    def __pt_container__(self):
        return self.dialog
