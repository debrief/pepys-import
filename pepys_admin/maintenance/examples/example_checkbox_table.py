from loguru import logger
from prompt_toolkit import Application
from prompt_toolkit.application.current import get_app
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import FloatContainer
from prompt_toolkit.styles import Style

from pepys_admin.maintenance.widgets.checkbox_table import CheckboxTable

logger.remove()
logger.add("gui.log")


table_data = [
    ["Name", "Type", "Nat."],
    ["NELSON", "Frigate", "UK"],
    ["SARK", "Destroyer blah blah blah", "UK"],
    ["ADRI", "Frigate", "UK"],
    ["JEAN", "Corvette", "France with very long entry"],
]

table_objects = [None, 1, 2, 3, 4]

checkbox_table = CheckboxTable(table_data, table_objects)


def create_prompt_toolkit_app():
    kb = KeyBindings()

    kb.add("tab")(focus_next)
    kb.add("s-tab")(focus_previous)

    @kb.add("escape")
    def exit_handler(event=None) -> None:
        "Button handler that exits the app"
        get_app().exit()

    root_container = FloatContainer(
        checkbox_table,
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
            ("table-title", "fg:#ff0000"),
            ("checkbox-selected", "bg:ansiyellow"),
        ]
    )

    app = Application(
        layout=layout, full_screen=True, key_bindings=kb, style=style, mouse_support=True
    )

    return app


app = create_prompt_toolkit_app()
app.run()
