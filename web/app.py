"""Aplikasi demo web (FastAPI + htmx) untuk sistem tanya jawab akademik FILKOM.

Jalankan dari root repositori:
    uv run uvicorn web.app:app --reload
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Form, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from web.pipeline import LABEL_METODE, SistemQA, muat_evaluasi, muat_set_uji

AKAR_WEB = Path(__file__).resolve().parent
sistem = SistemQA()
templates = Jinja2Templates(directory=str(AKAR_WEB / "templates"))


@asynccontextmanager
async def daur_hidup(app: FastAPI):
    """Muat korpus dan model UDPipe sekali saat server hidup."""
    await asyncio.to_thread(sistem.siapkan)
    yield


app = FastAPI(title="Demo Tanya Jawab Akademik FILKOM", lifespan=daur_hidup)
app.mount("/static", StaticFiles(directory=str(AKAR_WEB / "static")), name="static")


def _konteks_hasil(jejak: dict, request: Request) -> dict:
    return {"request": request, "label_metode": LABEL_METODE, **jejak}


@app.get("/", response_class=HTMLResponse)
async def beranda(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request,
            "halaman": "demo",
            "contoh": muat_set_uji(),
            "status": sistem.status(),
        },
    )


async def _jalankan(request: Request, pertanyaan: str):
    jejak = await asyncio.to_thread(sistem.trace, pertanyaan)
    return templates.TemplateResponse(
        request=request,
        name="_hasil.html",
        context=_konteks_hasil(jejak, request),
    )


@app.post("/tanya", response_class=HTMLResponse)
async def tanya_post(request: Request, pertanyaan: str = Form("")):
    return await _jalankan(request, pertanyaan)


@app.get("/tanya", response_class=HTMLResponse)
async def tanya_get(request: Request, q: str = Query("")):
    return await _jalankan(request, q)


@app.get("/evaluasi", response_class=HTMLResponse)
async def evaluasi(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="evaluasi.html",
        context={
            "request": request,
            "halaman": "evaluasi",
            "label_metode": LABEL_METODE,
            **muat_evaluasi(),
        },
    )


@app.get("/sehat", response_class=JSONResponse)
async def sehat():
    return sistem.status()
