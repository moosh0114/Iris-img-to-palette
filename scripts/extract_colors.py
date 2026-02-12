from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from sklearn.cluster import KMeans


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


def extract_dominant_colors(image_path: str, n_colors: int = 3) -> list[str]:
    """
    Extract dominant colors from an image as hex strings.

    Returns:
        List[str]: e.g. ['#ff0000', '#00ff00', '#0000ff']
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

    return [
        "#{:02x}{:02x}{:02x}".format(*centers[idx])
        for idx in sorted_indices
    ]


if __name__ == "__main__":
    test_image = Path("test.jpg")
    if test_image.exists():
        colors = extract_dominant_colors(str(test_image))
        print(f"Extracted Palette: {colors}")
    else:
        print("Error: 'test.jpg' not found. Please place a test image in the root directory.")
