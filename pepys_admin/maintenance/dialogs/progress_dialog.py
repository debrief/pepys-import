import asyncio
from asyncio import Future
from asyncio.tasks import ensure_future
from functools import partial

from prompt_toolkit.application.current import get_app
from prompt_toolkit.layout.containers import HSplit
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.widgets import Button, Label, ProgressBar
from prompt_toolkit.widgets.dialogs import Dialog


class ProgressDialog:
    def __init__(self, title, run_callback, show_cancel=True):
        self.future = Future()

        def set_cancelled():
            self.cancelled = True
            self.future.set_result(None)

        cancel_button = Button(text="Cancel", handler=(lambda: set_cancelled()))

        self.progressbar = ProgressBar()
        self.progressbar.percentage = 0

        self.run_callback = run_callback
        self.cancelled = False

        self.dialog = Dialog(
            title=title,
            body=HSplit([Label(text="In progress..."), self.progressbar]),
            buttons=[cancel_button] if show_cancel else [],
            width=D(preferred=80),
            modal=True,
        )

        async def coroutine():
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,
                partial(
                    self.run_callback,
                    set_percentage=self.set_percentage,
                    is_cancelled=self.is_cancelled,
                ),
            )

        ensure_future(coroutine())

    def set_percentage(self, value: int) -> None:
        if value == 100:
            self.future.set_result(None)

        self.progressbar.percentage = int(value)
        app = get_app()
        app.invalidate()

    def is_cancelled(self):
        return self.cancelled

    def __pt_container__(self):
        return self.dialog
