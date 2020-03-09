from .token import Token


def combine_tokens(*tokens):
    """
    Combine multiple tokens into one new Token, so that one single usage can be given
    for these tokens.
    """
    res = []
    for token in tokens:
        children = token.children
        res.extend(children)

    # Create a token with the combined list of tokens, using the highlighted file instance
    # of the first token (we assume all come from the same file)
    return Token(res, tokens[0].highlighted_file)
