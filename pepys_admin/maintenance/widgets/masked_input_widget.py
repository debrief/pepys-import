from loguru import logger
from prompt_toolkit.application.current import get_app
from prompt_toolkit.buffer import ValidationState
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.layout.containers import HorizontalAlign, VSplit
from prompt_toolkit.validation import ValidationError
from prompt_toolkit.widgets.base import Label

from pepys_admin.maintenance.widgets.custom_text_area import CustomTextArea


class FakeDocument:
    def __init__(self, text):
        self.text = text


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

        self.controls = []

        for entry in format_list:
            if entry.startswith("!"):
                self.controls.append(Label(entry[1:], width=len(entry[1:])))
            else:
                self.controls.append(
                    CustomTextArea(
                        entry,
                        width=len(entry),
                        multiline=False,
                        on_cursor_at_end=self.focus_next_field,
                        validator=part_validator,
                        key_bindings=self.get_keybindings(),
                    )
                )

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

        # Make space, enter or down-arrow open the dropdown
        @kb.add(" ")
        @kb.add("enter")
        @kb.add("down")
        def _(event) -> None:
            if self.handler is not None:
                self.handler()

        @kb.add("tab")
        def _(event):
            self.go_to_next_field()

        @kb.add("s-tab")
        def _(event):
            self.go_to_prev_field()

        return kb

    def go_to_next_field(self):
        app = get_app()
        if self.start_validating:
            self.validate_whole_text()
        app.layout.focus_next()

    def go_to_prev_field(self):
        app = get_app()
        if self.start_validating:
            self.validate_whole_text()
        app.layout.focus_previous()

    def validate_whole_text(self):
        logger.debug(f"Validating with text = {self.text}")
        doc = FakeDocument(self.text)
        try:
            self.overall_validator.validate(doc)
        except ValidationError as e:
            for control in self.controls:
                if isinstance(control, CustomTextArea):
                    control.buffer.validation_state = ValidationState.INVALID
                    control.buffer.validation_error = e
        else:
            for control in self.controls:
                if isinstance(control, CustomTextArea):
                    control.buffer.validation_state = ValidationState.VALID
                    control.buffer.validation_error = None

    @property
    def text(self):
        text = "".join([c.text for c in self.controls])
        return text

    def __pt_container__(self):
        return self.container
