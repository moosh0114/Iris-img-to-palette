from contextlib import asynccontextmanager
from html import escape
from pathlib import Path

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from .config import settings
from .services.format_service import format_result_for_template
from .services.palette_service import (
    clamp_n_colors,
    clear_history_records,
    extract_batch_palettes,
    load_history,
    load_result,
    normalize_method,
)
from .storage import init_db


templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))
MAX_BATCH_UPLOADS = 1000
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db(settings.db_path)
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="Iris Img to Palette", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
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
@limiter.limit("5/10seconds")
async def api_extract(
    request: Request,
    images: list[UploadFile] = File(...),
    n_colors: int = Form(10),
    current_index: int = Form(0),
    method: str = Form("kmeans"),
) -> HTMLResponse:
    if len(images) > MAX_BATCH_UPLOADS:
        return HTMLResponse(
            f"<div class='panel'>{escape(f'Too many images uploaded. Maximum is {MAX_BATCH_UPLOADS}.')}</div>",
            status_code=400,
        )

    try:
        result = await extract_batch_palettes(
            images,
            clamp_n_colors(int(n_colors)),
            db_path=settings.db_path,
            upload_dir=settings.upload_dir,
            method=normalize_method(method),
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
