from string import ascii_lowercase, ascii_uppercase


def process(text):
    al = ascii_lowercase
    au = ascii_uppercase
    new = ""
    for i in text:
        if str.islower(i):
            new += al[(al.find(i) + 13) % len(al)]
        elif str.isupper(i):
            new += au[(au.find(i) + 13) % len(au)]
        else:
            new += i
    return new
