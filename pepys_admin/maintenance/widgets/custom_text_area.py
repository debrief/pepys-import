from typing import List, Optional

from loguru import logger
from prompt_toolkit.auto_suggest import AutoSuggest, DynamicAutoSuggest
from prompt_toolkit.buffer import Buffer, BufferAcceptHandler
from prompt_toolkit.completion import Completer, DynamicCompleter
from prompt_toolkit.document import Document
from prompt_toolkit.filters import Condition, FilterOrBool, has_focus, is_done, is_true, to_filter
from prompt_toolkit.formatted_text import AnyFormattedText
from prompt_toolkit.history import History
from prompt_toolkit.layout.containers import Container, Window
from prompt_toolkit.layout.controls import BufferControl, GetLinePrefixCallable
from prompt_toolkit.layout.dimension import AnyDimension
from prompt_toolkit.layout.dimension import Dimension as D
from prompt_toolkit.layout.margins import NumberedMargin, ScrollbarMargin
from prompt_toolkit.layout.processors import (
    AppendAutoSuggestion,
    BeforeInput,
    ConditionalProcessor,
    PasswordProcessor,
    Processor,
)
from prompt_toolkit.lexers import DynamicLexer, Lexer
from prompt_toolkit.validation import DynamicValidator, Validator


class CustomTextArea:
    """
    This is mostly copied from the TextArea class that comes with prompt toolkit,
    but has some extra functionality. The original docstring is at the bottom, after
    we list the new parameters:

    New parameters
    :param on_cursor_at_end: A function to be called when the cursor is detected to be
        at the end of the control
    :param key_bindings: A KeyBindings object giving a  set of custom keybindings to be
        applied to the control
    :param limit_length: A Boolean specifying whether to limit the length of the field to the
        length of the initial text


    A simple input field.

    This is a higher level abstraction on top of several other classes with
    sane defaults.

    This widget does have the most common options, but it does not intend to
    cover every single use case. For more configurations options, you can
    always build a text area manually, using a
    :class:`~prompt_toolkit.buffer.Buffer`,
    :class:`~prompt_toolkit.layout.BufferControl` and
    :class:`~prompt_toolkit.layout.Window`.

    Buffer attributes:

    :param text: The initial text.
    :param multiline: If True, allow multiline input.
    :param completer: :class:`~prompt_toolkit.completion.Completer` instance
        for auto completion.
    :param complete_while_typing: Boolean.
    :param accept_handler: Called when `Enter` is pressed (This should be a
        callable that takes a buffer as input).
    :param history: :class:`~prompt_toolkit.history.History` instance.
    :param auto_suggest: :class:`~prompt_toolkit.auto_suggest.AutoSuggest`
        instance for input suggestions.

    BufferControl attributes:

    :param password: When `True`, display using asterisks.
    :param focusable: When `True`, allow this widget to receive the focus.
    :param focus_on_click: When `True`, focus after mouse click.
    :param input_processors: `None` or a list of
        :class:`~prompt_toolkit.layout.Processor` objects.
    :param validator: `None` or a :class:`~prompt_toolkit.validation.Validator`
        object.

    Window attributes:

    :param lexer: :class:`~prompt_toolkit.lexers.Lexer` instance for syntax
        highlighting.
    :param wrap_lines: When `True`, don't scroll horizontally, but wrap lines.
    :param width: Window width. (:class:`~prompt_toolkit.layout.Dimension` object.)
    :param height: Window height. (:class:`~prompt_toolkit.layout.Dimension` object.)
    :param scrollbar: When `True`, display a scroll bar.
    :param style: A style string.
    :param dont_extend_width: When `True`, don't take up more width then the
                              preferred width reported by the control.
    :param dont_extend_height: When `True`, don't take up more width then the
                               preferred height reported by the control.
    :param get_line_prefix: None or a callable that returns formatted text to
        be inserted before a line. It takes a line number (int) and a
        wrap_count and returns formatted text. This can be used for
        implementation of line continuations, things like Vim "breakindent" and
        so on.

    Other attributes:

    :param search_field: An optional `SearchToolbar` object.
    """

    def __init__(
        self,
        text: str = "",
        multiline: FilterOrBool = True,
        password: FilterOrBool = False,
        lexer: Optional[Lexer] = None,
        auto_suggest: Optional[AutoSuggest] = None,
        completer: Optional[Completer] = None,
        complete_while_typing: FilterOrBool = True,
        validator: Optional[Validator] = None,
        accept_handler: Optional[BufferAcceptHandler] = None,
        history: Optional[History] = None,
        focusable: FilterOrBool = True,
        focus_on_click: FilterOrBool = False,
        wrap_lines: FilterOrBool = True,
        read_only: FilterOrBool = False,
        width: AnyDimension = None,
        height: AnyDimension = None,
        dont_extend_height: FilterOrBool = False,
        dont_extend_width: FilterOrBool = False,
        line_numbers: bool = False,
        get_line_prefix: Optional[GetLinePrefixCallable] = None,
        scrollbar: bool = False,
        style: str = "",
        search_field=None,
        preview_search: FilterOrBool = True,
        prompt: AnyFormattedText = "",
        input_processors: Optional[List[Processor]] = None,
        on_cursor_at_end=None,
        key_bindings=None,
        limit_length=False,
    ) -> None:

        search_control = None

        if input_processors is None:
            input_processors = []

        self.on_cursor_at_end = on_cursor_at_end

        # Writeable attributes.
        self.completer = completer
        self.complete_while_typing = complete_while_typing
        self.lexer = lexer
        self.auto_suggest = auto_suggest
        self.read_only = read_only
        self.wrap_lines = wrap_lines
        self.validator = validator

        # Keep track of whether we're limiting the length or not
        self.limit_length = limit_length

        # Keep track of the initial placeholder text
        self.initial_text = text

        self.buffer = Buffer(
            document=Document(text, 0),
            multiline=multiline,
            read_only=Condition(lambda: is_true(self.read_only)),
            completer=DynamicCompleter(lambda: self.completer),
            complete_while_typing=Condition(lambda: is_true(self.complete_while_typing)),
            validate_while_typing=True,
            validator=DynamicValidator(lambda: self.validator),
            auto_suggest=DynamicAutoSuggest(lambda: self.auto_suggest),
            accept_handler=accept_handler,
            history=history,
            on_text_changed=self.on_text_changed,  # Added handler
        )

        self.control = BufferControl(
            buffer=self.buffer,
            lexer=DynamicLexer(lambda: self.lexer),
            input_processors=[
                ConditionalProcessor(AppendAutoSuggestion(), has_focus(self.buffer) & ~is_done),
                ConditionalProcessor(processor=PasswordProcessor(), filter=to_filter(password)),
                BeforeInput(prompt, style="class:text-area.prompt"),
            ]
            + input_processors,
            search_buffer_control=search_control,
            preview_search=preview_search,
            focusable=focusable,
            focus_on_click=focus_on_click,
            key_bindings=key_bindings,  # Pass over the new keybindings
        )

        if multiline:
            if scrollbar:
                right_margins = [ScrollbarMargin(display_arrows=True)]
            else:
                right_margins = []
            if line_numbers:
                left_margins = [NumberedMargin()]
            else:
                left_margins = []
        else:
            height = D.exact(1)
            left_margins = []
            right_margins = []

        style = "class:text-area " + style

        self.window = Window(
            height=height,
            width=width,
            dont_extend_height=dont_extend_height,
            dont_extend_width=dont_extend_width,
            content=self.control,
            style=style,
            wrap_lines=Condition(lambda: is_true(self.wrap_lines)),
            left_margins=left_margins,
            right_margins=right_margins,
            get_line_prefix=get_line_prefix,
        )

    def on_text_changed(self, event):
        if self.text[1:] == self.initial_text:
            # We've typed a character into the box that contained the placeholder
            # so remove the placeholder and just put in the new character
            self.text = self.text[0]
            logger.debug("Setting cursor position to 1")
            self.buffer._set_cursor_position(1)

        if self.limit_length:
            if len(self.text) > len(self.initial_text):
                # If we're limiting the length, and we're currently over the maximum length
                logger.debug(f"At start: {self.buffer.cursor_position=}")
                index = self.buffer.cursor_position - 1
                # We use the character before the current cursor_position to tell us
                # what character we just entered, as we want that character to replace
                # the next character.
                # This is, if the text was: abcd
                # and we added the capital E here: abEcd
                # we would want the result to be: abEd
                # (that is, the E overwrites the next character)
                # So, we split the text into the bits before/after the new character
                first_part = self.text[: index + 1]
                second_part = self.text[index + 2 :]

                if second_part == "" and len(first_part) > len(self.initial_text):
                    # If the second part is empty and the first part is too long then we
                    # added something at the end, and we want to just take the first part
                    # excluding the final character
                    self.text = first_part[:-1]
                else:
                    # Otherwise combine the two parts (which misses out the character that was
                    # between them)
                    self.text = first_part + second_part
                logger.debug(f"Setting {self.text=}")

                # Set a new cursor position (as it gets reset to 0 when self.text is set)
                # We want to go to index + 1 (ie. the next position), but we mustn't go over
                # the length of the text + 1
                new_cursor_pos = min(index + 1, len(self.initial_text) + 1)
                logger.debug(f"Setting cursor position to {new_cursor_pos}")
                self.buffer._set_cursor_position(new_cursor_pos)

        self.process_cursor_at_end()

    def process_cursor_at_end(self):
        if self.on_cursor_at_end is not None:
            # If we've got an event handler to call
            if self.text != self.initial_text and len(self.text) == len(self.initial_text):
                # If the text isn't the placeholder text, but it's the full length of the field
                # then get the index of the character we entered
                index = self.buffer.cursor_position - 1
                if index == len(self.initial_text) - 1:
                    # Move the cursor to the final position in the box
                    logger.debug(f"Setting cursor position to {len(self.text) - 1}")
                    self.buffer._set_cursor_position(len(self.text) - 1)
                    # Call the event handler function
                    logger.debug("Calling on cursor at end")
                    self.on_cursor_at_end()

    @property
    def text(self) -> str:
        """
        The `Buffer` text.
        """
        return self.buffer.text

    @text.setter
    def text(self, value: str) -> None:
        self.document = Document(value, 0)

    @property
    def document(self) -> Document:
        """
        The `Buffer` document (text + cursor position).
        """
        return self.buffer.document

    @document.setter
    def document(self, value: Document) -> None:
        self.buffer.set_document(value, bypass_readonly=True)

    @property
    def accept_handler(self) -> Optional[BufferAcceptHandler]:
        """
        The accept handler. Called when the user accepts the input.
        """
        return self.buffer.accept_handler

    @accept_handler.setter
    def accept_handler(self, value: BufferAcceptHandler) -> None:
        self.buffer.accept_handler = value

    def __pt_container__(self) -> Container:
        return self.window
