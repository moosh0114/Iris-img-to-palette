from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from strawberry.fastapi import GraphQLRouter

from .graphql_schema import (
    DB_PATH,
    UPLOAD_DIR,
    clear_history_records,
    context_getter,
    extract_and_store_upload,
    format_result_for_template,
    load_history,
    load_result,
    schema,
)
from .storage import init_db


templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))

app = FastAPI(title="Iris Img to Palette")
app.include_router(GraphQLRouter(schema, context_getter=context_getter), prefix="/graphql", tags=["graphql"])
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR), check_dir=False), name="uploads")


@app.on_event("startup")
async def _startup() -> None:
    await run_in_threadpool(init_db, DB_PATH)
    await run_in_threadpool(UPLOAD_DIR.mkdir, parents=True, exist_ok=True)


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
        },
    )


@app.get("/history", response_class=HTMLResponse)
async def history(request: Request) -> HTMLResponse:
    results = await load_history(DB_PATH, limit=20)
    return templates.TemplateResponse(
        "partials/history.html",
        {
            "request": request,
            "results": results,
        },
    )


@app.post("/api/history/clear", response_class=HTMLResponse)
async def api_clear_history(request: Request) -> HTMLResponse:
    await clear_history_records(DB_PATH)
    return templates.TemplateResponse(
        "partials/history.html",
        {
            "request": request,
            "results": [],
        },
    )


@app.get("/api/result/{result_id}", response_class=HTMLResponse)
async def api_result(request: Request, result_id: int) -> HTMLResponse:
    result = await load_result(DB_PATH, result_id)
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
    image: UploadFile = File(...),
    n_colors: int = Form(3),
) -> HTMLResponse:
    try:
        result = await extract_and_store_upload(
            upload=image,
            n_colors=int(n_colors),
            db_path=DB_PATH,
            upload_dir=UPLOAD_DIR,
        )
    except ValueError as exc:
        return HTMLResponse(f"<div class='panel'>{exc}</div>", status_code=400)

    results = await load_history(DB_PATH, limit=20)
    return templates.TemplateResponse(
        "partials/extract_response.html",
        {
            "request": request,
            "result": format_result_for_template(result),
            "results": results,
        },
    )
