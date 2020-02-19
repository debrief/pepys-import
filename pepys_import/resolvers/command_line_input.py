from prompt_toolkit import prompt


def create_menu(heading, choices):
    input_text = heading + "\n"
    for index, choice in enumerate(choices, 1):
        input_text += f"   {str(index)}) {choice}\n"
    input_text += f"   .) Cancel import\n > "
    choice = prompt(input_text)

    return choice
