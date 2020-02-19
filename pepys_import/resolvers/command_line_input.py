from qprompt import ask_int, Menu

# Two refinements are necessary: some responses permanently  assigned to a key
# (. for Cancel)
# Inject some responses for unit tests


def create_menu(heading, choices):
    menu = Menu(header=heading, fzf=True)
    for index, choice in enumerate(choices, 1):
        menu.add(str(index), choice)
    menu.add(".", "Cancel")
    choice = menu.show()
    return choice
