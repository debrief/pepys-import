from datetime import datetime

from loguru import logger
from prompt_toolkit import Application
from prompt_toolkit.application.current import get_app
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.layout import HSplit, Layout
from prompt_toolkit.layout.containers import FloatContainer
from prompt_toolkit.styles import Style
from prompt_toolkit.validation import Validator
from prompt_toolkit.widgets.toolbars import ValidationToolbar

from pepys_admin.maintenance.widgets.masked_input_widget import MaskedInputWidget
from pepys_admin.maintenance.widgets.utils import int_validator

logger.remove()
logger.add("gui.log")


def validate_datetime(s):
    try:
        datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return False
    return True


datetime_validator = Validator.from_callable(
    validate_datetime,
    error_message="This input is not a valid datetime value",
    move_cursor_to_end=True,
)


def create_prompt_toolkit_app():
    kb = KeyBindings()

    kb.add("tab")(focus_next)
    kb.add("s-tab")(focus_previous)

    @kb.add("escape")
    def exit_handler(event=None) -> None:
        "Button handler that exits the app"
        get_app().exit()

    @kb.add("c-a")
    def _(event):
        logger.debug(miw.text)

    miw = MaskedInputWidget(
        ["yyyy", "!-", "mm", "!-", "dd", "! ", "HH", "!:", "MM", "!:", "SS"],
        part_validator=int_validator,
        overall_validator=datetime_validator,
    )

    root_container = FloatContainer(
        HSplit([miw, ValidationToolbar()]),
        floats=[],
    )

    layout = Layout(root_container)

    # Styling.
    style = Style(
        [
            ("button", "#000000"),
            ("button-arrow", "#000000"),
            ("button.focused", "bg:#ff0000"),
            ("dropdown", "bg:#ffff00"),
            ("dropdown.focused", "bg:#ff0000"),
            ("text-area focused", "bg:#ff0000"),
            ("completion-menu.completion.current", "bg:#ff0000"),
            ("dropdown-highlight", "#ff0000"),
            ("filter-text", "fg:#0000ff"),
        ]
    )

    app = Application(layout=layout, full_screen=True, key_bindings=kb, style=style)

    return app


app = create_prompt_toolkit_app()
app.run()
