from loguru import logger
from prompt_toolkit import Application
from prompt_toolkit.application.current import get_app
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import FloatContainer
from prompt_toolkit.styles import Style

from pepys_admin.maintenance.widgets.filter_widget import FilterWidget

logger.remove()
logger.add("gui.log")


def on_filter_widget_change(filters):
    logger.debug(filters)


column_data = {
    "platform_id": {"type": "id", "values": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]},
    "name": {"type": "string", "values": ["HMS Name1", "HMS Floaty", "USS Sinky"]},
    "identifier": {"type": "string"},
    "nationality_id": {"type": "id"},
    "nationality_name": {"type": "string"},
    "timestamp": {"type": "datetime"},
    "speed": {"type": "float"},
}

filter_widget = FilterWidget(column_data, on_change_handler=on_filter_widget_change)


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
        logger.debug(filter_widget.filters)

    root_container = FloatContainer(
        filter_widget,
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

    app = Application(
        layout=layout, full_screen=True, key_bindings=kb, style=style, mouse_support=True
    )

    return app


app = create_prompt_toolkit_app()
app.run()
