from functools import partial

from prompt_toolkit.filters import Condition
from prompt_toolkit.formatted_text import Template
from prompt_toolkit.layout.containers import (
    ConditionalContainer,
    Container,
    DynamicContainer,
    HSplit,
    VSplit,
    Window,
)
from prompt_toolkit.widgets import Label


class BlankBorder:
    """
    Draw a blank border around any container, optionally with a title text.

    This is copied from the Frame class, just changing all the chars to be spaces.

    Changing the title and body of the frame is possible at runtime by
    assigning to the `body` and `title` attributes of this class.

    :param body: Another container object.
    :param title: Text to be displayed in the top of the frame (can be formatted text).
    :param style: Style string to be applied to this widget.
    """

    def __init__(
        self,
        body,
        title="",
        style="",
        width=None,
        height=None,
        key_bindings=None,
        modal=False,
    ) -> None:

        self.title = title
        self.body = body

        fill = partial(Window, style="class:frame.border")
        style = "class:frame " + style

        top_row_with_title = VSplit(
            [
                fill(width=1, height=1, char=""),
                fill(char=""),
                fill(width=1, height=1, char="|"),
                # Notice: we use `Template` here, because `self.title` can be an
                # `HTML` object for instance.
                Label(
                    lambda: Template(" {} ").format(self.title),
                    style="class:frame.label",
                    dont_extend_width=True,
                ),
                fill(width=1, height=1, char="|"),
                fill(char=""),
                fill(width=1, height=1, char=""),
            ],
            height=1,
        )

        top_row_without_title = VSplit(
            [
                fill(width=1, height=1, char=""),
                fill(char=""),
                fill(width=1, height=1, char=""),
            ],
            height=1,
        )

        @Condition
        def has_title() -> bool:
            return bool(self.title)

        self.container = HSplit(
            [
                ConditionalContainer(content=top_row_with_title, filter=has_title),
                ConditionalContainer(content=top_row_without_title, filter=~has_title),
                VSplit(
                    [
                        fill(width=1, char=""),
                        DynamicContainer(lambda: self.body),
                        fill(width=1, char=""),
                        # Padding is required to make sure that if the content is
                        # too small, the right frame border is still aligned.
                    ],
                    padding=0,
                ),
                VSplit(
                    [
                        fill(width=1, height=1, char=""),
                        fill(char=""),
                        fill(width=1, height=1, char=""),
                    ],
                    # specifying height here will increase the rendering speed.
                    height=1,
                ),
            ],
            width=width,
            height=height,
            style=style,
            key_bindings=key_bindings,
            modal=modal,
        )

    def __pt_container__(self) -> Container:
        return self.container
