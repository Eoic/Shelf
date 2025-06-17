import random

CROCKFORD_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def encode_crockford(num: int, length: int = 13) -> str:
    """Encode an integer to Crockford's Base32 string."""
    chars = []

    while num > 0:
        num, rem = divmod(num, 32)
        chars.append(CROCKFORD_ALPHABET[rem])

    while len(chars) < length:
        chars.append("0")

    return "".join(reversed(chars))


def generate_crockford_id(length: int = 13) -> str:
    """Generate a random Crockford Base32 ID of given length."""
    num = random.SystemRandom().getrandbits(length * 5)
    return encode_crockford(num, length)
