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

    return Token(res)
