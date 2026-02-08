import numpy as np


# Oklab -> LMS' (Bjorn Ottosson standard constants)
OKLAB_TO_LMS_PRIME = np.array(
    [
        [1.0, 0.3963377774, 0.2158037573],
        [1.0, -0.1055613458, -0.0638541728],
        [1.0, -0.0894841775, -1.2914855480],
    ],
    dtype=np.float64,
)

# Linear LMS -> Linear sRGB (Bjorn Ottosson standard constants)
LMS_TO_LINEAR_SRGB = np.array(
    [
        [4.0767416621, -3.3077115913, 0.2309699292],
        [-1.2684380046, 2.6097574011, -0.3413193965],
        [-0.0041960863, -0.7034186147, 1.7076147010],
    ],
    dtype=np.float64,
)


def _linear_to_srgb(c: float) -> float:
    """Convert one linear RGB channel to sRGB with standard gamma correction."""
    if c <= 0.0031308:
        return 12.92 * c
    return 1.055 * (c ** (1.0 / 2.4)) - 0.055


def oklab_to_hex(L: float, a: float, b: float) -> str:
    """
    Convert Oklab (L, a, b) to hexadecimal sRGB string.

    Pipeline: Oklab -> LMS -> Linear sRGB -> sRGB -> Hex.
    """
    oklab = np.array([L, a, b], dtype=np.float64)

    # Oklab -> LMS' then undo cube root to get linear LMS
    lms_prime = OKLAB_TO_LMS_PRIME @ oklab
    lms = lms_prime ** 3

    # LMS -> linear sRGB
    linear_rgb = LMS_TO_LINEAR_SRGB @ lms
    linear_rgb = np.clip(linear_rgb, 0.0, 1.0)

    # Linear sRGB -> sRGB (gamma encoded)
    srgb = np.array([_linear_to_srgb(channel) for channel in linear_rgb], dtype=np.float64)
    srgb = np.clip(srgb, 0.0, 1.0)

    rgb_255 = np.round(srgb * 255.0).astype(int)
    return "#{:02x}{:02x}{:02x}".format(*rgb_255)


if __name__ == "__main__":
    result = oklab_to_hex(1.0, 0.0, 0.0)
    print(result)
    assert result == "#ffffff", f"Expected #ffffff, got {result}"
