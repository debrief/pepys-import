class Char:
    """
    Object used to store information on a specific character.

    Stores the character letter itself, plus a list of usages of the character.

    A list of these is kept in HighlightedFile.chars (and also available through
    SubToken.chars), and iterating through this list is used to create the final
    highlighted file.
    """

    # For efficiency, define the attributes that are allowed to be used on this
    # object here - so Python uses a list not a dict to store the attributes, and
    # is more efficient
    # (We may potentially have millions of Char objects for a long file)
    __slots__ = ["letter", "usages"]

    def __init__(self, letter):
        self.letter = letter
        self.usages = []

    def __repr__(self):
        return f"Char: {self.letter} with {len(self.usages)} usage(s)"
