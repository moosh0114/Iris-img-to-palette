from pathlib import Path
from typing import Any

from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool

from ..config import settings
from ..core.extract_colors import extract_dominant_colors
from ..core.model_extract_colors import extract_dominant_colors_with_model
from ..storage import PaletteResult, clear_results, get_result, list_image_paths, list_results, save_result
from .file_service import (
    finalize_upload,
    is_within_upload_dir,
    safe_unlink,
    sanitize_filename,
    validate_image_magic,
    write_upload_to_temp,
)
from .format_service import palettes_response_payload


def clamp_n_colors(value: int) -> int:
    return max(1, min(12, int(value)))


def normalize_method(method: str | None) -> str:
    value = (method or "kmeans").strip().lower()
    return "model" if value in {"model", "ai"} else "kmeans"


async def load_history(db_path: Path, *, limit: int = settings.history_limit) -> list[PaletteResult]:
    return await list_results(db_path, limit=limit)


async def load_result(db_path: Path, result_id: int) -> PaletteResult | None:
    return await get_result(db_path, result_id)


async def clear_history_records(db_path: Path) -> None:
    paths = await list_image_paths(db_path)
    await clear_results(db_path)
    upload_root = settings.upload_dir.resolve()
    for path in paths:
        file_path = Path(path)
        if is_within_upload_dir(file_path, upload_root):
            safe_unlink(file_path.resolve())


async def extract_batch_palettes(
    uploads: list[UploadFile],
    n_colors: int,
    *,
    db_path: Path,
    upload_dir: Path,
    method: str = "kmeans",
) -> dict[str, Any]:
    if not uploads:
        raise ValueError("Please upload at least one image.")
    if len(uploads) > settings.max_batch_images:
        raise ValueError(f"You can upload up to {settings.max_batch_images} images at once.")

    n = clamp_n_colors(n_colors)
    selected_method = normalize_method(method)
    palettes_raw: list[list[dict[str, Any]]] = []

    for upload in uploads:
        original_name = Path(upload.filename or "upload").name
        safe_name = sanitize_filename(original_name)
        content_type = (upload.content_type or "").lower()
        if content_type and not content_type.startswith("image/"):
            raise ValueError(f"Unsupported file type: {original_name}")

        temp_path: Path | None = None
        final_path: Path | None = None
        try:
            temp_path, file_hash = await write_upload_to_temp(upload, upload_dir, safe_name, original_name)
            await run_in_threadpool(validate_image_magic, temp_path, original_name)
            final_path = finalize_upload(temp_path, upload_dir, file_hash, safe_name)
            temp_path = None

            try:
                if selected_method == "model":
                    palette = await run_in_threadpool(
                        extract_dominant_colors_with_model,
                        str(final_path),
                        n,
                        model_path=settings.model_path,
                        similarity_threshold=settings.model_similarity_threshold,
                    )
                else:
                    palette = await run_in_threadpool(extract_dominant_colors, str(final_path), n)
            except FileNotFoundError as exc:
                raise ValueError(str(exc)) from exc
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
            if temp_path is not None and temp_path.exists():
                safe_unlink(temp_path)
            if final_path is not None and final_path.exists():
                safe_unlink(final_path)

    return palettes_response_payload(palettes_raw, n)

