from pathlib import Path

import cv2
import numpy as np
from sklearn.cluster import KMeans

try:
    # When imported as a package (e.g. from FastAPI app)
    from .color_oklch import hex_to_oklch
except ImportError:  # pragma: no cover
    # When executed directly as a script
    from color_oklch import hex_to_oklch


def _resize_for_speed(image_bgr: np.ndarray) -> np.ndarray:
    """
    Resize image for faster clustering.
    Rule: use width 100px or 10% scale, whichever is smaller in width.
    """
    height, width = image_bgr.shape[:2]
    target_width = max(1, min(100, int(width * 0.1)))

    if target_width >= width:
        return image_bgr

    target_height = max(1, int(height * (target_width / width)))
    return cv2.resize(image_bgr, (target_width, target_height), interpolation=cv2.INTER_AREA)


def extract_dominant_colors(image_path: str, n_colors: int = 3) -> list[dict[str, object]]:
    """
    Extract dominant colors from an image in hex + OKLCH format.

    Returns:
        List[dict[str, object]]: e.g.
        [
            {"hex": "#ff0000", "oklch": {"L": 0.628, "c": 0.258, "h": 29.23}},
            ...
        ]
    """
    image_bgr = cv2.imread(image_path)
    if image_bgr is None:
        raise FileNotFoundError(f"Cannot read image: {image_path}")

    small_bgr = _resize_for_speed(image_bgr)
    image_rgb = cv2.cvtColor(small_bgr, cv2.COLOR_BGR2RGB)

    pixels = image_rgb.reshape(-1, 3)
    kmeans = KMeans(n_clusters=n_colors, n_init="auto", random_state=42)
    labels = kmeans.fit_predict(pixels)

    counts = np.bincount(labels, minlength=n_colors)
    centers = np.rint(kmeans.cluster_centers_).astype(np.uint8)
    sorted_indices = np.argsort(counts)[::-1]

    results: list[dict[str, object]] = []
    for idx in sorted_indices:
        hex_color = "#{:02x}{:02x}{:02x}".format(*centers[idx])
        L, c, h = hex_to_oklch(hex_color)

        # OKLCH hue is undefined for achromatic colors; normalize to 0 for stable output.
        if c < 1e-9:
            h = 0.0

        results.append(
            {
                "hex": hex_color,
                "oklch": {
                    "L": round(float(L), 6),
                    "c": round(float(c), 6),
                    "h": round(float(h), 6),
                },
            }
        )

    return results


if __name__ == "__main__":
    test_image = Path("test.jpg")
    if test_image.exists():
        colors = extract_dominant_colors(str(test_image))
        print(f"Extracted Palette: {colors}")
    else:
        print("Error: 'test.jpg' not found. Please place a test image in the root directory.")
