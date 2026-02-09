import math

def _srgb_channel_to_linear(c: float) -> float:
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def _hex_to_linear_rgb(hex_str: str) -> tuple[float, float, float]:
    s = hex_str.strip()
    if s.startswith("#"):
        s = s[1:]
    if len(s) != 6:
        raise ValueError("hex_str must be in RRGGBB format")

    r8 = int(s[0:2], 16)
    g8 = int(s[2:4], 16)
    b8 = int(s[4:6], 16)

    return (
        _srgb_channel_to_linear(r8 / 255.0),
        _srgb_channel_to_linear(g8 / 255.0),
        _srgb_channel_to_linear(b8 / 255.0),
    )


def _linear_rgb_to_oklab(r: float, g: float, b: float) -> tuple[float, float, float]:
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b

    l_ = math.copysign(abs(l) ** (1 / 3), l)
    m_ = math.copysign(abs(m) ** (1 / 3), m)
    s_ = math.copysign(abs(s) ** (1 / 3), s)

    L = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    a = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    b = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_
    return L, a, b


def oklab_to_oklch(L: float, a: float, b: float) -> tuple[float, float, float]:
    C = math.sqrt(a * a + b * b)
    h = math.degrees(math.atan2(b, a)) % 360.0
    return L, C, h


def hex_to_oklch(hex_str: str) -> tuple[float, float, float]:
    r, g, b = _hex_to_linear_rgb(hex_str)
    L, a, b = _linear_rgb_to_oklab(r, g, b)
    return oklab_to_oklch(L, a, b)

if __name__ == "__main__":
    # Hex -> OKLCH Already include OKLAB -> OKLCH testing
    hex_val = "#929cf9"
    l1, c1, h1 = hex_to_oklch(hex_val)
    print(f"HEX {hex_val} -> L: {l1:.4f}, C: {c1:.4f}, h: {h1:.2f}°")

    # Edge Situation
    black_hex = "#000000"
    l3, c3, h3 = hex_to_oklch(black_hex)
    print(f"HEX {black_hex} -> L: {l3:.4f}, C: {c3:.4f}, h: {h3:.2f}°")