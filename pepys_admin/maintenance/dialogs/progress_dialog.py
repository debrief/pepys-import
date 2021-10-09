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
    """Dialog showing a progress bar, with an optional Cancel button."""

    def __init__(self, title, run_callback, show_cancel=True):
        """Creates a dialog object which will show a dialog with a progress bar
        and an optional cancel button.

        Arguments:
        - `title`: Title for the dialog box
        - `run_callback`: Function to be called to do the actual work. This must be a
          normal, non-async function. It must take two keyword arguments: set_percentage
          and is_cancelled. When the function is called, two separate functions will
          be passed in as those two arguments. The set_percentage argument can be called
          with a number between 0 and 100 to set the progress bar to that value, and the
          is_cancelled function will return True if the cancel button has been pressed.
          The function given will be called with those two arguments only, if other
          arguments need passing then use functools.partial to pass them. The function
          must be thread-safe, as it is called in a separate thread.
        - `show_cancel`: Whether to show a cancel button or not (boolean, default True)
        """
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
            # This runs the run_callback function in a separate thread
            # but as part of the asyncio loop, so the GUI can still update
            # while a potentially-blocking function runs in the background
            try:
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(
                    None,
                    partial(
                        self.run_callback,
                        set_percentage=self.set_percentage,
                        is_cancelled=self.is_cancelled,
                    ),
                )
                get_app().progress_bar_finished.fire()
                self.future.set_result(result)
            except Exception as e:
                try:
                    self.future.set_result(e)
                except asyncio.InvalidStateError:
                    pass

        ensure_future(coroutine())

    def set_percentage(self, value: int) -> None:
        self.progressbar.percentage = int(value)
        # Refresh the GUI
        app = get_app()
        app.invalidate()

    def is_cancelled(self):
        return self.cancelled

    def __pt_container__(self):
        return self.dialog
