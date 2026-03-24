from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .qa_service import QAService
from .schemas import SearchRequest


BASE_DIR = Path(__file__).resolve().parents[1]
FILE_SYSTEM_DIR = BASE_DIR / "file_system"
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(title="Local File QA POC")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

qa_service = QAService(FILE_SYSTEM_DIR)


@app.get("/api/scan")
def scan_computer() -> dict:
    try:
        return qa_service.scan()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Scan failed: {exc}") from exc


@app.post("/api/search")
def search(request: SearchRequest) -> dict:
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        return qa_service.answer(query)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Search failed: {exc}") from exc


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
