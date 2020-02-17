from qprompt import ask_int, Menu

# Two refinements are necessary: some responses permanently  assigned to a key
# (. for Cancel)
# Inject some responses for unit tests


def create_menu(heading, choices):
    menu = Menu(header=heading)
    for index, choice in enumerate(choices, 1):
        menu.add(str(index), choice)
    menu.add(".", "Cancel")
    choice = menu.show()
    return choice


def get_choice_input(heading, choices):
    map_choice = False
    indexes = []
    while 1:
        input_text = heading + "\n"
        for idx, choice in enumerate(choices, 1):
            if isinstance(choice, list):
                choice_string = choice[0]
                map_choice = True
            else:
                choice_string = choice
            input_text += f"   {str(idx)}) {choice_string}\n"
            indexes.append(idx)

        # choice = input(input_text)
        choice = ask_int(input_text, valid=indexes)

        if not map_choice:
            return choice
        else:
            return choices[choice - 1][1]
