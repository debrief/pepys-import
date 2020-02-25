from prompt_toolkit import prompt


def create_menu(title, choices, completer=None):
    """
    A basic function which creates a menu with title and choices.

    :param title: Heading text
    :type title: String
    :param choices: Options to choose
    :type choices: List of strings
    :param completer: Optional argument that shows possible options while typing.
    :type completer: :class:`prompt_toolkit.completion.FuzzyWordCompleter`
    :return: Entered choice
    :rtype: String
    """
    input_text = title + "\n"
    for index, choice in enumerate(choices, 1):
        input_text += f"   {str(index)}) {choice}\n"
    input_text += f"   .) Cancel import\n > "
    choice = prompt(input_text, completer=completer)

    return choice
