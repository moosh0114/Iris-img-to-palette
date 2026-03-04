import hashlib
import json
import os
from pathlib import Path
from typing import Any

from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool

from .core.extract_colors import extract_dominant_colors

from .config import settings
from .storage import PaletteResult, clear_results, get_result, list_image_paths, list_results, save_result


MAGIC_BYTES = {b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n", b"GIF8", b"RIFF", b"BM"}


def clamp_n_colors(value: int) -> int:
    return max(1, min(12, int(value)))


def sanitize_filename(filename: str) -> str:
    safe_name = "".join(ch if ch.isalnum() or ch in ("-", "_", ".", " ") else "_" for ch in filename).strip()
    return safe_name or "upload"


def to_upload_url(image_path: str) -> str:
    return f"/uploads/{Path(image_path).name}"


def _palette_json_pretty(palette: list[dict[str, Any]]) -> str:
    return json.dumps(palette, ensure_ascii=False, indent=2)


def _palette_to_oklch_triplets(palette: list[dict[str, Any]]) -> list[list[float]]:
    out: list[list[float]] = []
    for color in palette:
        oklch = color.get("oklch") or {}
        out.append(
            [
                round(float(oklch.get("L", 0.0)), 3),
                round(float(oklch.get("c", 0.0)), 3),
                round(float(oklch.get("h", 0.0)), 3),
            ]
        )
    return out


def build_copy_json_pretty(palettes: list[list[list[float]]]) -> str:
    indent1 = "  "
    indent2 = "    "
    lines: list[str] = ["{", f'{indent1}"palettes": [']
    for idx, palette in enumerate(palettes):
        encoded = json.dumps(palette, ensure_ascii=False, separators=(",", ":"))
        suffix = "," if idx < len(palettes) - 1 else ""
        lines.append(f"{indent2}{encoded}{suffix}")
    lines.extend([f"{indent1}]", "}"])
    return "\n".join(lines)


def format_result_for_template(result: PaletteResult) -> dict[str, Any]:
    return {
        "id": result.id,
        "filename": result.filename,
        "n_colors": result.n_colors,
        "created_at": result.created_at,
        "palette": result.palette,
        "palette_json_pretty": _palette_json_pretty(result.palette),
        "image_url": to_upload_url(result.image_path),
    }


async def load_history(db_path: Path, *, limit: int = settings.history_limit) -> list[PaletteResult]:
    return await list_results(db_path, limit=limit)


async def load_result(db_path: Path, result_id: int) -> PaletteResult | None:
    return await get_result(db_path, result_id)


async def clear_history_records(db_path: Path) -> None:
    paths = await list_image_paths(db_path)
    await clear_results(db_path)
    upload_root = settings.upload_dir.resolve()
    for path in paths:
        p = Path(path).resolve()
        if upload_root in p.parents:
            p.unlink(missing_ok=True)


async def extract_batch_palettes(
    uploads: list[UploadFile],
    n_colors: int,
    *,
    db_path: Path,
    upload_dir: Path,
) -> dict[str, Any]:
    if not uploads:
        raise ValueError("Please upload at least one image.")
    if len(uploads) > settings.max_batch_images:
        raise ValueError(f"You can upload up to {settings.max_batch_images} images at once.")

    n = clamp_n_colors(n_colors)
    palettes_raw: list[list[dict[str, Any]]] = []

    for upload in uploads:
        original_name = Path(upload.filename or "upload").name
        safe_name = sanitize_filename(original_name)
        content_type = (upload.content_type or "").lower()
        if content_type and not content_type.startswith("image/"):
            raise ValueError(f"Unsupported file type: {original_name}")

        upload_dir.mkdir(parents=True, exist_ok=True)
        temp_path = upload_dir / f".tmp_batch_{os.urandom(8).hex()}_{safe_name}"
        total_bytes = 0
        sha256 = hashlib.sha256()
        final_path: Path | None = None
        try:
            with temp_path.open("wb") as f:
                while True:
                    chunk = await upload.read(settings.upload_chunk_size)
                    if not chunk:
                        break
                    total_bytes += len(chunk)
                    if total_bytes > settings.max_upload_bytes:
                        limit_mb = settings.max_upload_bytes // (1024 * 1024)
                        raise ValueError(f"File '{original_name}' exceeds {limit_mb}MB.")
                    sha256.update(chunk)
                    f.write(chunk)

            if total_bytes == 0:
                raise ValueError(f"File '{original_name}' is empty.")

            with temp_path.open("rb") as f:
                header = f.read(16)
            if not any(header.startswith(magic) for magic in MAGIC_BYTES):
                raise ValueError(f"'{original_name}' is not a valid image.")

            file_hash = sha256.hexdigest()
            final_path = upload_dir / f"{file_hash[:16]}_{safe_name}"
            temp_path.replace(final_path)
            palette = await run_in_threadpool(extract_dominant_colors, str(final_path), n)
            palettes_raw.append(palette)

            await save_result(
                db_path=db_path,
                filename=original_name,
                sha256=file_hash,
                n_colors=n,
                palette=palette,
                image_path=str(final_path),
            )
            final_path = None
        finally:
            await upload.close()
            if temp_path.exists():
                temp_path.unlink()
            if final_path is not None and final_path.exists():
                final_path.unlink()

    palettes_oklch = [_palette_to_oklch_triplets(item) for item in palettes_raw]
    return {
        "n_colors": n,
        "palette": palettes_raw[0] if palettes_raw else [],
        "palettes": palettes_raw,
        "palettes_json": json.dumps(palettes_raw, ensure_ascii=False, separators=(",", ":")),
        "palette_json_pretty": build_copy_json_pretty(palettes_oklch),
        "total_images": len(palettes_raw),
    }
