from prompt_toolkit import Application
from prompt_toolkit.application.current import get_app
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import (
    DynamicContainer,
    FloatContainer,
    HSplit,
    VSplit,
    Window,
)
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.widgets import Button
from prompt_toolkit.widgets.base import Label, TextArea


class ExampleApp:
    def __init__(self):
        kb = KeyBindings()

        kb.add("tab")(focus_next)
        kb.add("s-tab")(focus_previous)

        @kb.add("escape")
        def _(event=None) -> None:
            get_app().exit()

        @kb.add("c-a")
        def _(event):
            self.add_entry()

        self.rows = []
        self.add_button = Button("Add entry", handler=self.add_entry)

        self.dyn_container = DynamicContainer(self.get_container_contents)
        self.bottom_pane = HSplit([Label("Bottom pane here")], height=Dimension(weight=0.5))

        root_container = FloatContainer(
            HSplit([self.dyn_container, Window(char="-", height=1), self.bottom_pane]),
            floats=[],
        )

        layout = Layout(root_container)

        self.app = Application(layout=layout, full_screen=True, key_bindings=kb, mouse_support=True)

    def get_container_contents(self):
        contents = [row.get_widgets() for row in self.rows]

        contents.append(self.add_button)

        return HSplit(contents, padding=2, height=Dimension(weight=0.5))

    def add_entry(self):
        self.rows.append(Row(len(self.rows)))
        # Focus the most recently added entry
        app = get_app()
        app.layout.focus(self.rows[-1].get_widgets().get_children()[-1])


class Row:
    def __init__(self, index):
        self.label = Label(f"Label {index} here")
        self.text_area = TextArea("Type something here")

    def get_widgets(self):
        return VSplit([self.label, self.text_area], padding=2)


example_app = ExampleApp()
example_app.app.run()
