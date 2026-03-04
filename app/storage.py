import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiosqlite


@dataclass(frozen=True)
class PaletteResult:
    id: int
    filename: str
    sha256: str
    n_colors: int
    palette: list[dict[str, Any]]
    image_path: str
    created_at: str


def _load_palette(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, str):
        loaded = json.loads(value)
        if isinstance(loaded, list):
            return loaded
        return []
    if isinstance(value, list):
        return value
    return []


async def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(db_path) as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS palette_results (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              filename TEXT NOT NULL,
              sha256 TEXT NOT NULL,
              n_colors INTEGER NOT NULL,
              palette_json TEXT NOT NULL,
              image_path TEXT NOT NULL,
              created_at TEXT NOT NULL
            )
            """
        )
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_palette_results_created_at ON palette_results(created_at)")
        await conn.commit()


async def save_result(
    *,
    db_path: Path,
    filename: str,
    sha256: str,
    n_colors: int,
    palette: list[dict[str, Any]],
    image_path: str,
) -> int:
    created_at = datetime.now(timezone.utc).isoformat()
    palette_json = json.dumps(palette, ensure_ascii=False, separators=(",", ":"))
    async with aiosqlite.connect(db_path) as conn:
        cur = await conn.execute(
            """
            INSERT INTO palette_results (filename, sha256, n_colors, palette_json, image_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (filename, sha256, int(n_colors), palette_json, image_path, created_at),
        )
        await conn.commit()
        return int(cur.lastrowid)


async def get_result(db_path: Path, result_id: int) -> PaletteResult | None:
    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute(
            """
            SELECT id, filename, sha256, n_colors, palette_json, image_path, created_at
            FROM palette_results
            WHERE id = ?
            """,
            (int(result_id),),
        )
        row = await cur.fetchone()

    if row is None:
        return None

    palette = _load_palette(row["palette_json"])
    return PaletteResult(
        id=int(row["id"]),
        filename=str(row["filename"]),
        sha256=str(row["sha256"]),
        n_colors=int(row["n_colors"]),
        palette=palette,
        image_path=str(row["image_path"]),
        created_at=str(row["created_at"]),
    )


async def list_results(db_path: Path, *, limit: int = 20) -> list[PaletteResult]:
    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute(
            """
            SELECT id, filename, sha256, n_colors, palette_json, image_path, created_at
            FROM palette_results
            ORDER BY id DESC
            LIMIT ?
            """,
            (int(limit),),
        )
        rows = await cur.fetchall()

    out: list[PaletteResult] = []
    for row in rows:
        out.append(
            PaletteResult(
                id=int(row["id"]),
                filename=str(row["filename"]),
                sha256=str(row["sha256"]),
                n_colors=int(row["n_colors"]),
                palette=_load_palette(row["palette_json"]),
                image_path=str(row["image_path"]),
                created_at=str(row["created_at"]),
            )
        )
    return out


async def clear_results(db_path: Path) -> None:
    async with aiosqlite.connect(db_path) as conn:
        await conn.execute("DELETE FROM palette_results")
        await conn.commit()


async def list_image_paths(db_path: Path) -> list[str]:
    async with aiosqlite.connect(db_path) as conn:
        cur = await conn.execute("SELECT image_path FROM palette_results")
        rows = await cur.fetchall()
    return [str(row[0]) for row in rows if row and row[0]]

