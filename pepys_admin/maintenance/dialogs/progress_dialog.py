from asyncio import Future
from asyncio.tasks import ensure_future

from prompt_toolkit.application.current import get_app
from prompt_toolkit.layout.containers import HSplit
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.widgets import Button, Label, ProgressBar
from prompt_toolkit.widgets.dialogs import Dialog


class ProgressDialog:
    def __init__(self, title, run_callback):
        self.future = Future()

        def set_cancelled():
            self.cancelled = True
            self.future.set_result(None)

        ok_button = Button(text="Cancel", handler=(lambda: set_cancelled()))

        self.progressbar = ProgressBar()
        self.progressbar.percentage = 0

        self.run_callback = run_callback
        self.cancelled = False

        self.dialog = Dialog(
            title=title,
            body=HSplit([Label(text="In progress..."), self.progressbar]),
            buttons=[ok_button],
            width=D(preferred=80),
            modal=True,
        )

        # Get the keybindings for the dialog and add a binding for Esc
        # to close the dialog
        # dialog_kb = self.dialog.container.container.content.key_bindings

        # @dialog_kb.add("escape")
        # def _(event) -> None:
        #     set_done()

        async def coroutine():
            await self.run_callback(self.set_percentage, self.is_cancelled)

        ensure_future(coroutine())

    def set_percentage(self, value: int) -> None:
        self.progressbar.percentage = int(value)
        app = get_app()
        app.invalidate()

    def is_cancelled(self):
        return self.cancelled

    def __pt_container__(self):
        return self.dialog
