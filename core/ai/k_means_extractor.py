# This method samples pixels from the image and runs k-means in RGB space with
# k=10. Each cluster center is treated as one dominant color.
# The 10 centers are sorted by cluster size (pixel support) in descending order,
# so earlier colors represent more frequent colors in the sampled pixels.

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from sklearn.cluster import KMeans


def extract_top10_kmeans(
    image_path: str | Path,
    k: int = 10,
    sample_ratio: float = 0.35,
    max_samples: int = 40000,
    random_state: int = 42,
) -> np.ndarray:
    img_bgr = cv2.imread(str(image_path))
    if img_bgr is None:
        raise ValueError(f"Unable to read image: {image_path}")

    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    pixels_rgb = img_rgb.reshape(-1, 3).astype(np.float64)

    n = len(pixels_rgb)
    sample_n = max(k, min(int(n * sample_ratio), max_samples))
    rng = np.random.default_rng(random_state)
    sample_idx = rng.choice(n, sample_n, replace=False)
    sampled_rgb = pixels_rgb[sample_idx]

    kmeans = KMeans(n_clusters=k, init="k-means++", n_init=10, random_state=random_state)
    labels = kmeans.fit_predict(sampled_rgb)
    centers_rgb = np.clip(np.rint(kmeans.cluster_centers_), 0, 255).astype(np.int32)

    # Sort by cluster support (dominant colors first).
    counts = np.bincount(labels, minlength=k)
    sort_idx = np.argsort(-counts)
    return centers_rgb[sort_idx]


if __name__ == "__main__":
    colors = extract_top10_kmeans("data/uploads/254bd6e6c931c97c_test.png")
    print("Top 10 dominant colors ( RGB ) :")
    for i, c in enumerate(colors, 1):
        print(f"{i}: {c}  #{c[0]:02x}{c[1]:02x}{c[2]:02x}")
