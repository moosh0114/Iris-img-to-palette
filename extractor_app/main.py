from pathlib import Path
import tempfile
import os
import shutil
import traceback
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from fastapi import FastAPI, File, UploadFile, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.concurrency import run_in_threadpool

import sys

# Add project root to sys path so we can import core modules.
sys.path.append(str(Path(__file__).resolve().parent.parent))

from core.ai.gwo_extraction import extract_top10_oklab
from core.ai.saliency_extraction import extract_top10_saliency


app = FastAPI(title="Palette Extraction App")
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "selected_method": "gwo",
        },
    )


@app.post("/api/extract", response_class=HTMLResponse)
async def api_extract(
    request: Request,
    image: UploadFile = File(...),
    method: str = Form("gwo"),
) -> HTMLResponse:
    if not image:
        return HTMLResponse("<div class='text-red-500'>No image uploaded</div>", status_code=400)

    method = (method or "gwo").strip().lower()

    if method not in {"gwo", "saliency"}:
        return HTMLResponse("<div class='text-red-500'>Invalid extraction method</div>", status_code=400)

    fd, temp_path = tempfile.mkstemp(suffix=".png")
    os.close(fd)

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        if method == "saliency":
            colors = await run_in_threadpool(extract_top10_saliency, temp_path, 10)
        else:
            colors = await run_in_threadpool(extract_top10_oklab, temp_path, 10)

    except Exception:
        tb = traceback.format_exc()
        logger.error("[EXTRACTION ERROR]\n%s", tb)
        return HTMLResponse(
            f"<pre style='color:red;white-space:pre-wrap;font-size:12px'>[DEBUG] {tb}</pre>",
            status_code=500,
        )
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    palette = [
        {
            "r": int(c[0]),
            "g": int(c[1]),
            "b": int(c[2]),
            "hex": f"#{int(c[0]):02x}{int(c[1]):02x}{int(c[2]):02x}",
        }
        for c in colors
    ]

    return templates.TemplateResponse(
        "partials/result.html",
        {
            "request": request,
            "palette": palette,
            "image_filename": image.filename,
            "method": "SALIENCY" if method == "saliency" else method.upper(),
        },
    )
