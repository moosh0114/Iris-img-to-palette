import re


HEX_PATTERN = re.compile(r"^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


def is_valid_hex(hex_str: str) -> bool:
    # return True if the string is a valid 3/6-digit hex color
    return bool(HEX_PATTERN.fullmatch(hex_str.strip()))


def normalize_hex(hex_str: str) -> str:
    value = hex_str.strip().lstrip("#")

    if not is_valid_hex(value):
        raise ValueError(f"Invalid hex color: {hex_str}")

    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)

    return f"#{value.lower()}"


def hex_to_rgb(hex_str: str) -> tuple:
    normalized = normalize_hex(hex_str)
    value = normalized[1:]
    return tuple(int(value[i:i + 2], 16) for i in range(0, 6, 2))


if __name__ == "__main__":
    samples = ["#abc", "abc", "#A1B2C3", "A1B2C3", "#12FG34", "12345"]

    for sample in samples:
        valid = is_valid_hex(sample)
        print(f"Input: {sample}")
        print(f"Valid: {valid}")

        if valid:
            normalized = normalize_hex(sample)
            rgb = hex_to_rgb(sample)
            print(f"Normalized: {normalized}")
            print(f"RGB: {rgb}")

        print()
