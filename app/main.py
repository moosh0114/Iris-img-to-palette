from __future__ import annotations

import hashlib
import json
from pathlib import Path

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from scripts.extract_colors import extract_dominant_colors

from .storage import clear_results, get_result, init_db, list_results, save_result


REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "app.db"

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))

app = FastAPI(title="Iris Img to Palette")


@app.on_event("startup")
def _startup() -> None:
    init_db(DB_PATH)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
        },
    )


@app.get("/history", response_class=HTMLResponse)
def history(request: Request) -> HTMLResponse:
    results = list_results(DB_PATH, limit=20)
    return templates.TemplateResponse(
        "partials/history.html",
        {
            "request": request,
            "results": results,
        },
    )


@app.post("/api/history/clear", response_class=HTMLResponse)
def api_clear_history(request: Request) -> HTMLResponse:
    clear_results(DB_PATH)
    return templates.TemplateResponse(
        "partials/history.html",
        {
            "request": request,
            "results": [],
        },
    )


@app.get("/api/result/{result_id}", response_class=HTMLResponse)
def api_result(request: Request, result_id: int) -> HTMLResponse:
    result = get_result(DB_PATH, result_id)
    if result is None:
        return HTMLResponse("<div class='panel'>Not found.</div>", status_code=404)

    palette_for_template = result.palette
    if isinstance(palette_for_template, str):
        try:
            palette_for_template = json.loads(palette_for_template)
        except json.JSONDecodeError:
            palette_for_template = []
    if not isinstance(palette_for_template, list):
        palette_for_template = []

    palette_json_pretty = json.dumps(palette_for_template, ensure_ascii=False, indent=2)
    return templates.TemplateResponse(
        "partials/result.html",
        {
            "request": request,
            "result": {
                "id": result.id,
                "filename": result.filename,
                "n_colors": result.n_colors,
                "created_at": result.created_at,
                "palette": palette_for_template,
                "palette_json_pretty": palette_json_pretty,
            },
        },
    )


@app.post("/api/extract", response_class=HTMLResponse)
async def api_extract(
    request: Request,
    image: UploadFile = File(...),
    n_colors: int = Form(3),
) -> HTMLResponse:
    n = int(n_colors)
    n = max(1, min(12, n))

    original_name = Path(image.filename or "upload").name
    content = await image.read()
    if not content:
        return HTMLResponse("<div class='panel'>Empty upload.</div>", status_code=400)

    sha = hashlib.sha256(content).hexdigest()
    safe_name = "".join(ch if ch.isalnum() or ch in ("-", "_", ".", " ") else "_" for ch in original_name).strip()
    if not safe_name:
        safe_name = "upload"

    upload_path = UPLOAD_DIR / f"{sha[:16]}_{safe_name}"
    upload_path.write_bytes(content)

    palette = extract_dominant_colors(str(upload_path), n_colors=n)
    new_id = save_result(
        db_path=DB_PATH,
        filename=original_name,
        sha256=sha,
        n_colors=n,
        palette=palette,
        image_path=str(upload_path),
    )

    palette_json_pretty = json.dumps(palette, ensure_ascii=False, indent=2)
    results = list_results(DB_PATH, limit=20)

    return templates.TemplateResponse(
        "partials/extract_response.html",
        {
            "request": request,
            "result": {
                "id": new_id,
                "filename": original_name,
                "n_colors": n,
                "created_at": results[0].created_at if results else "",
                "palette": palette,
                "palette_json_pretty": palette_json_pretty,
            },
            "results": results,
        },
    )

