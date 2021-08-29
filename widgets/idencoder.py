def random_alphabet(base: str = "bcdfghjkmnpqrstvwxz"):
    from random import shuffle
    letters = list(base)
    shuffle(letters)
    return "".join(letters)


def twiddle(number: int):
    low = number & 0x000FFF
    mid = number & 0xFFF000
    high = number ^ (low | mid)
    return high | (low << 12) | (mid >> 12)


def encode(item_id: int, alphabet: str, min_length: int = 7):
    if item_id < 0:
        raise ValueError("Negative numbers cannot be encoded.", item_id)

    length = len(alphabet)
    letters = []
    wobble = 0
    number = twiddle(item_id)
    nybble = -1
    while number or nybble or len(letters) < min_length:
        number, nybble = divmod(number, length)
        index = (nybble + wobble) % length
        wobble += index - len(letters)
        letters.append(alphabet[index])
    return "".join(letters)


def decode(code: str, alphabet: str, default=None):
    length = len(alphabet)
    number = 0
    wobble = 0
    multiplier = 1
    valid = True
    nybble = None
    for n, letter in enumerate(code):
        index = alphabet.find(letter)
        if index < 0:
            valid = False

        nybble = (index - wobble) % length
        wobble += index - n
        number += nybble * multiplier
        multiplier *= length

    if valid and nybble == 0:
        return twiddle(number)
    return default
