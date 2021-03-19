from loguru import logger
from prompt_toolkit import Application
from prompt_toolkit.application.current import get_app
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import FloatContainer
from prompt_toolkit.styles import Style

from pepys_admin.maintenance.widgets.tree_view import TreeElement, TreeView

logger.remove()
logger.add("gui.log")

root = TreeElement("root", 42)
root.add_child(TreeElement("first level", 14))
root.add_child(TreeElement("first level - 2", 29))
second_level = root.children[0].add_child(TreeElement("second level", 20))
second_level.add_child(TreeElement("third level", 999))

root.expanded = True

i = 0


def on_add(selected_element):
    global i
    new_element = TreeElement(f"New entry {i}", None)
    selected_element.add_child(new_element)
    i += 1


def create_prompt_toolkit_app():
    kb = KeyBindings()

    kb.add("tab")(focus_next)
    kb.add("s-tab")(focus_previous)

    @kb.add("escape")
    def exit_handler(event=None) -> None:
        "Button handler that exits the app"
        get_app().exit()

    tree_view = TreeView(root, on_add=on_add)

    root_container = FloatContainer(
        tree_view,
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
            ("selected-element", "bg:ansicyan fg:ansiwhite"),
            ("add-button", "bg:ansigray"),
            ("add-button-focused", "bg:ansired fg:ansiwhite"),
            ("lines", "fg:ansibrightblack"),
        ]
    )

    app = Application(
        layout=layout, full_screen=True, key_bindings=kb, style=style, mouse_support=True
    )

    return app


app = create_prompt_toolkit_app()
app.run()
