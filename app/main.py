from contextlib import asynccontextmanager
from html import escape
from pathlib import Path

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import settings
from .palette_service import (
    clamp_n_colors,
    clear_history_records,
    extract_batch_palettes,
    format_result_for_template,
    load_history,
    load_result,
)
from .storage import init_db


templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db(settings.db_path)
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="Iris Img to Palette", lifespan=lifespan)
app.mount("/uploads", StaticFiles(directory=str(settings.upload_dir), check_dir=False), name="uploads")
app.mount("/static", StaticFiles(directory=str(Path(__file__).resolve().parent / "static")), name="static")


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    empty_result = {
        "palette": [],
        "palette_json_pretty": "",
        "palettes_json": "[]",
    }
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "result": empty_result,
        },
    )


@app.get("/history", response_class=HTMLResponse)
async def history(request: Request) -> HTMLResponse:
    history_rows = await load_history(settings.db_path, limit=settings.history_limit)
    results = [format_result_for_template(item) for item in history_rows]
    return templates.TemplateResponse(
        "partials/history.html",
        {
            "request": request,
            "results": results,
        },
    )


@app.post("/api/history/clear", response_class=HTMLResponse)
async def api_clear_history(request: Request) -> HTMLResponse:
    await clear_history_records(settings.db_path)
    return templates.TemplateResponse(
        "partials/history.html",
        {
            "request": request,
            "results": [],
        },
    )


@app.get("/api/result/{result_id}", response_class=HTMLResponse)
async def api_result(request: Request, result_id: int) -> HTMLResponse:
    result = await load_result(settings.db_path, result_id)
    if result is None:
        return HTMLResponse("<div class='panel'>Not found.</div>", status_code=404)

    return templates.TemplateResponse(
        "partials/result.html",
        {
            "request": request,
            "result": format_result_for_template(result),
        },
    )


@app.post("/api/extract", response_class=HTMLResponse)
async def api_extract(
    request: Request,
    images: list[UploadFile] = File(...),
    n_colors: int = Form(10),
    current_index: int = Form(0),
) -> HTMLResponse:
    try:
        result = await extract_batch_palettes(
            images,
            clamp_n_colors(int(n_colors)),
            db_path=settings.db_path,
            upload_dir=settings.upload_dir,
        )
        palettes = result.get("palettes") or []
        if palettes:
            idx = max(0, min(int(current_index), len(palettes) - 1))
            result["palette"] = palettes[idx]
    except ValueError as exc:
        return HTMLResponse(f"<div class='panel'>{escape(str(exc))}</div>", status_code=400)

    return templates.TemplateResponse(
        "partials/extract_response.html",
        {
            "request": request,
            "result": result,
        },
    )
