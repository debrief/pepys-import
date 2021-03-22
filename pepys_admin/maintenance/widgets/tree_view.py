from loguru import logger
from prompt_toolkit.formatted_text.base import merge_formatted_text
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.margins import ScrollbarMargin
from prompt_toolkit.mouse_events import MouseEventType

logger.remove()
logger.add("gui.log")

HORIZONTAL_LINE = "\u2500"
VERTICAL_AND_HORIZONTAL = "\u251c"
L_SHAPE = "\u2514"
VERTICAL_LINE = "\u2502"


class TreeView:
    def __init__(self, root_element, on_add=None, hide_root=False, height=None, width=None):
        self.root_element = root_element
        self.text_list = []
        self.object_list = []
        if hide_root:
            self.selected_element = root_element.children[0]
        else:
            self.selected_element = root_element
        self.selected_element_index = 0
        self.add_enabled = False
        self.on_add = on_add
        self.hide_root = hide_root
        self.width = width
        self.height = height

        self.container = Window(
            content=FormattedTextControl(
                text=self._get_formatted_text,
                focusable=True,
                key_bindings=self._get_key_bindings(),
            ),
            height=self.height,
            width=self.width,
            right_margins=[
                ScrollbarMargin(display_arrows=True),
            ],
        )

    def handle_click_on_item(self, mouse_event):
        if mouse_event.event_type == MouseEventType.MOUSE_UP:
            self.selected_element_index = mouse_event.position.y
            self.selected_element = self.object_list[self.selected_element_index]
            self.handle_expand_collapse_or_add()

    def handle_expand_collapse_or_add(self):
        if self.add_enabled:
            if callable(self.on_add):
                self.on_add(self.selected_element)
                self.selected_element.expanded = True
        else:
            self.selected_element.expanded = not self.selected_element.expanded

    def handle_click_on_add(self, mouse_event):
        if mouse_event.event_type == MouseEventType.MOUSE_UP:
            self.add_enabled = True
            self.selected_element_index = mouse_event.position.y
            self.selected_element = self.object_list[self.selected_element_index]
            self.handle_expand_collapse_or_add()
            self.add_enabled = False

    def format_element(self, element, indentation, root_entry):
        n_children = len(element.children)

        if self.selected_element == element:
            row_style = "class:selected-element"
        else:
            row_style = ""

        if self.add_enabled:
            add_style = "class:add-button-focused"
        else:
            add_style = "class:add-button"

        if root_entry:
            element_output = [[("", "")]]
        else:
            element_output = [[("", "\n")]]

        if indentation == 0:
            element_output.append([("", "")])
        else:
            indent_str = ""
            parent = element.parent
            for i in range(indentation - 1, 0, -1):
                if not parent.is_final_child:
                    indent_str += VERTICAL_LINE + " "
                else:
                    indent_str += "  "
                parent = parent.parent
            indent_str = indent_str[::-1]
            if element.is_final_child:
                indent_str += " " + L_SHAPE
            else:
                indent_str += " " + VERTICAL_AND_HORIZONTAL
            element_output.append([("class:lines", indent_str)])

        if n_children == 0:
            element_output.append([("class:lines", HORIZONTAL_LINE)])
        else:
            element_output.append([(row_style, "[")])

        if self.selected_element == element and not self.add_enabled and n_children > 0:
            element_output.append([("[SetCursorPosition]", "")])

        if n_children == 0:
            element_output.append([("class:lines", HORIZONTAL_LINE)])
        else:
            if element.expanded:
                element_output.append([(row_style, "-")])
            else:
                element_output.append([(row_style, "+")])

        if n_children == 0:
            element_output.append([("class:lines", HORIZONTAL_LINE)])
        else:
            element_output.append([(row_style, "]")])

        if self.selected_element == element and not self.add_enabled and n_children == 0:
            element_output.append([("[SetCursorPosition]", "")])

        element_output.append([(row_style, " " + element.text)])

        if self.selected_element == element:
            element_output.append([("", "   ")])
            if self.add_enabled:
                element_output.append([("[SetCursorPosition]", "")])
            element_output.append([(add_style, "Add", self.handle_click_on_add)])

        merged_text = merge_formatted_text(element_output)()

        # Add the main mouse handler (expand/collapse) to all text, except if the text
        # already has a mouse handler defined, in which case keep that one
        with_mouse_handlers = []
        for entry in merged_text:
            if len(entry) == 3:
                with_mouse_handlers.append(entry)
            else:
                with_mouse_handlers.append((entry[0], entry[1], self.handle_click_on_item))

        return with_mouse_handlers

    def walk_tree(self, root):
        text_output_list = []
        object_output_list = []

        def walk_tree_recursive(root, text_output_list, object_output_list, indentation):
            root_entry = len(text_output_list) == 0
            if self.hide_root and root.parent is None:
                # No parent, so must be root node
                # Don't display anything for this node, and reset indentation
                indentation -= 1
            else:
                merged_element_output = self.format_element(root, indentation, root_entry)

                text_output_list.append(merged_element_output)
                object_output_list.append(root)

            if root.expanded or (self.hide_root and root.parent is None):
                for child in root.children:
                    walk_tree_recursive(
                        child, text_output_list, object_output_list, indentation + 1
                    )

        walk_tree_recursive(root, text_output_list, object_output_list, indentation=0)

        return text_output_list, object_output_list

    def _get_formatted_text(self):
        logger.debug("Ran _get_formatted_text")
        self.text_list, self.object_list = self.walk_tree(self.root_element)

        merged_text = merge_formatted_text(self.text_list)()

        return merged_text

    def _get_key_bindings(self):
        kb = KeyBindings()

        @kb.add("up")
        def _go_up(event) -> None:
            self.selected_element_index = (self.selected_element_index - 1) % len(self.object_list)
            self.selected_element = self.object_list[self.selected_element_index]
            self.add_enabled = False

        @kb.add("down")
        def _go_down(event) -> None:
            self.selected_element_index = (self.selected_element_index + 1) % len(self.object_list)
            self.selected_element = self.object_list[self.selected_element_index]
            self.add_enabled = False

        @kb.add("enter")
        def _enter(event) -> None:
            self.handle_expand_collapse_or_add()

        @kb.add("right")
        def _go_right(event) -> None:
            self.add_enabled = True

        @kb.add("left")
        def _go_left(event) -> None:
            self.add_enabled = False

        return kb

    def __pt_container__(self):
        return self.container


class TreeElement:
    def __init__(self, text, object=None):
        self.text = text
        self.object = object
        self.expanded = False
        self.parent = None
        self.children = []

    def __repr__(self):
        return f"TreeElement(text={self.text})"

    def add_child(self, child):
        child.parent = self
        self.children.append(child)
        return child

    def remove_child(self, child):
        if child in self.children:
            self.children.remove(child)

    @property
    def is_final_child(self):
        try:
            logger.debug(f"{self.parent.children=}")
            logger.debug(f"{self=}")
            result = self.parent.children.index(self) == len(self.parent.children) - 1
            logger.debug(f"{result=}")
            return result
        except AttributeError:
            return False
