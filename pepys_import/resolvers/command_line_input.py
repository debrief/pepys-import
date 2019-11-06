def get_choice_input(heading, choices):
    map_choice = False
    while 1:
        input_text = heading + "\n"
        for idx, choice in enumerate(choices, 1):
            if isinstance(choice, list):
                choice_string = choice[0]
                map_choice = True
            else:
                choice_string = choice
            input_text += "   " + str(idx) + ") " + choice_string + "\n"
        choice = input(input_text)

        try:
            choice_value = int(choice)
        except ValueError:
            print(choice + " wasn't a valid number, please try again")
            continue

        if choice_value < 1 or choice_value > len(choices):
            print(choice + " was not one of the options, please try again")
        else:
            if not map_choice:
                return choice_value
            else:
                return choices[choice_value - 1][1]
