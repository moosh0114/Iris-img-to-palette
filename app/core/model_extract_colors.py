from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import torch

from core.ai import (
    extract_top10_gwo,
    extract_top10_saliency,
    extract_top10_kmeans,
    extract_top10_area_ratio_oklab,
    extract_top10_chroma_saliency_oklab,
    extract_top10_lightness_ratio_oklab,
    extract_top10_similar_area_oklab,
)
from core.ai.train.model import AestheticScorerMLP, apply_nms, load_model
from core.colors.color_oklab import oklab_to_hex
from core.colors.color_oklch import _rgb_to_oklab_vectorized, hex_to_oklch


_MODEL_CACHE: dict[Path, AestheticScorerMLP] = {}


def _load_scorer(model_path: Path) -> AestheticScorerMLP:
    resolved = model_path.resolve()
    cached = _MODEL_CACHE.get(resolved)
    if cached is not None:
        return cached

    if not resolved.exists():
        raise FileNotFoundError(f"Model file not found: {resolved}")

    model = AestheticScorerMLP(input_dim=19)
    model = load_model(model, str(resolved))
    _MODEL_CACHE[resolved] = model
    return model


def _rgb_palette_to_oklab_rows(colors_rgb: np.ndarray) -> list[dict[str, Any]]:
    rgb = np.clip(np.asarray(colors_rgb, dtype=np.float64), 0.0, 255.0) / 255.0
    labs = _rgb_to_oklab_vectorized(rgb)
    rows: list[dict[str, Any]] = []
    for idx, lab in enumerate(labs, start=1):
        rows.append(
            {
                "rank": idx,
                "oklab": {
                    "L": round(float(lab[0]), 3),
                    "a": round(float(lab[1]), 3),
                    "b": round(float(lab[2]), 3),
                },
            }
        )
    return rows


def _build_visual_rankings(area_data: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    base = area_data.get("top_colors", [])

    def _chroma(item: dict[str, Any]) -> float:
        oklab = item.get("oklab", {})
        a = float(oklab.get("a", 0.0))
        b = float(oklab.get("b", 0.0))
        return float(np.sqrt(a * a + b * b))

    vivid = sorted(base, key=_chroma, reverse=True)
    bright = sorted(base, key=lambda x: float(x.get("oklab", {}).get("L", 0.0)), reverse=True)

    return {
        "dominant_main_color_ranking": [
            {
                "rank": idx + 1,
                "area_ratio": round(float(item.get("area_ratio", 0.0)), 3),
                "oklab": item.get("oklab", {}),
            }
            for idx, item in enumerate(base)
        ],
        "vividness_ranking": [
            {
                "rank": idx + 1,
                "chroma": round(_chroma(item), 3),
                "oklab": item.get("oklab", {}),
            }
            for idx, item in enumerate(vivid)
        ],
        "brightness_ranking": [
            {
                "rank": idx + 1,
                "lightness": round(float(item.get("oklab", {}).get("L", 0.0)), 3),
                "oklab": item.get("oklab", {}),
            }
            for idx, item in enumerate(bright)
        ],
    }


def _build_feature_matrix(image_path: str | Path) -> tuple[np.ndarray, list[dict[str, Any]]]:
    gwo_colors = extract_top10_gwo(image_path, 10)
    kmeans_colors = extract_top10_kmeans(image_path, 10)
    saliency_colors = extract_top10_saliency(image_path, 10)

    area_data = extract_top10_area_ratio_oklab(image_path, 10)
    similar_data = extract_top10_similar_area_oklab(image_path, 10)
    chroma_data = extract_top10_chroma_saliency_oklab(image_path, 10)
    lightness_data = extract_top10_lightness_ratio_oklab(image_path, 10)
    visual_rankings = _build_visual_rankings(area_data)

    sources = [
        ("gwo_colors", [1.0, 0.0, 0.0], _rgb_palette_to_oklab_rows(gwo_colors)),
        ("kmeans_colors", [0.0, 1.0, 0.0], _rgb_palette_to_oklab_rows(kmeans_colors)),
        ("saliency_colors", [0.0, 0.0, 1.0], _rgb_palette_to_oklab_rows(saliency_colors)),
    ]

    visual_dimensions_oklab = {
        "physical_area_ratio": area_data,
        "similar_color_area_sum": similar_data,
        "chroma_saliency": chroma_data,
        "lightness_ratio": lightness_data,
    }

    candidates: list[dict[str, Any]] = []
    for source_name, one_hot, rows in sources:
        for row in rows:
            candidates.append({"color": row, "source": one_hot, "source_name": source_name})

    all_labs = np.array(
        [
            [
                float(c["color"]["oklab"]["L"]),
                float(c["color"]["oklab"]["a"]),
                float(c["color"]["oklab"]["b"]),
            ]
            for c in candidates
        ],
        dtype=np.float32,
    )
    mean_lab = np.mean(all_labs, axis=0)

    def _get_metric_for_color(target_lab: np.ndarray, metric_name: str, sub_metric: str = "score") -> float:
        if metric_name in visual_dimensions_oklab:
            rows = visual_dimensions_oklab[metric_name].get("top_colors", [])
        elif metric_name in visual_rankings:
            rows = visual_rankings[metric_name]
        else:
            return 0.0

        best = 0.0
        for row in rows:
            o = row.get("oklab", {})
            cand_lab = np.array([float(o.get("L", 0.0)), float(o.get("a", 0.0)), float(o.get("b", 0.0))], dtype=np.float32)
            if np.linalg.norm(target_lab - cand_lab) < 0.01:
                best = float(row.get(sub_metric, 0.0))
                break
        return best

    features: list[list[float]] = []
    output_candidates: list[dict[str, Any]] = []

    for i, candidate in enumerate(candidates):
        lab = all_labs[i]
        source = candidate["source"]
        rank_in_src = int(candidate["color"]["rank"])
        f_rank_scaled = max(0.0, 1.0 - (rank_in_src - 1) / 9.0)

        l = float(lab[0])
        a = float(lab[1])
        b = float(lab[2])
        chroma = float(np.sqrt(a * a + b * b))

        f_area = _get_metric_for_color(lab, "physical_area_ratio", "score")
        f_sim_area = _get_metric_for_color(lab, "similar_color_area_sum", "score")
        f_chroma_saliency = _get_metric_for_color(lab, "chroma_saliency", "score")
        f_lightness_ratio = _get_metric_for_color(lab, "lightness_ratio", "score")
        f_dom = _get_metric_for_color(lab, "dominant_main_color_ranking", "area_ratio")
        f_viv = _get_metric_for_color(lab, "vividness_ranking", "chroma")
        f_bright = _get_metric_for_color(lab, "brightness_ranking", "lightness")

        other_labs = np.delete(all_labs, i, axis=0)
        dists = np.linalg.norm(other_labs - lab, axis=-1)
        min_dist = float(np.min(dists)) if len(dists) > 0 else 0.0
        mean_dist = float(np.mean(dists)) if len(dists) > 0 else 0.0
        local_density = float(np.sum(dists < 0.03)) if len(dists) > 0 else 0.0
        dist_to_mean = float(np.linalg.norm(lab - mean_lab))

        feature = source + [
            f_rank_scaled,
            l,
            a,
            b,
            chroma,
            f_area,
            f_sim_area,
            f_chroma_saliency,
            f_lightness_ratio,
            f_dom,
            f_viv,
            f_bright,
            min_dist,
            mean_dist,
            local_density,
            dist_to_mean,
        ]
        features.append(feature)
        output_candidates.append(
            {
                "oklab": {"L": l, "a": a, "b": b},
                "source": candidate["source_name"],
            }
        )

    return np.array(features, dtype=np.float32), output_candidates


def extract_dominant_colors_with_model(
    image_path: str,
    n_colors: int,
    *,
    model_path: str | Path,
    similarity_threshold: float = 0.02,
) -> list[dict[str, Any]]:
    feature_matrix, candidates = _build_feature_matrix(image_path)
    if feature_matrix.size == 0:
        return []

    model = _load_scorer(Path(model_path))
    features = torch.from_numpy(feature_matrix).unsqueeze(0)
    scores = model.predict_proba(features).cpu().numpy().flatten()
    selected = apply_nms(
        candidates,
        scores,
        max_colors=max(1, int(n_colors)),
        similarity_threshold=float(similarity_threshold),
    )

    palette: list[dict[str, Any]] = []
    for color in selected:
        oklab = color["oklab"]
        hex_color = oklab_to_hex(float(oklab["L"]), float(oklab["a"]), float(oklab["b"]))
        L, c, h = hex_to_oklch(hex_color)
        if c < 1e-9:
            h = 0.0
        palette.append(
            {
                "hex": hex_color,
                "oklch": {
                    "L": round(float(L), 6),
                    "c": round(float(c), 6),
                    "h": round(float(h), 6),
                },
            }
        )
    return palette
