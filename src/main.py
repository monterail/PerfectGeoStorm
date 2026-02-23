"""FastAPI entry point for GeoStorm."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.database import initialize_database

logger = logging.getLogger(__name__)

_STATIC_DIR = Path(__file__).resolve().parent.parent / "web" / "dist" / "client"


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    database: str
    scheduler: str


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Startup and shutdown lifecycle for GeoStorm."""
    await initialize_database()
    logger.info("GeoStorm started on port 8080")
    yield
    logger.info("GeoStorm shutting down")


app = FastAPI(
    title="GeoStorm",
    description="Observability for AI-driven software discovery",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# TODO(routes): include routers from src/routes/ when implemented


@app.get("/health")
async def health_check() -> HealthResponse:
    """Return service health status."""
    return HealthResponse(
        status="ok",
        database="connected",
        scheduler="running",
    )


if _STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")


@app.get("/{_full_path:path}")
async def serve_spa(_full_path: str) -> FileResponse | JSONResponse:
    """Serve the Astro SSR index for client-side routing."""
    index_file = _STATIC_DIR / "index.html"
    if index_file.is_file():
        return FileResponse(str(index_file))
    return JSONResponse(
        content={"detail": "Frontend not built. Run pnpm build in web/."},
        status_code=404,
    )
