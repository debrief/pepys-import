from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.layout import BufferControl, HSplit
from prompt_toolkit.layout.containers import VSplit, Window
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.widgets import Box, Button, Frame, Label, TextArea


class MainMenu:
    def __init__(self):
        self.log_output = Buffer()
        start_context = Context(self, self.log_output)
        self.root_container = VSplit(
            [
                start_context.layout(),
                Window(width=1, char="|"),
                Window(BufferControl(buffer=self.log_output)),
            ]
        )

        self.app = Application(
            Layout(self.root_container),
            full_screen=True,
            key_bindings=self.get_bindings(),
        )
        self.app.layout.focus(self.root_container.children[0])

    def change_context(self):
        other = OtherContext(self, self.log_output)
        self.root_container.children[0] = other.layout()
        self.app.layout.focus(self.root_container.children[0])

    def get_bindings(self):
        kb = KeyBindings()

        @kb.add("c-q")
        def _(event):
            print("exiting")
            event.app.exit()

        @kb.add("c-c")
        def _(event):
            self.change_context()

        return kb


class Context:
    def __init__(self, mainmenu, logbuffer):
        self.mainmenu = mainmenu
        self._buttons = HSplit(
            [Button("command_1", handler=self.command_1)],
            key_bindings=self.get_key_bindings(),
        )

        self.logbuffer = logbuffer

    @property
    def buttons(self):
        return self._buttons

    def layout(self):
        # return HSplit(
        #     [Label("Introductory text here"), Button("command_1", handler=self.command_1)],
        #     key_bindings=self.get_key_bindings(),
        # )

        # All the widgets for the UI.
        button1 = Button("Button 1", handler=self.command_1)
        button2 = Button("Button 2", handler=lambda: None)
        button3 = Button("Button 3", handler=lambda: None)
        button4 = Button("Exit", handler=lambda: None)
        text_area = TextArea(focusable=True)

        # Combine all the widgets in a UI.
        # The `Box` object ensures that padding will be inserted around the containing
        # widget. It adapts automatically, unless an explicit `padding` amount is given.
        wizard_container = Box(
            HSplit(
                [
                    Label(text="Press `Tab` to move the focus."),
                    VSplit(
                        [
                            Box(
                                body=HSplit([button1, button2, button3, button4], padding=1),
                                padding=1,
                                style="class:left-pane",
                            ),
                            Box(body=Frame(text_area), padding=1, style="class:right-pane"),
                        ]
                    ),
                ]
            ),
        )

        return wizard_container

    def get_key_bindings(self):
        kb = KeyBindings()

        @kb.add("c-s")
        def _(event):
            self.command_1()

        kb.add("tab")(focus_next)
        kb.add("s-tab")(focus_previous)
        kb.add("up")(focus_previous)
        kb.add("down")(focus_next)

        return kb

    def command_1(self):
        self.logbuffer.text = self.logbuffer.text + "\ncommand_1"
        self.mainmenu.change_context()


class OtherContext:
    def __init__(self, mainmenu, logbuffer):
        self.mainmenu = mainmenu
        self._buttons = HSplit(
            [Button("command_2", handler=self.command_2)],
            key_bindings=self.get_key_bindings(),
        )

        self.logbuffer = logbuffer

    @property
    def buttons(self):
        return self._buttons

    def layout(self):
        return HSplit(
            [Label("Introductory text here"), Button("command_1", handler=self.command_2)],
            key_bindings=self.get_key_bindings(),
        )

    def get_key_bindings(self):
        kb = KeyBindings()

        @kb.add("c-o")
        def _(event):
            print("other")
            self.command_2()

        return kb

    def command_2(self):
        self.logbuffer.text = self.logbuffer.text + "\ncommand_2"


def main():
    main_menu = MainMenu()
    main_menu.app.run()


if __name__ == "__main__":
    main()
