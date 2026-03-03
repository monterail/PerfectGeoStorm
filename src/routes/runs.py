"""Run, response, perception, and analytics endpoints for GeoStorm API."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from src.container import run_repo, run_service, term_repo
from src.progress import RunPhase, RunProgressEvent, progress_bus
from src.routes.deps import get_project_or_404
from src.schemas import (  # noqa: TC001
    HeatmapCell,
    HeatmapRow,
    PaginatedResponse,
    PerceptionBreakdownResponse,
    PerceptionResponse,
    ProjectHeatmapResponse,
    ResponseItem,
    RunBreakdownResponse,
    RunDetailResponse,
    RunResponse,
    RunTermBreakdownItem,
    TrajectoryResponse,
)

router = APIRouter(prefix="/api")


# ---------------------------------------------------------------------------
# 1) GET /api/projects/{project_id}/runs
# ---------------------------------------------------------------------------


@router.get("/projects/{project_id}/runs")
async def list_runs(
    project_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    status: str | None = Query(default=None),
) -> PaginatedResponse[RunResponse]:
    """Paginated list of runs for a project."""
    await get_project_or_404(project_id)
    return await run_service.list_runs(project_id, limit, offset, status)


# ---------------------------------------------------------------------------
# 2) GET /api/runs/{run_id}
# ---------------------------------------------------------------------------


@router.get("/runs/{run_id}")
async def get_run(run_id: str) -> RunDetailResponse:
    """Run detail with aggregate perception score and competitors detected."""
    result = await run_service.get_run_detail(run_id)
    if not result:
        raise HTTPException(status_code=404, detail="Run not found")
    return result


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 3) GET /api/runs/{run_id}/progress  (SSE)
# ---------------------------------------------------------------------------


@router.get("/runs/{run_id}/progress")
async def stream_run_progress(run_id: str) -> StreamingResponse:
    """Server-Sent Events stream for real-time run progress."""
    run = await run_service.get_run_status(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    async def event_generator() -> AsyncGenerator[str, None]:
        status = run["status"]
        # If already done, send a single final event and close
        if status in ("completed", "failed", "cancelled"):
            phase = RunPhase.complete if status == "completed" else RunPhase.failed
            event = RunProgressEvent(
                run_id=run_id, phase=phase,
                completed=run["completed_queries"], failed=run["failed_queries"],
                total=run["total_queries"], status=status,
            )
            yield f"data: {json.dumps(event.to_dict())}\n\n"
            return

        # Send an initial snapshot so the client renders immediately
        initial = RunProgressEvent(
            run_id=run_id,
            phase=RunPhase.preparing if status == "pending" else RunPhase.querying,
            completed=run["completed_queries"],
            failed=run["failed_queries"],
            total=run["total_queries"],
            status=status,
        )
        yield f"data: {json.dumps(initial.to_dict())}\n\n"

        queue = progress_bus.subscribe(run_id)
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(event.to_dict())}\n\n"
                    # Close stream when run finishes
                    if event.phase in (RunPhase.complete, RunPhase.failed):
                        return
                except TimeoutError:
                    # Keepalive comment to prevent proxy/browser timeout
                    yield ": keepalive\n\n"
        except asyncio.CancelledError:
            return
        finally:
            progress_bus.unsubscribe(run_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# 4) GET /api/runs/{run_id}/responses
# ---------------------------------------------------------------------------


@router.get("/runs/{run_id}/responses")
async def list_responses(
    run_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> PaginatedResponse[ResponseItem]:
    """Paginated responses with nested mentions for a run."""
    run = await run_repo.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return await run_service.list_responses(run_id, run["project_id"], limit, offset)


# ---------------------------------------------------------------------------
# 5) GET /api/projects/{project_id}/perception
# ---------------------------------------------------------------------------


@router.get("/projects/{project_id}/perception")
async def get_perception(
    project_id: str,
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
) -> PerceptionResponse:
    """Time-series perception data for a project."""
    await get_project_or_404(project_id)
    return await run_service.get_perception(project_id, start_date, end_date)


# ---------------------------------------------------------------------------
# 6) GET /api/projects/{project_id}/trajectory
# ---------------------------------------------------------------------------


@router.get("/projects/{project_id}/trajectory")
async def get_trajectory(
    project_id: str,
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    period: Literal["daily", "weekly", "monthly"] = Query(default="weekly"),
) -> TrajectoryResponse:
    """Historical trajectory data showing week-over-week or day-over-day changes."""
    await get_project_or_404(project_id)
    return await run_service.get_trajectory(project_id, start_date, end_date, period)


# ---------------------------------------------------------------------------
# 7) GET /api/projects/{project_id}/perception/breakdown
# ---------------------------------------------------------------------------


@router.get("/projects/{project_id}/perception/breakdown")
async def get_perception_breakdown(project_id: str) -> PerceptionBreakdownResponse:
    """Per-term and per-provider perception breakdown from the latest scoring period."""
    await get_project_or_404(project_id)
    term_rows = await term_repo.list_active_term_ids_and_names(project_id)
    term_names = {row["id"]: row["name"] for row in term_rows}
    return await run_service.get_perception_breakdown(project_id, term_names)


# ---------------------------------------------------------------------------
# 8) GET /api/runs/{run_id}/breakdown
# ---------------------------------------------------------------------------


@router.get("/runs/{run_id}/breakdown")
async def get_run_breakdown(
    run_id: str,
    provider: str | None = Query(default=None),
) -> RunBreakdownResponse:
    """Per-term brand mention summary for a single run."""
    run = await run_repo.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    rows = await run_repo.get_run_term_breakdown(run_id, provider)
    terms = [
        RunTermBreakdownItem(
            term_id=row["term_id"],
            term_name=row["term_name"],
            total_responses=row["total_responses"],
            brand_mentions=row["brand_mentions"],
            mention_pct=(
                row["brand_mentions"] / row["total_responses"]
                if row["total_responses"] > 0 else 0.0
            ),
        )
        for row in rows
    ]
    return RunBreakdownResponse(run_id=run_id, provider=provider, terms=terms)


# ---------------------------------------------------------------------------
# 9) GET /api/projects/{project_id}/heatmap
# ---------------------------------------------------------------------------


@router.get("/projects/{project_id}/heatmap")
async def get_project_heatmap(
    project_id: str,
    provider: str | None = Query(default=None),
) -> ProjectHeatmapResponse:
    """Project heatmap: rows=runs, columns=terms, cells=brand mention %."""
    await get_project_or_404(project_id)
    rows = await run_repo.get_project_heatmap(project_id, provider)
    available_providers = await run_repo.get_project_providers(project_id)

    # Build ordered term list and per-run data
    term_order: list[str] = []
    term_id_map: dict[str, str] = {}  # term_id → term_name
    run_data: dict[str, dict[str, object]] = {}  # run_id → {run_date, cells}

    for row in rows:
        tid = row["term_id"]
        if tid not in term_id_map:
            term_id_map[tid] = row["term_name"]
            term_order.append(tid)
        rid = row["run_id"]
        if rid not in run_data:
            run_data[rid] = {"run_date": row["run_date"], "cells": {}}
        total = row["total_responses"]
        pct = row["brand_mentions"] / total if total > 0 else 0.0
        run_data[rid]["cells"][tid] = pct  # type: ignore[index]

    # Build ordered column names
    term_names = [term_id_map[tid] for tid in term_order]

    # Build HeatmapRow objects — one per run, cells aligned to term_order
    heatmap_rows = []
    for rid, rdata in run_data.items():
        cells: list[HeatmapCell] = []
        for tid in term_order:
            pct_val = rdata["cells"].get(tid)  # type: ignore[union-attr]
            cells.append(
                HeatmapCell(
                    term_id=tid,
                    term_name=term_id_map[tid],
                    mention_pct=float(pct_val) if pct_val is not None else None,
                )
            )
        heatmap_rows.append(
            HeatmapRow(
                run_id=rid,
                run_date=datetime.fromisoformat(str(rdata["run_date"])),
                cells=cells,
            )
        )

    return ProjectHeatmapResponse(
        project_id=project_id,
        provider=provider,
        terms=term_names,
        rows=heatmap_rows,
        available_providers=available_providers,
    )
