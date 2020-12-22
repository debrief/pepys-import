from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.layout import BufferControl, HSplit
from prompt_toolkit.layout.containers import DynamicContainer, VSplit, Window
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.widgets import Box, Button, Frame, Label, RadioList, Shadow, TextArea


class MainApplication:
    def __init__(self):
        self.right_buffer = Buffer()

        self.current_layout = 1

        self.layout_1 = self.wizard_body_layout(
            "Wizard - Page 1",
            HSplit(
                [
                    Label(text="Enter something here"),
                    TextArea(multiline=False, accept_handler=self.text_handler),
                ],
                padding=1,
            ),
        )

        entries = [
            ("platform", "Platform"),
            ("sensor", "Sensor"),
            ("platformtype", "Platform Type"),
            ("sensortype", "Sensor Type"),
            ("nationality", "Nationality"),
            ("datafile", "Datafile"),
            ("privacy", "Privacy"),
        ]
        self.cblist = RadioList(entries)
        self.layout_2 = self.wizard_body_layout(
            "Wizard - Page 2",
            HSplit(
                [
                    Label(
                        text="This page allows you to select the table that you want to query.\nMore information here, blah rgg wewtw wgwg"
                    ),
                    self.cblist,
                    VSplit([Button("Save", self.save_handler)]),
                ],
                width=96,
                padding=1,
            ),
        )

        self.root_container = VSplit(
            [
                # One window that holds the BufferControl with the default buffer on
                # the left.
                DynamicContainer(self.get_layout),
                # A vertical line in the middle. We explicitly specify the width, to
                # make sure that the layout engine will not try to divide the whole
                # width by three for all these windows. The window will simply fill its
                # content by repeating this character.
                Window(width=1, char="|"),
                # Display the text 'Hello world' on the right.
                Window(content=BufferControl(self.right_buffer)),
            ]
        )

        layout = Layout(self.root_container)

        self.app = Application(
            layout=layout, key_bindings=self.get_keybindings(), full_screen=True, mouse_support=True
        )

    def get_layout(self):
        if self.current_layout == 1:
            return self.layout_1
        else:
            return self.layout_2

    def save_handler(self):
        self.right_buffer.text += "\n" + repr(self.cblist.current_value)

    def text_handler(self, event):
        self.right_buffer.text += "\n" + event.text

    def button_1_handler(self):
        self.current_layout = 2

    def prev_button_handler(self):
        self.current_layout = self.current_layout - 1
        self.app.layout.focus(self.root_container.children[0])

    def next_button_handler(self):
        self.current_layout = self.current_layout + 1
        self.app.layout.focus(self.root_container.children[0])

    def get_keybindings(self):
        kb = KeyBindings()

        @kb.add("c-q")
        def _(event):
            print("exiting")
            event.app.exit()

        kb.add("tab")(focus_next)
        kb.add("s-tab")(focus_previous)
        kb.add("up")(focus_previous)
        kb.add("down")(focus_next)
        kb.add("left")(focus_previous)
        kb.add("right")(focus_next)

        return kb

    def wizard_body_layout(self, title, body):
        main_body = HSplit(
            [
                # Add optional padding around the body.
                Box(
                    body=body,
                    padding=1,
                    padding_bottom=0,
                ),
                # The buttons.
                Box(
                    body=VSplit(
                        [
                            Button("Prev", handler=self.prev_button_handler),
                            Button("Next", handler=self.next_button_handler),
                        ],
                        padding=1,
                    ),
                    height=3,
                ),
            ]
        )

        whole_layout = Shadow(
            body=Frame(
                title=title,
                body=main_body,
                style="class:dialog.body",
                width=100,
                modal=True,
            )
        )

        return whole_layout


mainapp = MainApplication()
mainapp.app.run()
