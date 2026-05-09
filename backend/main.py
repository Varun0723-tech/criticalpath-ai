from __future__ import annotations

import logging
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Support both:
# 1. `uvicorn backend.main:app --reload` from the project root
# 2. `uvicorn main:app --reload` from inside the backend directory
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.routes.triage import router as triage_router
from backend.services.config import get_settings
from backend.services.llm_service import get_llm_service

settings = get_settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Multi-agent emergency triage workflow with FHIR-style reporting.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.frontend_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(triage_router)


@app.get("/health")
async def healthcheck() -> dict[str, object]:
    llm_service = get_llm_service()
    return {
        "status": "ok",
        "service": settings.app_name,
        "llm_enabled": settings.enable_llm,
        "llm_available": llm_service.available,
        "llm_status_message": None if llm_service.available else llm_service.unavailable_reason,
        "openai_key_configured": bool(settings.openai_api_key),
        "model": settings.openai_model,
    }


frontend_dist = project_root / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
