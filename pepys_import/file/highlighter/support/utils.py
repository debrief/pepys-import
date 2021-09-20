def merge_adjacent_text_locations(text_locations):
    current_low = text_locations[0][0]
    current_high = text_locations[0][1]
    output = []

    for low, high in text_locations[1:]:
        if low <= current_high + 1:
            current_high = high
        else:
            output.append((current_low, current_high))
            current_low = low
            current_high = high
    output.append((current_low, current_high))

    return output
