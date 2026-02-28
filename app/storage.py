import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
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
        conn.execute("CREATE INDEX IF NOT EXISTS idx_palette_results_created_at ON palette_results(created_at)")
        conn.commit()


def save_result(
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
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO palette_results (filename, sha256, n_colors, palette_json, image_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (filename, sha256, int(n_colors), palette_json, image_path, created_at),
        )
        conn.commit()
        return int(cur.lastrowid)


def get_result(db_path: Path, result_id: int) -> PaletteResult | None:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT id, filename, sha256, n_colors, palette_json, image_path, created_at
            FROM palette_results
            WHERE id = ?
            """,
            (int(result_id),),
        ).fetchone()

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


def list_results(db_path: Path, *, limit: int = 20) -> list[PaletteResult]:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, filename, sha256, n_colors, palette_json, image_path, created_at
            FROM palette_results
            ORDER BY id DESC
            LIMIT ?
            """,
            (int(limit),),
        ).fetchall()

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


def clear_results(db_path: Path) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM palette_results")
        conn.commit()


def list_image_paths(db_path: Path) -> list[str]:
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute("SELECT image_path FROM palette_results").fetchall()
    return [str(row[0]) for row in rows if row and row[0]]

