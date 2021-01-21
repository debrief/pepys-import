from loguru import logger
from prompt_toolkit.application.current import get_app
from prompt_toolkit.buffer import ValidationState
from prompt_toolkit.document import Document
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.layout.containers import HorizontalAlign, VSplit
from prompt_toolkit.validation import ValidationError
from prompt_toolkit.widgets.base import Label

from pepys_admin.maintenance.widgets.custom_text_area import CustomTextArea


class MaskedInputWidget:
    def __init__(self, format_list, overall_validator=None, part_validator=None):
        """Displays a masked text control using the format given in format_list.

        format_list should be a list of strings. Strings starting with ! will be
        displayed as a static label, and all other strings will be displayed as
        initial text in a text box. All content (excluding the ! themselves) will
        be rended in the .text output.

        For example, to get a masked input for entering a date, use something like

        ["yyyy", "!-", "mm", "!-", "dd"]

        The text property will then return something like "2020-01-02"
        """

        self.overall_validator = overall_validator
        self.start_validating = False
        self.buffer_to_max_len = {}

        self.controls = []

        for entry in format_list:
            if entry.startswith("!"):
                # This is an entry containing static text to be displayed
                self.controls.append(Label(entry[1:], width=len(entry[1:])))
            else:
                # This is an entry with placeholder text that can be edited
                text_area = CustomTextArea(
                    entry,
                    width=len(entry),
                    multiline=False,
                    on_cursor_at_end=self.focus_next_field,
                    validator=part_validator,
                    key_bindings=self.get_keybindings(),
                    limit_length=True,
                )
                self.controls.append(text_area)
                # Keep track of the max length of this text area, so we can
                # find it when we look at the current_buffer later
                self.buffer_to_max_len[text_area.buffer] = len(text_area.initial_text)

        self.container = VSplit(self.controls, align=HorizontalAlign.LEFT)

    def focus_next_field(self):
        app = get_app()

        if app.layout.current_window == self.controls[-1].window:
            # Are we in the final control?
            # If so, start validating the overall result
            self.start_validating = True
            self.validate_whole_text()
        else:
            # We're not at the end, so move to the next control
            # if the current field is valid - otherwise stay
            # where we are so we can see the validation error
            if app.layout.current_buffer.validate():
                self.go_to_next_field()

    def get_keybindings(self):
        kb = KeyBindings()

        @kb.add("tab")
        def _(event):
            # Can't use the standard focus_next function as we need our custom logic
            self.go_to_next_field(coming_from="left")

        @kb.add("s-tab")
        def _(event):
            # Can't use the standard focus_previous function as we need our custom logic
            self.go_to_prev_field(coming_from="right")

        @kb.add("right")
        def _(event):
            # Override the default handler for the right arrow key that comes with the Buffer,
            # so we can do our own processing
            app = get_app()
            buff = event.current_buffer

            if (
                buff.cursor_position == len(buff.text) - 1
                and len(buff.text) == self.buffer_to_max_len[buff]
            ):
                # If the cursor is at the end of the buffer, and the buffer is full to it's max len
                if app.layout.current_window != self.controls[-1].window:
                    # If we're not in the final control, then move right
                    self.go_to_next_field(coming_from="left")
            else:
                # Do exactly what the standard right arrow handler does
                buff.cursor_position += buff.document.get_cursor_right_position(count=event.arg)

        @kb.add("left")
        def _(event):
            # Override the default handler for the left arrow key that comes with the Buffer,
            # so we can do our own processing
            app = get_app()
            buff = event.current_buffer

            if buff.cursor_position == 0:
                # If the cursor is at the beginning of the buffer
                if app.layout.current_window != self.controls[0].window:
                    # If we're not in the first control then go to previous control
                    # This stops us looping round and round
                    self.go_to_prev_field(coming_from="right")
            else:
                # Otherwise, do exactly what the standard left arrow handler does
                buff.cursor_position += buff.document.get_cursor_left_position(count=event.arg)

        return kb

    def go_to_next_field(self, coming_from=None):
        logger.debug("go_to_next_field")
        app = get_app()
        if self.start_validating:
            # If we're validating now (because we've already filled it to the end)
            # then validate and display the errors
            self.validate_whole_text()
        # Focus on the next field, using the standard Prompt Toolkit focus_next function
        app.layout.focus_next()

        if coming_from == "left":
            # If we've come from the left-hand side, then set the cursor to the beginning of the field
            logger.debug("Setting cursor position to 0")
            app.layout.current_buffer._set_cursor_position(0)
        elif coming_from == "right":
            # If we've come from the right-hand side, then set the cursor to the end of the field
            app.layout.current_buffer._set_cursor_position(len(app.layout.current_buffer.text) - 1)

    def go_to_prev_field(self, coming_from=None):
        logger.debug("go_to_prev_field")
        app = get_app()
        if self.start_validating:
            # If we're validating now (because we've already filled it to the end)
            # then validate and display the errors
            self.validate_whole_text()
        # Focus on the previous field, using the standard Prompt Toolkit focus_previous function
        app.layout.focus_previous()

        if coming_from == "left":
            # If we've come from the left-hand side, then set the cursor to the beginning of the field
            app.layout.current_buffer._set_cursor_position(0)
        elif coming_from == "right":
            # If we've come from the right-hand side, then set the cursor to the end of the field
            app.layout.current_buffer._set_cursor_position(len(app.layout.current_buffer.text) - 1)

    def validate_whole_text(self):
        # Create a temporary Document instance (as used under the hood in Buffer)
        # so we can run a validator (as the validator needs a Document instance)
        doc = Document(self.text, None)
        try:
            # Do the validation
            self.overall_validator.validate(doc)
        except ValidationError as e:
            # Store the error on each CustomTextArea control
            for control in self.controls:
                if isinstance(control, CustomTextArea):
                    control.buffer.validation_state = ValidationState.INVALID
                    control.buffer.validation_error = e
        else:
            # This else clause runs if the try block succeeded
            # So remove the error from every control
            for control in self.controls:
                if isinstance(control, CustomTextArea):
                    control.buffer.validation_state = ValidationState.VALID
                    control.buffer.validation_error = None

    @property
    def text(self):
        # Join the text of all the controls together
        text = "".join([c.text for c in self.controls])
        return text

    def __pt_container__(self):
        return self.container
