from re import finditer
from .token import Token, SubToken
from .usages import SingleUsage


class Line:
    """
    Object representing a line from a HighlightedDatafile.

    Has methods to get a list of Tokens in the line, and to record a usage of the whole line.
    """

    WHITESPACE_DELIM = "\\S+"
    CSV_DELIM = (
        r'(?:,"|^")(""|[\w\W]*?)(?=",|"$)|(?:,(?!")|^(?!"))([^,]*?)(?=$|,)|(\r\n|\n)'
    )

    def __init__(self, list_of_subtokens, hf_instance):
        """
        Create a new line, giving it a list of SubToken objects as children of the line

        Usually this will be just a list of one item, but has the flexibility to have more
        for composite tokens.
        """
        self.children = list_of_subtokens
        self.highlighted_file = hf_instance

    def __repr__(self):
        res = "Line: "
        for child in self.children:
            res += (
                "("
                + str(child.line_start)
                + "+"
                + repr(child.span)
                + ", "
                + child.text
                + ")"
            )
        return res

    @property
    def text(self):
        res = ""
        for child in self.children:
            res += child.text
        return res

    def tokens(self, reg_exp=WHITESPACE_DELIM, strip_char=""):
        """
        Returns a list of Token objects for each token in the line.
        
        Tokens are generated by splitting by the given regular expression, using it as the delimiter.
        The strip_char argument is any characters to remove after splitting - so we don't get the
        delimiters themselves in the returned values. Whitespace is also stripped.
        """
        self.tokens_array = []

        for child in self.children:
            for match in finditer(reg_exp, child.text):
                token_str = match.group()
                # special handling, we may need to strip a leading delimiter
                if strip_char != "":
                    char_index = token_str.find(strip_char)
                    if char_index == 0:
                        token_str = token_str[1:]
                        # and ditch any new whitespace
                    token_str = token_str.strip()

                subtoken = SubToken(
                    match.span(), token_str, int(child.line_start), child.chars
                )

                # the token object expects an array of SubTokens, as it could be
                # a composite object
                list_of_subtokens = [subtoken]

                self.tokens_array.append(
                    Token(list_of_subtokens, self.highlighted_file)
                )

        return self.tokens_array

    def record(self, tool, message):
        """
        Record a usage of the whole line, by adding a SingleUsage object to each of the
        relevant characters in the char array referenced by each SubToken child.
        """
        self.highlighted_file.fill_char_array_if_needed()

        for child in self.children:
            for i in range(int(child.start()), int(child.end())):
                usage = SingleUsage(tool, message)
                child.chars[i].usages.append(usage)
