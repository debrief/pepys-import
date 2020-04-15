class SingleUsage:
    """
    Stores information on a single usage of a character.

    Contains two fields: tool_field and message.

    Objects created from this class are stored in the usages list
    on Char objects.
    """

    __slots__ = ("tool_field", "message")

    def __init__(self, tool_field, message):
        self.tool_field = tool_field
        self.message = message
