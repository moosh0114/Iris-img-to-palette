import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import strawberry
from fastapi.concurrency import run_in_threadpool
from strawberry.file_uploads import Upload
from strawberry.types import Info

from scripts.extract_colors import extract_dominant_colors

from .storage import PaletteResult, clear_results, get_result, list_results, save_result


REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "app.db"


@dataclass(frozen=True)
class Context:
    db_path: Path
    upload_dir: Path


async def context_getter() -> Context:
    return Context(db_path=DB_PATH, upload_dir=UPLOAD_DIR)


class UploadLike(Protocol):
    filename: str | None

    async def read(self) -> bytes: ...


def _clamp_n_colors(value: int) -> int:
    return max(1, min(12, int(value)))


def _sanitize_filename(filename: str) -> str:
    safe_name = "".join(ch if ch.isalnum() or ch in ("-", "_", ".", " ") else "_" for ch in filename).strip()
    return safe_name or "upload"


def _to_upload_url(image_path: str) -> str:
    return f"/uploads/{Path(image_path).name}"


def _palette_json_pretty(palette: list[dict[str, Any]]) -> str:
    return json.dumps(palette, ensure_ascii=False, indent=2)


def _build_result(content: bytes, original_name: str, n_colors: int, db_path: Path, upload_dir: Path) -> PaletteResult:
    n = _clamp_n_colors(n_colors)
    if not content:
        raise ValueError("Empty upload.")

    sha = hashlib.sha256(content).hexdigest()
    safe_name = _sanitize_filename(original_name)
    upload_dir.mkdir(parents=True, exist_ok=True)

    upload_path = upload_dir / f"{sha[:16]}_{safe_name}"
    upload_path.write_bytes(content)

    palette = extract_dominant_colors(str(upload_path), n_colors=n)
    new_id = save_result(
        db_path=db_path,
        filename=original_name,
        sha256=sha,
        n_colors=n,
        palette=palette,
        image_path=str(upload_path),
    )

    saved = get_result(db_path, new_id)
    if saved is None:
        raise RuntimeError("Failed to load saved result.")
    return saved


async def extract_and_store_upload(upload: UploadLike, n_colors: int, db_path: Path, upload_dir: Path) -> PaletteResult:
    original_name = Path(upload.filename or "upload").name
    content = await upload.read()
    return await run_in_threadpool(_build_result, content, original_name, n_colors, db_path, upload_dir)


async def clear_history_records(db_path: Path) -> None:
    await run_in_threadpool(clear_results, db_path)


async def load_history(db_path: Path, *, limit: int = 20) -> list[PaletteResult]:
    return await run_in_threadpool(list_results, db_path, limit=limit)


async def load_result(db_path: Path, result_id: int) -> PaletteResult | None:
    return await run_in_threadpool(get_result, db_path, result_id)


def format_result_for_template(result: PaletteResult) -> dict[str, Any]:
    return {
        "id": result.id,
        "filename": result.filename,
        "n_colors": result.n_colors,
        "created_at": result.created_at,
        "palette": result.palette,
        "palette_json_pretty": _palette_json_pretty(result.palette),
        "image_url": _to_upload_url(result.image_path),
    }


@strawberry.type
class OklchColor:
    L: float
    c: float
    h: float


@strawberry.type
class PaletteColor:
    hex: str
    oklch: OklchColor


@strawberry.type
class PaletteResultNode:
    id: int
    filename: str
    sha256: str
    n_colors: int
    image_url: str
    created_at: str
    palette_json_pretty: str
    palette: list[PaletteColor]


@strawberry.type
class OperationError:
    message: str
    code: str


@strawberry.type
class HistorySuccess:
    results: list[PaletteResultNode]


@strawberry.type
class ResultSuccess:
    result: PaletteResultNode


@strawberry.type
class ExtractPaletteSuccess:
    result: PaletteResultNode


@strawberry.type
class ClearHistorySuccess:
    ok: bool


HistoryResponse = HistorySuccess | OperationError
ResultResponse = ResultSuccess | OperationError
ExtractPaletteResponse = ExtractPaletteSuccess | OperationError
ClearHistoryResponse = ClearHistorySuccess | OperationError


@strawberry.type
class Query:
    @strawberry.field
    async def history(self, info: Info[Context, None], limit: int = 20) -> HistoryResponse:
        try:
            rows = await load_history(info.context.db_path, limit=max(1, min(100, limit)))
        except Exception:
            return OperationError(message="Failed to load history.", code="INTERNAL_ERROR")
        return HistorySuccess(results=[_to_result_node(item) for item in rows])

    @strawberry.field
    async def result(self, info: Info[Context, None], result_id: int) -> ResultResponse:
        try:
            item = await load_result(info.context.db_path, result_id)
        except Exception:
            return OperationError(message="Failed to load result.", code="INTERNAL_ERROR")
        if item is None:
            return OperationError(message="Result not found.", code="NOT_FOUND")
        return ResultSuccess(result=_to_result_node(item))


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def extract_palette(self, info: Info[Context, None], image: Upload, n_colors: int = 3) -> ExtractPaletteResponse:
        try:
            result = await extract_and_store_upload(
                upload=image,
                n_colors=n_colors,
                db_path=info.context.db_path,
                upload_dir=info.context.upload_dir,
            )
        except ValueError as exc:
            return OperationError(message=str(exc), code="BAD_REQUEST")
        except Exception:
            return OperationError(message="Failed to extract palette.", code="INTERNAL_ERROR")
        return ExtractPaletteSuccess(result=_to_result_node(result))

    @strawberry.mutation
    async def clear_history(self, info: Info[Context, None]) -> ClearHistoryResponse:
        try:
            await clear_history_records(info.context.db_path)
        except Exception:
            return OperationError(message="Failed to clear history.", code="INTERNAL_ERROR")
        return ClearHistorySuccess(ok=True)


def _to_result_node(result: PaletteResult) -> PaletteResultNode:
    palette_nodes: list[PaletteColor] = []
    for color in result.palette:
        oklch = color.get("oklch") or {}
        palette_nodes.append(
            PaletteColor(
                hex=str(color.get("hex", "")),
                oklch=OklchColor(
                    L=float(oklch.get("L", 0.0)),
                    c=float(oklch.get("c", 0.0)),
                    h=float(oklch.get("h", 0.0)),
                ),
            )
        )

    return PaletteResultNode(
        id=result.id,
        filename=result.filename,
        sha256=result.sha256,
        n_colors=result.n_colors,
        image_url=_to_upload_url(result.image_path),
        created_at=result.created_at,
        palette_json_pretty=_palette_json_pretty(result.palette),
        palette=palette_nodes,
    )


schema = strawberry.Schema(query=Query, mutation=Mutation)
