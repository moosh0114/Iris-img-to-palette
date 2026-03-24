# This extractor computes per-pixel saliency weights, converts sampled pixels to
# OKLab, and runs weighted k-means with k=10.
# Pixels with higher visual saliency contribute more to the cluster centers.
# It returns 10 colors sorted by weighted cluster support, meaning colors from
# visually salient regions are prioritized rather than pure global pixel frequency.

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from sklearn.cluster import KMeans

from core.colors.color_oklab import oklab_to_hex
from core.colors.color_oklch import _linear_rgb_to_oklab, _srgb_channel_to_linear


def _rgb_to_oklab_pixels(rgb_pixels: np.ndarray) -> np.ndarray:
    rgb_unit = rgb_pixels.astype(np.float64) / 255.0
    oklab_pixels = np.empty_like(rgb_unit, dtype=np.float64)
    for i, (r, g, b) in enumerate(rgb_unit):
        lr = _srgb_channel_to_linear(float(r))
        lg = _srgb_channel_to_linear(float(g))
        lb = _srgb_channel_to_linear(float(b))
        oklab_pixels[i] = _linear_rgb_to_oklab(lr, lg, lb)
    return oklab_pixels


def _compute_saliency_weights(image_rgb: np.ndarray) -> np.ndarray:
    h, w = image_rgb.shape[:2]

    saliency = None
    if hasattr(cv2, "saliency") and hasattr(cv2.saliency, "StaticSaliencySpectralResidual_create"):
        saliency = cv2.saliency.StaticSaliencySpectralResidual_create()

    if saliency is not None:
        success, saliency_map = saliency.computeSaliency(image_rgb)
        if success and saliency_map is not None:
            saliency_map = saliency_map.astype(np.float32)
            if saliency_map.max() > 1.0:
                saliency_map = saliency_map / 255.0
            saliency_map = np.clip(saliency_map, 0.0, 1.0)
            return saliency_map.reshape(-1)

    # Fallback: gradient-based visual importance map.
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0
    grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    mag = cv2.magnitude(grad_x, grad_y)
    if mag.max() > 0.0:
        mag = mag / (mag.max() + 1e-8)
    else:
        mag = np.ones((h, w), dtype=np.float32)
    return np.clip(mag.reshape(-1), 0.0, 1.0)


def extract_top10_saliency(
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
    pixels_rgb = img_rgb.reshape(-1, 3)
    weights = _compute_saliency_weights(img_rgb)

    n = len(pixels_rgb)
    sample_n = max(k, min(int(n * sample_ratio), max_samples))
    rng = np.random.default_rng(random_state)
    sample_idx = rng.choice(n, sample_n, replace=False)

    sampled_rgb = pixels_rgb[sample_idx]
    sampled_weights = weights[sample_idx]
    sampled_weights = np.maximum(sampled_weights, 1e-3)

    sampled_oklab = _rgb_to_oklab_pixels(sampled_rgb)

    kmeans = KMeans(n_clusters=k, n_init=10, random_state=random_state)
    kmeans.fit(sampled_oklab, sample_weight=sampled_weights)
    centers_oklab = kmeans.cluster_centers_

    # Sort by weighted cluster support (dominance first).
    labels = kmeans.labels_
    cluster_weight = np.bincount(labels, weights=sampled_weights, minlength=k)
    sort_idx = np.argsort(-cluster_weight)
    sorted_centers = centers_oklab[sort_idx]

    result_rgb: list[list[int]] = []
    for center in sorted_centers:
        hex_str = oklab_to_hex(float(center[0]), float(center[1]), float(center[2]))
        h = hex_str.lstrip("#")
        result_rgb.append([int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)])

    return np.array(result_rgb, dtype=np.int32)


if __name__ == "__main__":
    colors = extract_top10_saliency("data/uploads/254bd6e6c931c97c_test.png")
    print("Top colors ( RGB ) :")
    for i, c in enumerate(colors, 1):
        print(f"{i}: {c}  #{c[0]:02x}{c[1]:02x}{c[2]:02x}")
