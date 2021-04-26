from copy import copy, deepcopy

from loguru import logger
from prompt_toolkit.application.current import get_app
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
    def __init__(
        self,
        root_element,
        on_add=None,
        on_select=None,
        hide_root=False,
        height=None,
        width=None,
        max_levels=None,
        level_to_name=None,
    ):
        """TreeView widget, shows a view of TreeElement objects with expanding/collapsing entries.

        :param root_element: Root TreeElement
        :type root_element: TreeElement
        :param on_add: Function to call when add button is pressed, defaults to None
        :type on_add: function, optional
        :param on_select: Function to call when an entry is selected, defaults to None
        :type on_select: function, optional
        :param hide_root: If True, hide the root element and show the root element's children as top-level elements, defaults to False
        :type hide_root: bool, optional
        :param height: Height of TreeView, defaults to None
        :type height: int, optional
        :param width: Width of TreeView, defaults to None
        :type width: int, optional
        :param max_levels: Maximum number of levels the TreeView can have, defaults to None. Setting this will stop the 'Add' button
        appearing on the leaf nodes.
        :type max_levels: int, optional
        :param level_to_name: Dictionary mapping each level of the TreeView (0, 1, 2 etc) to a name, so appropriate names can
        be used in the 'Add XXX' button, defaults to None
        :type level_to_name: dict, optional
        """
        self.root_element = root_element
        self.filtered_root_element = self.root_element
        self.text_list = []
        self.object_list = []
        self.add_enabled = False
        self.on_add = on_add
        self.on_select = on_select
        self.hide_root = hide_root
        self.width = width
        self.height = height
        self.filter_text = ""
        self.level_to_name = level_to_name

        if max_levels is None:
            self.max_levels = 9999
        else:
            self.max_levels = max_levels

        if self.hide_root:
            self.max_levels -= 1

        self.initialise_selected_element()

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

    def set_root(self, new_root):
        """Set a new root TreeElement

        :param new_root: New root element
        :type new_root: TreeElement
        """
        self.root_element = new_root
        self.filtered_root_element = self.root_entry
        self.initialise_selected_element()

    def initialise_selected_element(self):
        if self.hide_root:
            try:
                self.selected_element = self.root_element.children[0]
            except IndexError:
                self.selected_element = None
        else:
            self.selected_element = self.root_element
        self.selected_element_index = 0

    def handle_click_on_item(self, mouse_event):
        if mouse_event.event_type == MouseEventType.MOUSE_UP:
            get_app().layout.focus(self)
            self.selected_element_index = mouse_event.position.y
            self.selected_element = self.object_list[self.selected_element_index]
            if callable(self.on_select):
                self.on_select(self.selected_element)

    def handle_click_on_plus_minus(self, mouse_event):
        if mouse_event.event_type == MouseEventType.MOUSE_UP:
            get_app().layout.focus(self)
            self.selected_element_index = mouse_event.position.y
            self.selected_element = self.object_list[self.selected_element_index]
            if callable(self.on_select):
                self.on_select(self.selected_element)
            self.do_expand_collapse()

    def handle_expand_collapse_or_add(self):
        if self.add_enabled:
            self.do_add()
        else:
            self.do_expand_collapse()

    def do_expand_collapse(self):
        self.selected_element.expanded = not self.selected_element.expanded

    def do_add(self):
        if callable(self.on_add):
            self.on_add(self.selected_element)
            self.selected_element.expanded = True

    def handle_click_on_add(self, mouse_event):
        if mouse_event.event_type == MouseEventType.MOUSE_UP:
            get_app().layout.focus(self)
            self.selected_element_index = mouse_event.position.y
            self.selected_element = self.object_list[self.selected_element_index]
            self.do_add()

    def format_element(self, element, indentation, root_entry):
        """Format an element for display in the TreeView

        :param element: Element to format
        :type element: TreeElement
        :param indentation: Indentation required for this level
        :type indentation: str
        :param root_entry: True if this is the root entry, False otherwise
        :type root_entry: bool
        :return: Formatted text ready for display
        :rtype: list
        """
        n_children = len(element.children)

        if self.selected_element == element:
            row_style = "class:tree-selected-element"
        else:
            row_style = ""

        row_style += f" class:tree-level-{element.level}"

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
            for _ in range(indentation - 1, 0, -1):
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
            element_output.append([(row_style, "[", self.handle_click_on_plus_minus)])

        if self.selected_element == element and not self.add_enabled and n_children > 0:
            element_output.append([("[SetCursorPosition]", "")])

        if n_children == 0:
            element_output.append([("class:lines", HORIZONTAL_LINE)])
        else:
            if element.expanded:
                element_output.append([(row_style, "-", self.handle_click_on_plus_minus)])
            else:
                element_output.append([(row_style, "+", self.handle_click_on_plus_minus)])

        if n_children == 0:
            element_output.append([("class:lines", HORIZONTAL_LINE)])
        else:
            element_output.append([(row_style, "]", self.handle_click_on_plus_minus)])

        if self.selected_element == element and not self.add_enabled and n_children == 0:
            element_output.append([("[SetCursorPosition]", "")])

        if self.filter_text != "" and self.filter_text.lower() in element.text.lower():
            index = element.text.lower().index(self.filter_text.lower())
            element_output.append([(row_style, " " + element.text[:index])])
            element_output.append(
                [
                    (
                        row_style + " class:tree-matched-filter",
                        element.text[index : index + len(self.filter_text)],
                    )
                ]
            )
            element_output.append([(row_style, element.text[index + len(self.filter_text) :])])
        else:
            element_output.append([(row_style, " " + element.text)])

        # Only show the Add button if we're on the selected element, and we're not at the maximum level
        if self.selected_element == element and self.selected_element.level <= self.max_levels:
            element_output.append([("", "   ")])
            if self.add_enabled:
                element_output.append([("[SetCursorPosition]", "")])
            if self.level_to_name is not None:
                try:
                    add_text = f"<Add {self.level_to_name[element.level]}>"
                except KeyError:
                    add_text = "<Add>"
            else:
                add_text = "<Add>"
            element_output.append([(add_style, add_text, self.handle_click_on_add)])

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

    def filter(self, filter_text):
        """Filter the TreeView entries, showing thise that match the filter_text
        (and their parents and children)

        :param filter_text: Filter text
        :type filter_text: str
        """
        self.filter_text = filter_text
        if self.filter_text == "":
            self.filtered_root_element = self.root_element
            return

        self.filtered_root_element = deepcopy(self.root_element)

        self.remove_nonmatching_elements(self.filter_text, self.filtered_root_element)

        get_app().invalidate()

    def remove_nonmatching_elements(self, filter_text, root_element):
        """Remove elements that don't match the filter_text, and expand other elements
        as required to ensure that the matched entries are visible.

        :param filter_text: Filter text
        :type filter_text: str
        :param root_element: Root TreeElement
        :type root_element: TreeElement
        """
        if filter_text.lower() not in root_element.text.lower():
            children = copy(root_element.children)
            for child in children:
                self.remove_nonmatching_elements(filter_text, child)

            if len(root_element.children) == 0:
                if root_element.parent is not None:
                    root_element.parent.remove_child(root_element)
            else:
                if root_element.parent is not None:
                    root_element.parent.expanded = True
        else:
            if root_element.parent is not None:
                root_element.parent.expanded = True
                root_element.expanded = True

    def walk_tree(self, root):
        """Walk the tree, formatting each element as we go

        :param root: Root TreeElement
        :type root: TreeElement
        :return: Tuple containing the list of FormattedText entries, plus the list of objects from the TreeElements
        :rtype: tuple
        """
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

    def select_element(self, element):
        """Select the given element

        :param element: Element to select
        :type element: TreeElement
        """
        self.filtered_root_element = self.root_element

        # Expand all parents of the element to select, so we can see it
        current_element = element
        while current_element.parent is not None:
            current_element.parent.expanded = True
            current_element = current_element.parent

        self.text_list, self.object_list = self.walk_tree(self.filtered_root_element)

        if self.hide_root and element == self.filtered_root_element:
            # If we've got a hidden root then we can't select the root element
            # so select the first child of the root element
            try:
                element = self.root_element.children[0]
            except Exception:
                self.selected_element = None
                self.selected_element_index = 0
                return
        index = self.object_list.index(element)
        self.selected_element = self.object_list[index]
        self.selected_element_index = index

        if callable(self.on_select):
            self.on_select(self.selected_element)

    def _get_formatted_text(self):
        self.text_list, self.object_list = self.walk_tree(self.filtered_root_element)

        merged_text = merge_formatted_text(self.text_list)()

        return merged_text

    def _get_key_bindings(self):
        kb = KeyBindings()

        @kb.add("up")
        def _go_up(event) -> None:
            self.selected_element_index = (self.selected_element_index - 1) % len(self.object_list)
            self.selected_element = self.object_list[self.selected_element_index]
            self.add_enabled = False
            if callable(self.on_select):
                self.on_select(self.selected_element)

        @kb.add("down")
        def _go_down(event) -> None:
            self.selected_element_index = (self.selected_element_index + 1) % len(self.object_list)
            self.selected_element = self.object_list[self.selected_element_index]
            self.add_enabled = False
            if callable(self.on_select):
                self.on_select(self.selected_element)

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
        """Represents an element in a Tree

        :param text: Text to display in the TreeView
        :type text: str
        :param object: Object associated with this element, defaults to None
        :type object: obj, optional
        """
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

    def sort_children_by_start_time(self):
        self.children = sorted(self.children, key=lambda x: x.object.start)

    @property
    def is_final_child(self):
        """Returns True if this is the final child entry of its parent."""
        try:
            result = self.parent.children.index(self) == len(self.parent.children) - 1
            return result
        except AttributeError:
            return False

    @property
    def level(self):
        """Returns the level of this entry in the tree.

        0 is the root element, 1 is a child of the root element, etc.
        """
        level = 0
        current_element = self
        while current_element.parent is not None:
            current_element = current_element.parent
            level += 1

        return level
